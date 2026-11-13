"""
Testes automatizados do modo Perseguição + verificações dos modos originais.
Uso (na pasta do projeto):  python testes/testes_perseguicao.py
Roda sem janela (SDL dummy) e salva capturas de tela em testes/capturas/.
"""
import os
import random
import sys
import traceback

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
PASTA_TESTES = os.path.dirname(os.path.abspath(__file__))
PASTA_PROJETO = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(PASTA_TESTES)
CAPTURAS = os.path.join(PASTA_TESTES, "capturas")
os.makedirs(CAPTURAS, exist_ok=True)
sys.path.insert(0, PASTA_PROJETO)
sys.path.insert(0, PASTA_TESTES)

import pygame  # noqa: E402
import bot  # noqa: E402
import main  # noqa: E402
from constantes import *  # noqa: E402,F401,F403
from guardiao import fator_velocidade_guardiao  # noqa: E402
from loja import CATALOGO, comprar, Inventario  # noqa: E402
from mapa_perseguicao import gerar_mapa_perseguicao, mapa_perseguicao_valido  # noqa: E402
from niveis import NIVEIS  # noqa: E402

DT = 1 / 60
RESULTADOS = []
JOGO = main.Jogo()


def teste(nome):
    def decorar(funcao):
        def executar():
            random.seed(7)
            try:
                detalhe = funcao()
                RESULTADOS.append((nome, True, detalhe or ""))
            except Exception as erro:  # noqa: BLE001
                RESULTADOS.append((nome, False, f"{erro!r}\n{traceback.format_exc()}"))
        executar.nome = nome
        return executar
    return decorar


def nova_partida(semente=1234):
    """Entra no modo pelo menu, com mapa de semente fixa."""
    import perseguicao
    original = perseguicao.gerar_mapa_perseguicao
    perseguicao.gerar_mapa_perseguicao = lambda s=None: original(semente)
    JOGO.ir_para_menu()
    JOGO.executar_acao("iniciar")
    JOGO.executar_acao(ACAO_PERSEGUICAO)
    perseguicao.gerar_mapa_perseguicao = original
    p = JOGO.perseguicao
    p.jogador.ler_teclado = lambda: (0, 0)
    return p


def passo(n=1, dt=DT):
    for _ in range(n):
        JOGO.atualizar(dt, dt)


def colocar_jogador(p, tile):
    p.jogador.posicionar((tile[0] * 40, 80 + tile[1] * 40))
    p.tile_jogador = tile


def acordar(p):
    p.guardiao.dormindo = 0.0


def distancia_bfs(p, a, b):
    caminho = p.labirinto.caminho_bfs(a, b, LIMITE_BFS_TOTAL)
    return None if caminho is None else len(caminho)


def tiles_livres(p):
    lab = p.labirinto
    return [(c, l) for l in range(LINHAS) for c in range(COLUNAS) if lab.tile_livre(c, l)]


# ======================================================================
@teste("01 Menu apresenta os três modos (+ Voltar)")
def t01():
    acoes = [b.acao for b in JOGO.menu_modos.botoes]
    textos = [b.texto for b in JOGO.menu_modos.botoes]
    assert acoes == ["campanha", "infinito", ACAO_PERSEGUICAO, "voltar"], acoes
    for b in JOGO.menu_modos.botoes:                       # nada fora da tela
        assert b.retangulo.bottom < ALTURA_JANELA - 40
    # clique do mouse no 3º botão inicia o modo
    JOGO.ir_para_menu()
    JOGO.executar_acao("iniciar")
    JOGO.tratar_eventos = JOGO.tratar_eventos
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                         pos=JOGO.menu_modos.botoes[2].retangulo.center))
    JOGO.tratar_eventos()
    assert JOGO.perseguicao is not None and JOGO.estado == ESTADO_JOGANDO
    return ", ".join(textos)


@teste("02 Campanha continua funcionando (bot conclui a fase 1)")
def t02():
    JOGO.ir_para_menu()
    JOGO.executar_acao("campanha")
    assert JOGO.perseguicao is None and JOGO.modo_infinito is False
    assert JOGO.nivel is NIVEIS[0]
    JOGO.jogador.ler_teclado = lambda: bot.direcao_para(
        JOGO.labirinto, JOGO.jogador, *bot.objetivo(JOGO.labirinto, JOGO.itens))
    for _ in range(60 * 60):
        passo()
        if JOGO.numero_fase == 2:
            break
    assert JOGO.numero_fase == 2, "não chegou à fase 2"
    return f"pontos={JOGO.pontos}"


@teste("03 Modo infinito continua gerando mapas")
def t03():
    JOGO.ir_para_menu()
    JOGO.executar_acao("infinito")
    assert JOGO.perseguicao is None and JOGO.modo_infinito is True
    mapas = {tuple(JOGO.nivel["mapa"])}
    for fase in (2, 3, 4, 5):
        JOGO.carregar_fase(fase)
        mapas.add(tuple(JOGO.nivel["mapa"]))
        passo(30)
    assert len(mapas) == 5
    assert any(i.__class__.__name__ == "Dragao" for i in JOGO.inimigos)   # fase 5 = chefe
    return "5 mapas distintos; fase 5 com dragão"


@teste("04 Modo Perseguição inicia corretamente")
def t04():
    p = nova_partida()
    assert JOGO.estado == ESTADO_JOGANDO and JOGO.modo_infinito in (True, False)
    assert p.jogador.vidas == 3 and p.pontos == 0 and p.ouro == 0
    assert p.guardiao.tile == p.labirinto.guardiao_inicial and p.guardiao.dormindo > 0
    d = distancia_bfs(p, p.tile_jogador, p.guardiao.tile)
    assert d >= DIST_MIN_GUARDIAO_INICIO, d
    assert p.labirinto.santuarios and p.labirinto.esconderijos and p.labirinto.passagens
    assert any(i.tipo == "chave" for i in p.itens)
    passo(60)
    JOGO.desenhar()
    return f"Guardião a {d} tiles do jogador"


@teste("05 Jogador não atravessa paredes (inclusive com poção e quadros lentos)")
def t05():
    p = nova_partida(99)
    acordar(p)
    p.guardiao.velocidade_base = 0                  # o foco aqui é o jogador
    rng = random.Random(3)
    entrada = {"d": (1, 0)}
    p.jogador.ler_teclado = lambda: entrada["d"]
    violacoes = 0
    for i in range(6000):
        if i % 20 == 0:
            entrada["d"] = (rng.choice((-1, 0, 1)), rng.choice((-1, 0, 1)))
        if i == 2000:
            p.inventario.quantidades["velocidade"] = 1
            p.usar_item("velocidade")
        p.jogador.invulneravel_restante = 5
        passo(1, 0.05 if i % 7 == 0 else DT)
        if JOGO.estado != ESTADO_JOGANDO:
            break
        if p.jogador.retangulo.collidelist(p.labirinto.paredes) != -1:
            violacoes += 1
    assert violacoes == 0, violacoes
    return "6000 quadros, 0 sobreposições com paredes"


@teste("06/08 Guardião não atravessa paredes nem fica preso")
def t06():
    p = nova_partida(5)
    acordar(p)
    rng = random.Random(4)
    entrada = {"d": (0, 1)}
    p.jogador.ler_teclado = lambda: entrada["d"]
    parado, maior_parado, ultimo = 0.0, 0.0, None
    visitados = set()
    for i in range(60 * 150):                       # 150 s (passa pela fúria)
        if i % 25 == 0:
            entrada["d"] = (rng.choice((-1, 0, 1)), rng.choice((-1, 0, 1)))
        p.jogador.invulneravel_restante = 5         # não queremos game over aqui
        passo()
        g = p.guardiao
        assert g.retangulo.collidelist(p.labirinto.paredes) == -1, "Guardião na parede"
        assert p.labirinto.tile_livre(*g.tile) and p.labirinto.tile_livre(*g.destino)
        assert g.tile not in p.labirinto.passagens and g.destino not in p.labirinto.passagens
        visitados.add(g.tile)
        if g.ativo:
            posicao = (round(g.x), round(g.y))
            parado = parado + DT if posicao == ultimo else 0.0
            maior_parado = max(maior_parado, parado)
            ultimo = posicao
        else:
            parado = 0.0
    assert maior_parado < 1.0, f"parado por {maior_parado:.2f}s"
    assert len(visitados) > 40, len(visitados)
    return f"{len(visitados)} tiles visitados; maior tempo parado {maior_parado:.2f}s"


@teste("07 Guardião persegue o jogador (BFS)")
def t07():
    p = nova_partida(11)
    acordar(p)
    livres = tiles_livres(p)
    # coloca o jogador a 7 tiles de caminho do Guardião (dentro do raio de detecção)
    alvo = next(t for t in livres if distancia_bfs(p, p.guardiao.tile, t) == 7
                and not p.labirinto.eh_perigoso(*t) and t not in p.recargas)
    colocar_jogador(p, alvo)
    distancias = []
    for _ in range(60 * 6):
        passo()
        distancias.append(distancia_bfs(p, p.guardiao.tile, p.tile_jogador))
        if p.capturas:
            break
    assert p.capturas == 1 or min(distancias) <= 1, distancias[-10:]
    estagio = p.guardiao.estagio
    return f"capturou em {len(distancias) * DT:.1f}s (estágio durante a caçada: {estagio})"


@teste("09 Velocidade do Guardião aumenta com o tempo")
def t09():
    tabela = {0: 1.0, 29.9: 1.0, 30: 1.2, 59: 1.2, 60: 1.4, 89: 1.4, 90: 1.6, 300: 1.6}
    for tempo, esperado in tabela.items():
        assert abs(fator_velocidade_guardiao(tempo) - esperado) < 1e-9, (tempo, esperado)
    p = nova_partida(12)
    acordar(p)
    p.jogador.invulneravel_restante = 999
    medidas = {}
    for alvo_tempo in (10, 40, 70, 95):
        p.tempo_partida = alvo_tempo
        passo(2)
        medidas[alvo_tempo] = p.guardiao.velocidade
    assert medidas[10] == VELOCIDADE_GUARDIAO
    assert abs(medidas[40] - VELOCIDADE_GUARDIAO * 1.2) < 1e-6
    assert abs(medidas[70] - VELOCIDADE_GUARDIAO * 1.4) < 1e-6
    assert abs(medidas[95] - VELOCIDADE_GUARDIAO * 1.6) < 1e-6
    assert p.guardiao.estagio == ESTAGIO_FURIA
    return ", ".join(f"{t}s→{v:.0f}px/s" for t, v in medidas.items())


def forcar_contato(p):
    """Coloca o Guardião exatamente sobre o jogador."""
    g = p.guardiao
    g.teleportar(*p.tile_jogador)
    g.dormindo = 0.0


@teste("10 Captura desconta exatamente uma vida e reposiciona com segurança")
def t10():
    p = nova_partida(21)
    passo(5)
    forcar_contato(p)
    passo(1)
    assert p.jogador.vidas == 2 and p.capturas == 1 and p.animacao_captura > 0
    passo(int(TEMPO_ANIMACAO_CAPTURA * 60) + 5)
    assert p.animacao_captura == 0 and JOGO.estado == ESTADO_JOGANDO
    tile_j, tile_g = p.tile_jogador, p.guardiao.tile
    d = distancia_bfs(p, tile_j, tile_g)
    assert d >= DIST_MIN_GUARDIAO_RESPAWN, d
    assert p.labirinto.tile_livre(*tile_j) and not p.labirinto.eh_perigoso(*tile_j)
    assert p.jogador.retangulo.collidelist(p.labirinto.paredes) == -1
    assert p.guardiao.dormindo > 0 and p.jogador.invulneravel
    # vários reposicionamentos seguidos: sempre seguros
    for _ in range(25):
        p.jogador.vidas = 3
        forcar_contato(p)
        p.jogador.invulneravel_restante = 0
        passo(1)
        passo(int(TEMPO_ANIMACAO_CAPTURA * 60) + 3)
        tj = p.tile_jogador
        assert p.labirinto.tile_livre(*tj) and not p.labirinto.eh_perigoso(*tj)
        assert distancia_bfs(p, tj, p.guardiao.tile) >= min(DIST_MIN_RESPAWN,
                                                            DIST_MIN_GUARDIAO_RESPAWN)
    return f"após captura: jogador a {d} tiles do Guardião"


@teste("11 Escudo impede uma captura (e não é permanente)")
def t11():
    p = nova_partida(22)
    p.inventario.quantidades["escudo"] = 1
    forcar_contato(p)
    passo(1)
    assert p.jogador.vidas == 3 and p.inventario.quantidade("escudo") == 0
    assert p.bloqueios_escudo == 1 and p.guardiao.atordoado > 0 and p.capturas == 0
    d = distancia_bfs(p, p.tile_jogador, p.guardiao.tile)
    assert 3 <= d <= 5, d                              # Guardião foi repelido
    passo(int((TEMPO_INVULNERAVEL + 0.2) * 60))
    assert not p.jogador.invulneravel
    forcar_contato(p)
    passo(1)
    assert p.jogador.vidas == 2 and p.capturas == 1
    return "1º contato bloqueado; 2º contato capturou"


@teste("12 Sem perda repetida de vidas durante a invulnerabilidade")
def t12():
    p = nova_partida(23)
    forcar_contato(p)
    passo(1)
    passo(int(TEMPO_ANIMACAO_CAPTURA * 60) + 2)
    vidas = p.jogador.vidas
    assert p.jogador.invulneravel
    for _ in range(int(TEMPO_INVULNERAVEL * 60) - 5):     # Guardião colado no jogador
        g = p.guardiao
        g.teleportar(*p.tile_jogador)
        g.dormindo = 0.0
        passo(1)
    assert p.jogador.vidas == vidas and p.capturas == 1
    return f"vidas estáveis em {vidas} durante {TEMPO_INVULNERAVEL}s de contato"


@teste("13 Chave abre a saída (sem chave não há fuga)")
def t13():
    p = nova_partida(31)
    p.guardiao.dormindo = 9999
    frente = bot.frente_da_porta(p.labirinto)
    colocar_jogador(p, frente)
    p.jogador.ler_teclado = lambda: bot.direcao_para(p.labirinto, p.jogador, frente,
                                                     p.labirinto.porta.center)
    passo(90)
    assert JOGO.estado == ESTADO_JOGANDO and not p.labirinto.porta_aberta
    assert "trancada" in p.mensagem
    chave = next(i for i in p.itens if i.tipo == "chave")
    colocar_jogador(p, bot.tile_de(chave.retangulo.center))
    p.jogador.ler_teclado = lambda: (0, 0)
    passo(2)
    assert p.tem_chave and p.labirinto.porta_aberta
    colocar_jogador(p, frente)
    p.jogador.ler_teclado = lambda: bot.direcao_para(p.labirinto, p.jogador, frente,
                                                     p.labirinto.porta.center)
    passo(120)
    assert JOGO.estado == ESTADO_VITORIA
    return "porta trancada sem chave; vitória após pegar a chave"


@teste("14/15 Loja: abre só no santuário, compra desconta ouro, bloqueia inválidas")
def t14():
    p = nova_partida(41)
    p.guardiao.dormindo = 9999
    JOGO.tratar_tecla(pygame.K_e)                    # longe do santuário
    assert not p.loja.aberta
    colocar_jogador(p, p.labirinto.santuarios[0])
    passo(1)
    JOGO.tratar_tecla(pygame.K_e)
    assert p.loja.aberta
    p.ouro = 0
    JOGO.tratar_tecla(pygame.K_RETURN)               # Poção de Cura sem saldo
    assert p.ouro == 0 and p.inventario.quantidade("cura") == 0
    assert "insuficiente" in p.loja.aviso
    p.ouro = 400
    JOGO.tratar_tecla(pygame.K_RETURN)               # compra cura (50)
    assert p.ouro == 350 and p.inventario.quantidade("cura") == 1
    JOGO.tratar_tecla(pygame.K_DOWN)
    JOGO.tratar_tecla(pygame.K_DOWN)                 # escudo (80)
    JOGO.tratar_tecla(pygame.K_RETURN)
    assert p.ouro == 270 and p.inventario.quantidade("escudo") == 1
    # clique do mouse na bússola
    p.clicar(p.loja.linhas[4].center)
    assert p.ouro == 210 and p.inventario.quantidade("bussola") == 1
    # limite por item
    p.ouro = 10000
    for _ in range(10):
        p.loja.selecionado = 1
        p.comprar_selecionado()
    assert p.inventario.quantidade("velocidade") == MAX_POR_ITEM
    assert p.ouro == 10000 - MAX_POR_ITEM * PRECO_POCAO_VELOCIDADE
    # regra pura de compra
    inv = Inventario()
    assert comprar("invisibilidade", 99, inv) == (99, False, "Ouro insuficiente! Faltam 1.")
    assert comprar("invisibilidade", 100, inv)[:2] == (0, True)
    JOGO.desenhar()
    pygame.image.save(JOGO.tela, os.path.join(CAPTURAS, "04_loja.png"))
    JOGO.tratar_tecla(pygame.K_ESCAPE)               # ESC fecha a loja (não pausa)
    assert not p.loja.aberta and JOGO.estado == ESTADO_JOGANDO
    return "saldo e inventário corretos; limite de 5 por item"


@teste("16/18 Itens funcionam e efeitos temporários expiram (tempo real)")
def t16():
    p = nova_partida(51)
    p.guardiao.dormindo = 9999
    inv = p.inventario
    for item in CATALOGO:
        inv.quantidades[item["id"]] = 1
    # cura com vidas cheias não é consumida; com 2 vidas recupera 1
    assert not p.usar_item("cura") and inv.quantidade("cura") == 1
    p.jogador.vidas = 2
    assert p.usar_item("cura") and p.jogador.vidas == 3 and inv.quantidade("cura") == 0
    assert not p.usar_item("cura")                       # acabou
    # velocidade: desloca 1.5x mais no mesmo tempo
    assert p.usar_item("velocidade") and p.fator_velocidade_jogador() == FATOR_POCAO_VELOCIDADE
    assert not p.usar_item("velocidade")                 # não há outra no inventário
    # invisibilidade e bússola
    assert p.usar_item("invisibilidade") and not p.detectavel
    assert p.usar_item("bussola")
    passo(2)
    assert p.angulo_bussola is not None and p.trilha_bussola
    # escudo é passivo: tecla 3 não gasta
    assert not p.usar_item("escudo") and inv.quantidade("escudo") == 1
    # expiração com quadros irregulares (dt variável)
    tempo = 0.0
    while tempo < DURACAO_VELOCIDADE + 0.3:
        dt = random.choice((1 / 30, 1 / 60, 1 / 144))
        JOGO.atualizar(dt, dt)
        tempo += dt
        if tempo < DURACAO_INVISIBILIDADE - 0.1:
            assert p.efeito_invisivel > 0
    assert p.efeito_velocidade == 0 and p.efeito_invisivel == 0 and p.efeito_bussola == 0
    assert p.fator_velocidade_jogador() == 1.0 and p.detectavel and p.angulo_bussola is None
    return "cura/velocidade/escudo/invisibilidade/bússola ok; expiram por dt"


@teste("16b Invisibilidade faz o Guardião perder o rastro")
def t16b():
    p = nova_partida(52)
    acordar(p)
    alvo = next(t for t in tiles_livres(p) if distancia_bfs(p, p.guardiao.tile, t) == 6
                and not p.labirinto.eh_perigoso(*t) and t not in p.recargas)
    colocar_jogador(p, alvo)
    passo(30)
    assert p.guardiao.estagio == ESTAGIO_CACADA and p.guardiao.ciente
    p.inventario.quantidades["invisibilidade"] = 1
    p.usar_item("invisibilidade")
    p.jogador.invulneravel_restante = 99
    passo(30)
    assert not p.guardiao.ciente and p.guardiao.estagio == ESTAGIO_VIGILANCIA
    return "CAÇADA → VIGILÂNCIA ao ficar invisível"


@teste("17 Guardião continua ativo com a loja aberta")
def t17():
    p = nova_partida(61)
    acordar(p)
    colocar_jogador(p, p.labirinto.santuarios[0])
    passo(1)
    p.alternar_loja()
    assert p.loja.aberta
    antes = (p.guardiao.x, p.guardiao.y)
    tempo_antes = p.tempo_partida
    jogador_antes = p.jogador.retangulo.topleft
    p.jogador.ler_teclado = lambda: (1, 0)           # setas navegam a loja, não andam
    passo(60)
    assert (p.guardiao.x, p.guardiao.y) != antes
    assert p.tempo_partida > tempo_antes + 0.9
    assert p.jogador.retangulo.topleft == jogador_antes
    return "Guardião andou e o cronômetro correu com a loja aberta"


@teste("19 Vitória completa (bot pega a chave e foge, com bônus)")
def t19():
    p = nova_partida(71)
    recorde_antes = JOGO.recorde_perseguicao
    p.jogador.ler_teclado = lambda: bot.direcao_para(
        p.labirinto, p.jogador, *bot.objetivo(p.labirinto, p.itens))
    for _ in range(60 * 120):
        p.jogador.invulneravel_restante = 1.0        # o bot não sabe fugir; só testa o fluxo
        passo()
        if JOGO.estado == ESTADO_VITORIA:
            break
    assert JOGO.estado == ESTADO_VITORIA, JOGO.estado
    assert ("Fuga da masmorra", PONTOS_FUGA) in p.bonus
    assert ("Fuga sem captura", BONUS_SEM_CAPTURA) in p.bonus and p.capturas == 0
    assert JOGO.recorde_perseguicao == max(recorde_antes, p.pontos)
    passo(60)
    assert JOGO.menu_atual() is JOGO.menu_fim
    JOGO.desenhar()
    pygame.image.save(JOGO.tela, os.path.join(CAPTURAS, "06_vitoria.png"))
    return f"pontos={p.pontos} em {p.tempo_partida:.1f}s"


@teste("20 Game Over após perder as três vidas")
def t20():
    p = nova_partida(81)
    for _ in range(3):
        p.jogador.invulneravel_restante = 0
        forcar_contato(p)
        passo(1)
        passo(int(TEMPO_ANIMACAO_CAPTURA * 60) + 3)
    assert JOGO.estado == ESTADO_GAME_OVER and p.jogador.vidas == 0 and p.capturas == 3
    passo(60)
    assert JOGO.menu_atual() is JOGO.menu_fim
    JOGO.desenhar()
    pygame.image.save(JOGO.tela, os.path.join(CAPTURAS, "07_game_over.png"))
    return "GAME_OVER com menu de fim"


@teste("21 Reiniciar limpa os dados da partida anterior")
def t21():
    p = nova_partida(82)
    p.ouro, p.pontos, p.capturas = 500, 300, 2
    p.inventario.quantidades["escudo"] = 3
    p.efeito_velocidade = 5
    p.jogador.vidas = 1
    p.tempo_partida = 70
    p.guardiao.estagio = ESTAGIO_FURIA
    JOGO.estado = ESTADO_GAME_OVER
    JOGO.tempo_fim = 2
    JOGO.tratar_tecla(pygame.K_r)
    q = JOGO.perseguicao
    assert q is not p and JOGO.estado == ESTADO_JOGANDO
    assert (q.ouro, q.pontos, q.capturas, q.jogador.vidas) == (0, 0, 0, 3)
    assert all(v == 0 for v in q.inventario.quantidades.values())
    assert q.efeito_velocidade == 0 and q.tempo_partida == 0
    assert q.guardiao.estagio == ESTAGIO_VIGILANCIA and q.jogador.fator_velocidade == 1.0
    return "partida nova com valores iniciais"


@teste("22 Voltar ao menu não deixa variáveis do modo ativas")
def t22():
    p = nova_partida(83)
    p.ouro = 999
    JOGO.tratar_tecla(pygame.K_ESCAPE)                # pausa
    assert JOGO.estado == ESTADO_PAUSADO
    passo(30)                                         # pausado: nada anda
    assert p.tempo_partida == 0 or p.tempo_partida < 0.01
    JOGO.executar_acao("menu")
    assert JOGO.perseguicao is None and JOGO.estado == ESTADO_MENU
    JOGO.executar_acao("iniciar")
    JOGO.executar_acao("campanha")
    assert JOGO.perseguicao is None and JOGO.pontos == 0 and JOGO.jogador.vidas == VIDAS_INICIAIS
    assert JOGO.jogador.fator_velocidade == 1.0 and JOGO.nivel is NIVEIS[0]
    passo(120)
    JOGO.desenhar()
    assert JOGO.desenhar_hud is not None
    JOGO.executar_acao("menu")
    return "perseguicao=None; campanha começa limpa"


@teste("23 Recordes e dados separados entre os modos")
def t23():
    JOGO.recorde_fase = 4
    p = nova_partida(84)
    p.pontos = 777
    p._finalizar(ESTADO_GAME_OVER)
    assert JOGO.recorde_perseguicao >= 777 and JOGO.recorde_fase == 4
    JOGO.executar_acao("menu")
    JOGO.executar_acao("infinito")
    assert JOGO.pontos == 0 and JOGO.recorde_fase == 4 and JOGO.perseguicao is None
    JOGO.executar_acao("menu")
    return "recorde_fase intacto; recorde_perseguicao próprio"


@teste("Extra: 500 mapas gerados são válidos e completáveis")
def t_mapas():
    for semente in range(500):
        mapa = gerar_mapa_perseguicao(semente)["mapa"]
        assert mapa_perseguicao_valido(mapa), semente
        texto = "".join(mapa)
        assert texto.count("G") == 1 and texto.count("K") == 1 and texto.count("S") == 1
        assert texto.count("$") >= 1 and all(len(linha) == COLUNAS for linha in mapa)
    return "500/500 válidos"


@teste("Extra: passagem secreta - jogador atravessa, Guardião não")
def t_passagem():
    p = nova_partida(91)
    p.guardiao.dormindo = 9999
    coluna, linha = p.labirinto.passagens[0]
    assert not p.labirinto.tile_livre(coluna, linha)
    vizinhos = [(coluna + d[0], linha + d[1]) for d in ((1, 0), (-1, 0), (0, 1), (0, -1))
                if p.labirinto.tile_livre(coluna + d[0], linha + d[1])]
    a, b = vizinhos[0], vizinhos[1]
    colocar_jogador(p, a)
    direcao = (b[0] - a[0], b[1] - a[1])
    p.jogador.ler_teclado = lambda: direcao
    atravessou = False
    for _ in range(60):
        passo(1)
        if bot.tile_de(p.jogador.retangulo.center) == b:
            atravessou = True
            break
    assert atravessou, "jogador não atravessou"
    caminho = p.labirinto.caminho_bfs(a, b, 400)
    assert caminho and (coluna, linha) not in caminho and len(caminho) >= ATALHO_MIN_PASSAGEM
    return f"atalho de 2 passos contra {len(caminho)} pelo labirinto"


@teste("Extra: esconderijo despista e tem duração limitada")
def t_esconderijo():
    p = nova_partida(92)
    acordar(p)
    esconderijo = p.labirinto.esconderijos[0]
    colocar_jogador(p, esconderijo)
    passo(2)
    assert p.escondido > 0 and not p.detectavel
    forcar_contato(p)
    passo(1)
    assert p.capturas == 0                                 # escondido não é capturado
    p.guardiao.teleportar(*p.labirinto.guardiao_inicial)
    p.guardiao.dormindo = 9999
    passo(int((DURACAO_ESCONDERIJO + 0.2) * 60))
    assert p.escondido == 0 and p.recargas[esconderijo] > 0 and p.detectavel
    return f"escondido por {DURACAO_ESCONDERIJO}s, depois recarga de {RECARGA_ESCONDERIJO}s"


@teste("Extra: espinhos deixam o jogador lento e atrasam o Guardião")
def t_armadilha():
    p = nova_partida(93)
    armadilha = p.armadilhas[0]
    armadilha.relogio = TEMPO_ARMADILHA_RECOLHIDA + 0.2     # ativa
    p.guardiao.dormindo = 9999
    colocar_jogador(p, bot.tile_de(armadilha.retangulo.center))
    passo(1)
    assert p.lentidao > 0 and p.jogador.vidas == 3
    assert p.fator_velocidade_jogador() == FATOR_LENTIDAO
    p.guardiao.teleportar(*bot.tile_de(armadilha.retangulo.center))
    p.guardiao.dormindo = 0
    p.jogador.invulneravel_restante = 99
    armadilha.relogio = TEMPO_ARMADILHA_RECOLHIDA + 0.2
    passo(1)
    assert p.guardiao.atordoado > 0
    return "lentidão no jogador; Guardião atordoado"


@teste("Extra: BFS em intervalos controlados (não a cada quadro)")
def t_bfs():
    p = nova_partida(94)
    acordar(p)
    contador = {"n": 0}
    original = p.labirinto.caminho_bfs

    def contar(*args):
        contador["n"] += 1
        return original(*args)
    p.labirinto.caminho_bfs = contar
    p.jogador.invulneravel_restante = 999
    passo(600)                                   # 10 s
    p.labirinto.caminho_bfs = original
    por_segundo = contador["n"] / 10
    assert por_segundo < 20, por_segundo         # 60 quadros/s -> bem menos de 1 por quadro
    return f"{por_segundo:.1f} buscas/s (percepção+proximidade+passos) para 60 quadros/s"


@teste("Extra: telas desenham sem erro (capturas de tela)")
def t_telas():
    p = nova_partida(95)
    acordar(p)
    p.inventario.quantidades.update({"cura": 2, "escudo": 1, "bussola": 1})
    p.ouro = 230
    p.usar_item("bussola")
    alvo = next(t for t in tiles_livres(p) if distancia_bfs(p, p.guardiao.tile, t) == 5
                and not p.labirinto.eh_perigoso(*t) and t not in p.recargas)
    colocar_jogador(p, alvo)
    p.jogador.invulneravel_restante = 99
    passo(60 * 4)
    JOGO.desenhar()
    pygame.image.save(JOGO.tela, os.path.join(CAPTURAS, "03_cacada.png"))
    forcar_contato(p)
    p.jogador.invulneravel_restante = 0
    passo(1)
    passo(30)
    JOGO.desenhar()
    pygame.image.save(JOGO.tela, os.path.join(CAPTURAS, "05_captura.png"))
    JOGO.tratar_tecla(pygame.K_p)
    JOGO.desenhar()
    pygame.image.save(JOGO.tela, os.path.join(CAPTURAS, "08_pausa.png"))
    JOGO.executar_acao("menu")
    JOGO.estado = ESTADO_INSTRUCOES
    JOGO.desenhar()
    pygame.image.save(JOGO.tela, os.path.join(CAPTURAS, "09_instrucoes.png"))
    JOGO.ir_para_menu()
    return "capturas salvas"


if __name__ == "__main__":
    for nome, valor in list(globals().items()):
        if callable(valor) and hasattr(valor, "nome"):
            valor()
    falhas = 0
    for nome, ok, detalhe in RESULTADOS:
        print(f"[{'OK ' if ok else 'FALHOU'}] {nome}" + (f"  ->  {detalhe}" if detalhe else ""))
        falhas += not ok
    print(f"\n{len(RESULTADOS) - falhas}/{len(RESULTADOS)} testes passaram")
    sys.exit(1 if falhas else 0)
