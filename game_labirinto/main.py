"""
Labirinto: A Fuga - ETAPA 8 (terceiro modo)
Cobre as etapas 1 a 9 do roteiro: menu inicial, instruções, escolha de modo,
pausa e telas de Game Over / vitória, além de animações e fases aleatórias.
Três modos: Campanha, Infinito e Perseguição (o Guardião das Trevas).

Como jogar:  python main.py   (o modo é escolhido no menu)

Organização:
  constantes.py -> valores configuráveis
  niveis.py     -> mapas e lista de fases da campanha
  gerador.py    -> gerador aleatório de fases (modo infinito)
  interface.py  -> botões, menus, fundo animado do menu e tela de instruções
  perseguicao.py, guardiao.py, loja.py, inventario.py, gerador_perseguicao.py,
  desenho_perseguicao.py, constantes_perseguicao.py -> modo Perseguição
  assets.py     -> carregamento opcional das imagens PNG (sprites)
  desenho.py    -> funções que desenham (pixel art com formas do Pygame)
  efeitos.py    -> partículas, textos flutuantes, iluminação e vinheta
  entidades.py  -> Item, Labirinto, Jogador, inimigos e armadilhas
  main.py       -> classe Jogo (laço principal, regras e interface)
"""

import math
import random
import sys

import pygame

from assets import sprites
from constantes import (
    ALTURA_JANELA, CHEFE, COR_ALERTA, COR_FUNDO, COR_OURO,
    COR_SUCESSO, COR_TEXTO, COR_VIDA, ESQUELETO, ESTADO_GAME_OVER,
    DIFICULDADE_PADRAO, DIFICULDADES_INFINITO, ESTADO_DIFICULDADE,
    ESTADO_INSTRUCOES, ESTADO_JOGANDO, ESTADO_MENU, ESTADO_MODOS,
    ESTADO_PAUSADO, ESTADO_VITORIA, FPS, GOBLIN, INTERVALO_CHEFE,
    INTERVALO_POEIRA, INTENSIDADE_TREMOR, LARGURA_JANELA, LUZ_ATIVADA,
    MAX_VIDAS, MODO_INFINITO, TEMPO_ALERTA, TEMPO_FADE,
    TEMPO_FLASH_DANO, TEMPO_MENSAGEM, TEMPO_TITULO_FASE, TEMPO_TREMOR,
    TIPO_CHAVE, TIPO_MOEDA, VELOCIDADE_CHEFE, VELOCIDADE_ESQUELETO,
    VELOCIDADE_GOBLIN, VIDAS_INICIAIS,
)
from desenho import (
    criar_fundo_hud, desenhar_coracao, desenhar_icone_chave,
    desenhar_icone_moeda, desenhar_icone_relogio,
)
from efeitos import Iluminacao, SistemaParticulas, criar_vinheta
from entidades import Dragao, Esqueleto, Goblin, Jogador, Labirinto
from gerador import gerar_nivel
from interface import (
    FundoMenu, MenuVertical, desenhar_instrucoes, desenhar_texto_contorno,
    desenhar_titulo,
)
from niveis import NIVEIS
# --- modo Perseguição (código separado em módulos próprios) ---
from gerador_perseguicao import gerar_nivel_perseguicao
from perseguicao import ModoPerseguicao, RecordesPerseguicao

# Para cada símbolo de inimigo no mapa: (classe, velocidade base)
TIPOS_INIMIGO = {
    ESQUELETO: (Esqueleto, VELOCIDADE_ESQUELETO),
    GOBLIN: (Goblin, VELOCIDADE_GOBLIN),
    CHEFE: (Dragao, VELOCIDADE_CHEFE),
}

# Estados da transição entre fases
TRANSICAO_SAINDO = "saindo"      # a tela escurece
TRANSICAO_ENTRANDO = "entrando"  # a tela clareia na fase nova


class Jogo:
    """Controla o laço principal, as regras (pontos, vidas, tempo) e a interface."""

    def __init__(self, modo_infinito=MODO_INFINITO):
        self.modo_infinito = modo_infinito
        self.dificuldade_infinito = DIFICULDADE_PADRAO   # só vale para o modo infinito
        self.vidas_iniciais = VIDAS_INICIAIS             # vidas do começo da partida atual
        self.modo_perseguicao = False        # terceiro modo (independente do modo_infinito)
        self.perseguicao = None              # dados da partida de Perseguição (None nos outros modos)
        self.recordes_perseguicao = RecordesPerseguicao()
        self.mapas_usados = set()      # assinaturas dos mapas já jogados (nunca repete)
        self.recorde_fase = 0          # fase mais alta alcançada nesta sessão
        pygame.init()
        pygame.display.set_caption("Labirinto: A Fuga")
        self.tela = pygame.display.set_mode((LARGURA_JANELA, ALTURA_JANELA))
        self.cena = pygame.Surface((LARGURA_JANELA, ALTURA_JANELA))   # onde o mundo é desenhado
        self.veu = pygame.Surface((LARGURA_JANELA, ALTURA_JANELA), pygame.SRCALPHA)
        self.relogio = pygame.time.Clock()
        self.carregar_sprites()
        self.fonte_titulo = pygame.font.SysFont("georgia", 26, bold=True)
        self.fonte = pygame.font.SysFont("georgia", 22, bold=True)
        self.fonte_pequena = pygame.font.SysFont("georgia", 18)
        self.fonte_gigante = pygame.font.SysFont("georgia", 64, bold=True)
        self.fonte_botao = pygame.font.SysFont("georgia", 26, bold=True)
        self.fonte_logo = pygame.font.SysFont("georgia", 88, bold=True)
        self.fonte_sublogo = pygame.font.SysFont("georgia", 44, bold=True)
        self.criar_menus()
        self.fundo_hud = criar_fundo_hud()
        self.vinheta = criar_vinheta()
        self.iluminacao = Iluminacao()
        self.particulas = SistemaParticulas()
        self.luz_ativada = LUZ_ATIVADA
        self.rodando = True
        self.fundo_menu = FundoMenu()
        self.tempo_menu = 0.0          # segundos desde que o menu atual apareceu
        self.mouse_pos = None          # última posição do mouse (None = ainda não mexeu)
        self.novo_jogo()
        self.ir_para_menu()

    @staticmethod
    def texto_vidas(quantidade):
        return f"{quantidade} VIDA" if quantidade == 1 else f"{quantidade} VIDAS"

    def vidas_do_modo(self):
        """Vidas iniciais: vêm da dificuldade no modo infinito; nos demais modos, o padrão."""
        if self.modo_infinito and not self.modo_perseguicao:
            return DIFICULDADES_INFINITO[self.dificuldade_infinito]["vidas"]
        return VIDAS_INICIAIS

    def criar_menus(self):
        """Cria os menus de botões de cada tela."""
        meio = LARGURA_JANELA // 2
        self.menu_principal = MenuVertical(
            [("Iniciar", "iniciar"), ("Instruções", "instrucoes"), ("Sair", "sair")],
            meio, 300)
        self.menu_modos = MenuVertical(
            [("Modo Campanha", "campanha"), ("Modo Infinito", "infinito"),
             ("Modo Perseguição", "perseguicao"), ("Voltar", "voltar")],
            meio, 290, largura=400)
        self.menu_dificuldade = MenuVertical(
            [(config["nome"].upper(), chave, self.texto_vidas(config["vidas"]))
             for chave, config in DIFICULDADES_INFINITO.items()]
            + [("VOLTAR", "voltar_modos")],
            meio, 268, largura=400, altura=64)
        self.menu_pausa = MenuVertical(
            [("Continuar", "continuar"), ("Voltar ao menu", "menu")], meio, 320)
        self.menu_fim = MenuVertical(
            [("Jogar novamente", "reiniciar"), ("Voltar ao menu", "menu")], meio, 440)

    def carregar_sprites(self):
        """Usa as imagens de assets/imagens/ quando existirem (senão, desenho padrão)."""
        carregados, ausentes = sprites.carregar()
        if carregados:
            print("Sprites carregados:", ", ".join(carregados))
        if ausentes:
            print("Sem imagem (usando desenho padrão):", ", ".join(ausentes))

    # ---------------- controle de partida e fases ----------------
    def novo_jogo(self):
        """Zera pontos e vidas e começa pela primeira fase."""
        # Cada partida de Perseguição começa com dados novos (nada vaza entre partidas/modos)
        self.perseguicao = (ModoPerseguicao(self.recordes_perseguicao)
                            if self.modo_perseguicao else None)
        self.jogador = Jogador()
        self.vidas_iniciais = self.vidas_do_modo()
        self.jogador.vidas = self.vidas_iniciais     # dificuldade (infinito) ou padrão
        self.pontos = 0
        self.pontos_exibidos = 0.0     # a pontuação na tela "sobe" até o valor real
        self.estado = ESTADO_JOGANDO
        self.tempo_animacao = 0.0
        self.tempo_fim = 0.0           # segundos desde o fim de jogo (anima as telas finais)
        self.tremor = 0.0
        self.flash_dano = 0.0
        self.mapas_usados.clear()
        self.carregar_fase(1)
        self.transicao = TRANSICAO_ENTRANDO   # a aventura começa com um fade-in
        self.tempo_transicao = 0.0

    def obter_nivel(self, numero):
        """
        Dados da fase 'numero' (1, 2, 3...). Na campanha vêm da lista NIVEIS;
        no modo infinito são gerados na hora, sempre diferentes dos anteriores.
        """
        if not self.modo_infinito and not self.modo_perseguicao:
            return NIVEIS[numero - 1]
        for _ in range(20):
            if self.modo_perseguicao:
                nivel = gerar_nivel_perseguicao(numero)
            else:
                nivel = gerar_nivel(numero)
            assinatura = tuple(nivel["mapa"])
            if assinatura not in self.mapas_usados:
                break
        self.mapas_usados.add(assinatura)
        print(f"Fase {numero}: {nivel['nome']} (semente {nivel['semente']})")
        return nivel

    def carregar_fase(self, numero):
        """Cria o labirinto, os itens e os inimigos da fase; reinicia o cronômetro."""
        self.numero_fase = numero
        nivel = self.obter_nivel(numero)
        self.nivel = nivel
        self.labirinto = Labirinto(nivel["mapa"])
        self.itens = list(self.labirinto.itens)
        self.inimigos = self.criar_inimigos(nivel["fator_inimigos"])
        self.armadilhas = self.labirinto.armadilhas
        self.chaves_necessarias = sum(1 for i in self.itens if i.tipo == TIPO_CHAVE)
        self.chaves_coletadas = 0
        self.tempo_limite = nivel["tempo"]
        self.tempo_restante = float(self.tempo_limite)
        self.jogador.posicionar(self.labirinto.posicao_inicial)
        self.mensagem = ""
        self.tempo_mensagem = 0.0
        self.tempo_poeira = 0.0
        self.tempo_titulo = TEMPO_TITULO_FASE     # faixa com o nome da fase
        self.transicao = None
        self.tempo_transicao = 0.0
        self.particulas.limpar()
        if self.perseguicao is not None:
            self.perseguicao.preparar(self)

    def criar_inimigos(self, fator_velocidade):
        """Cria um inimigo para cada 'E', 'X' ou 'B' do mapa."""
        inimigos = []
        for simbolo, coluna, linha in self.labirinto.inimigos_iniciais:
            classe, velocidade = TIPOS_INIMIGO[simbolo]
            inimigos.append(classe(coluna, linha, velocidade * fator_velocidade))
        return inimigos

    def iniciar_saida(self):
        """O jogador atravessou a porta: a tela escurece e, depois, muda de fase."""
        if self.perseguicao is not None:
            self.perseguicao.ao_escapar(self)       # bônus de fuga e recordes
        self.transicao = TRANSICAO_SAINDO
        self.tempo_transicao = 0.0
        x, y = self.labirinto.porta.center
        self.particulas.explosao(x, y, [COR_SUCESSO, (200, 255, 200), COR_OURO], 24, 130, 0.8)
        # No modo infinito, vencer um chefe devolve uma vida (até o limite)
        if self.modo_infinito and self.numero_fase % INTERVALO_CHEFE == 0 \
                and self.jogador.vidas < MAX_VIDAS:
            self.jogador.vidas += 1
            self.particulas.texto(x, y - 20, "+1 VIDA", COR_VIDA)

    def atualizar_transicao(self, dt_real):
        """Controla o fade entre as fases (o jogo fica 'congelado' durante ele)."""
        self.tempo_transicao += dt_real
        if self.tempo_transicao < TEMPO_FADE:
            return
        if self.transicao == TRANSICAO_SAINDO:
            if self.perseguicao is not None or self.modo_infinito \
                    or self.numero_fase < len(NIVEIS):
                self.carregar_fase(self.numero_fase + 1)   # infinitos: sempre há um próximo mapa
                self.transicao = TRANSICAO_ENTRANDO
            else:
                self.estado = ESTADO_VITORIA
                self.tempo_fim = 0.0
                self.transicao = TRANSICAO_ENTRANDO
        else:
            self.transicao = None
        self.tempo_transicao = 0.0

    def mostrar_mensagem(self, texto):
        self.mensagem = texto
        self.tempo_mensagem = TEMPO_MENSAGEM

    # ---------------- regras ----------------
    def coletar_itens(self):
        """Remove os itens tocados pelo jogador e aplica seus efeitos."""
        for item in self.itens[:]:               # cópia: vamos remover durante o laço
            if self.jogador.retangulo.colliderect(item.retangulo):
                self.itens.remove(item)
                self.pontos += item.pontos
                x, y = item.retangulo.center
                if item.tipo == TIPO_CHAVE:
                    self.chaves_coletadas += 1
                    self.particulas.explosao(x, y, [COR_OURO, (255, 245, 170)], 22, 140, 0.8)
                    self.particulas.texto(x, y - 10, "CHAVE!", COR_OURO)
                    if self.chaves_coletadas >= self.chaves_necessarias:
                        self.labirinto.abrir_porta()
                        self.mostrar_mensagem("Chave encontrada! A porta foi destrancada.")
                else:
                    cores = [COR_OURO, (255, 240, 150), (200, 150, 30)]
                    quantidade = 10 if item.tipo == TIPO_MOEDA else 20
                    self.particulas.explosao(x, y, cores, quantidade)
                    self.particulas.texto(x, y - 10, f"+{item.pontos}", COR_OURO)

    def verificar_saida(self):
        """Inicia a saída da fase se o jogador encostar na porta aberta."""
        encostou = self.jogador.retangulo.inflate(4, 4).colliderect(self.labirinto.porta)
        if not encostou:
            return
        if self.labirinto.porta_aberta:
            self.iniciar_saida()
        else:
            self.mostrar_mensagem("A porta está trancada! Encontre a chave.")

    def ferir_jogador(self, mensagem):
        """Tira uma vida e dispara os efeitos de dano (tremor, clarão, partículas)."""
        self.jogador.perder_vida()
        self.tremor = TEMPO_TREMOR
        self.flash_dano = TEMPO_FLASH_DANO
        x, y = self.jogador.retangulo.center
        self.particulas.explosao(x, y, [COR_VIDA, (255, 130, 130), (120, 20, 30)], 18, 130)
        if self.jogador.vidas <= 0:
            self.estado = ESTADO_GAME_OVER
            self.tempo_fim = 0.0
            if self.perseguicao is None:      # o recorde de fase é só dos modos de fases
                self.recorde_fase = max(self.recorde_fase, self.numero_fase)
        else:
            self.mostrar_mensagem(mensagem)

    def verificar_inimigos(self):
        """Tira uma vida se um inimigo tocar o jogador (e ele não estiver protegido)."""
        if self.jogador.invulneravel:
            return
        for inimigo in self.inimigos:
            if inimigo.hitbox.colliderect(self.jogador.hitbox):
                self.ferir_jogador("Um monstro te atingiu!")
                return

    def verificar_armadilhas(self):
        """Tira uma vida se o jogador pisar em espinhos que estejam para fora."""
        if self.jogador.invulneravel:
            return
        for armadilha in self.armadilhas:
            if armadilha.estado == "ativa" and \
                    armadilha.area_dano.colliderect(self.jogador.hitbox):
                self.ferir_jogador("Espinhos! Fique atento ao aviso vermelho.")
                return

    def atualizar_cronometro(self, dt_real):
        """Desconta o tempo REAL decorrido (não depende do FPS)."""
        self.tempo_restante -= dt_real
        if self.tempo_restante <= 0:
            self.ferir_jogador("Tempo esgotado! Você perdeu uma vida.")
            if self.estado == ESTADO_JOGANDO:
                self.tempo_restante = float(self.tempo_limite)

    # ---------------- laço principal ----------------
    def menu_atual(self):
        """Menu de botões ativo no estado atual (ou None se não há botões na tela)."""
        if self.estado == ESTADO_MENU:
            return self.menu_principal
        if self.estado == ESTADO_MODOS:
            return self.menu_modos
        if self.estado == ESTADO_DIFICULDADE:
            return self.menu_dificuldade
        if self.estado == ESTADO_PAUSADO:
            return self.menu_pausa
        if self.estado in (ESTADO_GAME_OVER, ESTADO_VITORIA) and self.tempo_fim >= 0.6:
            return self.menu_fim
        return None

    def ir_para_menu(self):
        self.estado = ESTADO_MENU
        self.menu_principal.selecionado = 0
        self.tempo_menu = 0.0

    def executar_acao(self, acao):
        """Faz o que o botão escolhido pede."""
        if acao == "iniciar":
            self.estado = ESTADO_MODOS
            self.menu_modos.selecionado = 0
            self.tempo_menu = 0.0
        elif acao == "instrucoes":
            self.estado = ESTADO_INSTRUCOES
            self.tempo_menu = 0.0
        elif acao == "sair":
            self.rodando = False
        elif acao == "campanha":
            self.modo_infinito = False
            self.modo_perseguicao = False
            self.novo_jogo()
        elif acao == "infinito":
            # o infinito pede a dificuldade antes de começar
            self.estado = ESTADO_DIFICULDADE
            self.menu_dificuldade.selecionado = 1        # começa em Médio (o padrão)
            self.tempo_menu = 0.0
        elif acao in DIFICULDADES_INFINITO:
            self.dificuldade_infinito = acao
            self.modo_infinito = True
            self.modo_perseguicao = False
            self.novo_jogo()
        elif acao == "voltar_modos":
            self.estado = ESTADO_MODOS
            self.tempo_menu = 0.0
        elif acao == "perseguicao":
            self.modo_perseguicao = True
            self.modo_infinito = False
            self.novo_jogo()
        elif acao == "voltar":
            self.ir_para_menu()
        elif acao == "continuar":
            self.estado = ESTADO_JOGANDO
        elif acao == "reiniciar":
            self.novo_jogo()
        elif acao == "menu":
            self.ir_para_menu()

    def tratar_tecla(self, tecla):
        confirmar = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)
        if self.estado == ESTADO_INSTRUCOES:
            if tecla in confirmar + (pygame.K_ESCAPE,):
                self.ir_para_menu()
            return
        if self.estado == ESTADO_JOGANDO:
            if self.perseguicao is not None and self.perseguicao.tratar_tecla(self, tecla):
                return                                  # item, loja ou santuário usou a tecla
            if tecla in (pygame.K_ESCAPE, pygame.K_p):
                self.estado = ESTADO_PAUSADO
                self.menu_pausa.selecionado = 0
                self.tempo_menu = 0.0
            elif tecla == pygame.K_l:
                self.luz_ativada = not self.luz_ativada
                self.mostrar_mensagem("Iluminação ligada" if self.luz_ativada
                                      else "Iluminação desligada")
            return
        menu = self.menu_atual()
        if menu is not None:
            if tecla in (pygame.K_UP, pygame.K_w):
                menu.mover(-1)
            elif tecla in (pygame.K_DOWN, pygame.K_s):
                menu.mover(1)
            elif tecla in confirmar:
                self.executar_acao(menu.acao_selecionada())
                return
        if self.estado == ESTADO_PAUSADO and tecla in (pygame.K_ESCAPE, pygame.K_p):
            self.executar_acao("continuar")
        elif self.estado == ESTADO_MODOS and tecla == pygame.K_ESCAPE:
            self.executar_acao("voltar")
        elif self.estado == ESTADO_DIFICULDADE and tecla == pygame.K_ESCAPE:
            self.executar_acao("voltar_modos")
        elif self.estado in (ESTADO_GAME_OVER, ESTADO_VITORIA):
            if tecla == pygame.K_r:
                self.executar_acao("reiniciar")
            elif tecla in (pygame.K_m, pygame.K_ESCAPE):
                self.executar_acao("menu")

    def tratar_eventos(self):
        for evento in pygame.event.get():
            if self.perseguicao is not None and self.perseguicao.tratar_mouse(self, evento):
                continue                                # clique/movimento na loja
            if evento.type == pygame.QUIT:
                self.rodando = False
            elif evento.type == pygame.MOUSEMOTION:
                self.mouse_pos = evento.pos
                menu = self.menu_atual()
                if menu is not None:
                    menu.passar_mouse(evento.pos)
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                menu = self.menu_atual()
                if menu is not None:
                    acao = menu.clicar(evento.pos)
                    if acao is not None:
                        self.executar_acao(acao)
                elif self.estado == ESTADO_INSTRUCOES:
                    self.ir_para_menu()
            elif evento.type == pygame.KEYDOWN:
                self.tratar_tecla(evento.key)

    def atualizar_efeitos(self, dt, dt_real):
        """Anima o que é puramente visual (roda mesmo durante transições e telas finais)."""
        self.tempo_animacao += dt
        self.particulas.atualizar(dt)
        self.labirinto.atualizar(dt)
        self.tremor = max(0.0, self.tremor - dt_real)
        self.flash_dano = max(0.0, self.flash_dano - dt_real)
        self.tempo_titulo = max(0.0, self.tempo_titulo - dt_real)
        if self.tempo_mensagem > 0:
            self.tempo_mensagem -= dt_real
        # A pontuação exibida "corre" até a pontuação real
        diferenca = self.pontos - self.pontos_exibidos
        if diferenca > 0:
            self.pontos_exibidos += min(diferenca, max(60 * dt_real, diferenca * 8 * dt_real))
        # Brasas subindo das tochas
        for x, y in self.labirinto.tochas:
            if random.random() < dt * 2.5:
                self.particulas.brasa(x, y - 8)

    def atualizar(self, dt, dt_real):
        if self.estado in (ESTADO_MENU, ESTADO_MODOS, ESTADO_DIFICULDADE, ESTADO_INSTRUCOES):
            self.tempo_menu += dt_real
            self.fundo_menu.atualizar(dt, self.mouse_pos)
            return
        if self.estado == ESTADO_PAUSADO:
            self.tempo_menu += dt_real      # só a interface da pausa anima; o jogo fica parado
            return
        self.atualizar_efeitos(dt, dt_real)
        if self.estado != ESTADO_JOGANDO:
            self.tempo_fim += dt_real
            if self.transicao is not None:
                self.atualizar_transicao(dt_real)
            return
        if self.transicao is not None:
            if self.perseguicao is not None:
                self.perseguicao.passar_tempo_transicao(dt_real)   # efeitos continuam expirando
            self.atualizar_transicao(dt_real)
            return
        self.jogador.atualizar(dt, self.labirinto)
        self.atualizar_poeira(dt)
        self.coletar_itens()
        self.verificar_saida()
        if self.transicao is not None:
            return
        for inimigo in self.inimigos:
            inimigo.atualizar(dt, self.labirinto, self.jogador)
        for armadilha in self.armadilhas:
            armadilha.atualizar(dt)
        self.verificar_inimigos()
        if self.perseguicao is not None and self.estado == ESTADO_JOGANDO:
            self.perseguicao.atualizar(self, dt, dt_real)
        if self.estado == ESTADO_JOGANDO:
            self.verificar_armadilhas()
        if self.estado == ESTADO_JOGANDO and self.perseguicao is None:
            self.atualizar_cronometro(dt_real)      # a Perseguição não tem limite de tempo

    def atualizar_poeira(self, dt):
        """Solta uma nuvenzinha de poeira de vez em quando enquanto o jogador anda."""
        if not self.jogador.andando:
            return
        self.tempo_poeira -= dt
        if self.tempo_poeira <= 0:
            retangulo = self.jogador.retangulo
            self.particulas.poeira(retangulo.centerx, retangulo.bottom - 2)
            self.tempo_poeira = INTERVALO_POEIRA

    # ---------------- desenho ----------------
    def deslocamento_tremor(self):
        """Pequeno deslocamento aleatório da cena enquanto a tela treme."""
        if self.tremor <= 0:
            return (0, 0)
        forca = int(INTENSIDADE_TREMOR * self.tremor / TEMPO_TREMOR)
        return (random.randint(-forca, forca), random.randint(-forca, forca))

    def desenhar(self):
        if self.estado in (ESTADO_MENU, ESTADO_MODOS, ESTADO_DIFICULDADE, ESTADO_INSTRUCOES):
            self.desenhar_telas_de_menu()
            pygame.display.flip()
            return
        cena = self.cena
        self.labirinto.desenhar(cena, self.tempo_animacao)
        for armadilha in self.armadilhas:
            armadilha.desenhar(cena)
        for item in self.itens:
            item.desenhar(cena, self.tempo_animacao)
        for inimigo in self.inimigos:
            inimigo.desenhar(cena)
        if self.perseguicao is not None:
            self.perseguicao.desenhar_mundo(self, cena)
        self.jogador.desenhar(cena)
        if self.perseguicao is not None:
            self.perseguicao.desenhar_sobre_jogador(self, cena)
        self.particulas.desenhar(cena, self.fonte_pequena)
        if self.luz_ativada:
            escuridao = self.nivel["escuridao"]
            self.iluminacao.desenhar(cena, self.jogador.retangulo.center,
                                     self.labirinto.tochas, self.tempo_animacao, escuridao)
        if self.perseguicao is not None:
            self.perseguicao.desenhar_apos_luz(self, cena)
        cena.blit(self.vinheta, (0, 0))

        # A cena (com tremor) vai para a tela; a interface fica por cima, sem tremer
        self.tela.fill(COR_FUNDO)
        self.tela.blit(cena, self.deslocamento_tremor())
        self.desenhar_hud()
        self.desenhar_flash_dano()
        if self.tempo_titulo > 0 and self.estado == ESTADO_JOGANDO:
            self.desenhar_titulo_fase()
        if self.tempo_mensagem > 0 and self.estado == ESTADO_JOGANDO:
            self.desenhar_mensagem()
        if self.perseguicao is not None and self.estado == ESTADO_JOGANDO:
            self.perseguicao.desenhar_interface(self)       # aviso do santuário e loja
        if self.estado == ESTADO_PAUSADO:
            self.desenhar_pausa()
        elif self.estado == ESTADO_GAME_OVER:
            self.desenhar_tela_final("GAME OVER", COR_ALERTA)
        elif self.estado == ESTADO_VITORIA:
            self.desenhar_tela_final("VOCÊ ESCAPOU!", COR_SUCESSO)
        self.desenhar_fade()
        pygame.display.flip()

    def desenhar_texto(self, texto, fonte, cor, posicao, centralizar=False):
        imagem = fonte.render(texto, True, cor)
        retangulo = imagem.get_rect()
        if centralizar:
            retangulo.center = posicao
        else:
            retangulo.topleft = posicao
        self.tela.blit(imagem, retangulo)

    def desenhar_hud(self):
        if self.perseguicao is not None:
            self.perseguicao.desenhar_hud(self)             # barra própria do modo
            return
        self.tela.blit(self.fundo_hud, (0, 0))
        self.desenhar_texto(f"Fase {self.numero_fase} - {self.nivel['nome']}",
                            self.fonte_titulo, COR_TEXTO, (20, 8))

        if self.modo_infinito:
            # Modo infinito: mostra o recorde da sessão no canto
            recorde = max(self.recorde_fase, self.numero_fase)
            nome_dificuldade = DIFICULDADES_INFINITO[self.dificuldade_infinito]["nome"]
            imagem = self.fonte_pequena.render(f"{nome_dificuldade}  |  Recorde: fase {recorde}",
                                               True, (190, 160, 90))
            self.tela.blit(imagem, imagem.get_rect(topright=(LARGURA_JANELA - 20, 14)))
        else:
            # Campanha: uma bolinha por fase (cheia = já alcançada)
            for i in range(len(NIVEIS)):
                centro = (LARGURA_JANELA - 40 - (len(NIVEIS) - 1 - i) * 26, 22)
                if i < self.numero_fase:
                    pygame.draw.circle(self.tela, COR_OURO, centro, 8)
                pygame.draw.circle(self.tela, (150, 110, 40), centro, 8, 2)

        y = 44
        # Pontuação (com moeda girando)
        desenhar_icone_moeda(self.tela, 20, y, self.tempo_animacao)
        self.desenhar_texto(str(int(self.pontos_exibidos)), self.fonte, COR_OURO, (50, y))

        # Vidas: com uma vida só, o coração bate
        pulso = 0.0
        if self.jogador.vidas == 1:
            pulso = (math.sin(self.tempo_animacao * 8) + 1) / 2
        for i in range(max(self.vidas_iniciais, self.jogador.vidas)):
            cheio = i < self.jogador.vidas
            desenhar_coracao(self.tela, 250 + i * 32, y + 1, cheio,
                             pulso if cheio and self.jogador.vidas == 1 else 0.0)

        # Cronômetro: pisca em vermelho quando está acabando
        segundos = max(0, math.ceil(self.tempo_restante))
        urgente = segundos <= TEMPO_ALERTA
        cor_tempo = COR_ALERTA if urgente and int(self.tempo_animacao * 3) % 2 == 0 \
            else (COR_TEXTO if not urgente else (255, 140, 120))
        desenhar_icone_relogio(self.tela, 480, y, cor_tempo, self.tempo_animacao)
        self.desenhar_texto(f"{segundos // 60}:{segundos % 60:02d}", self.fonte,
                            cor_tempo, (510, y))

        # Chaves: um ícone por chave necessária (dourado quando coletada)
        for i in range(self.chaves_necessarias):
            desenhar_icone_chave(self.tela, 690 + i * 30, y, i < self.chaves_coletadas)
        self.desenhar_texto(f"{self.chaves_coletadas}/{self.chaves_necessarias}",
                            self.fonte, COR_OURO, (690 + self.chaves_necessarias * 30 + 6, y))

    def desenhar_flash_dano(self):
        """Clarão vermelho que some depressa quando o jogador leva dano."""
        if self.flash_dano <= 0:
            return
        alfa = int(120 * self.flash_dano / TEMPO_FLASH_DANO)
        self.veu.fill((200, 30, 30, alfa))
        self.tela.blit(self.veu, (0, 0))

    def desenhar_titulo_fase(self):
        """Faixa 'FASE N - nome' que surge e desaparece suavemente."""
        t = self.tempo_titulo
        fator = max(0.0, min(1.0, (TEMPO_TITULO_FASE - t) / 0.4, t / 0.5))
        faixa = pygame.Surface((LARGURA_JANELA, 96), pygame.SRCALPHA)
        faixa.fill((0, 0, 0, int(170 * fator)))
        deslocamento = int((1 - fator) * 24)
        self.tela.blit(faixa, (0, 270 + deslocamento))
        nome = self.nivel["nome"]
        rotulo = (f"PERSEGUIÇÃO - MAPA {self.numero_fase}" if self.perseguicao is not None
                  else f"FASE {self.numero_fase}")
        for texto, fonte, cor, y in [(rotulo, self.fonte, COR_OURO, 298),
                                     (nome, self.fonte_titulo, COR_TEXTO, 334)]:
            imagem = fonte.render(texto, True, cor)
            imagem.set_alpha(int(255 * fator))
            self.tela.blit(imagem, imagem.get_rect(center=(LARGURA_JANELA // 2,
                                                           y + deslocamento)))

    def desenhar_mensagem(self):
        """Faixa com um aviso temporário na parte de baixo da tela."""
        imagem = self.fonte.render(self.mensagem, True, COR_TEXTO)
        fundo = imagem.get_rect(center=(LARGURA_JANELA // 2, ALTURA_JANELA - 30))
        fundo.inflate_ip(30, 14)
        pygame.draw.rect(self.tela, (0, 0, 0), fundo, border_radius=8)
        pygame.draw.rect(self.tela, COR_OURO, fundo, 2, border_radius=8)
        self.tela.blit(imagem, imagem.get_rect(center=fundo.center))

    def desenhar_telas_de_menu(self):
        """Menu inicial, escolha de modo e instruções sobre o cenário animado."""
        self.fundo_menu.desenhar(self.tela)
        if self.estado == ESTADO_INSTRUCOES:
            desenhar_instrucoes(self.tela, self.fonte_gigante, self.fonte_titulo,
                                self.fonte_pequena, self.tempo_menu)
            return
        desenhar_titulo(self.tela, self.fonte_logo, self.fonte_sublogo, self.tempo_menu)
        meio = LARGURA_JANELA // 2
        if self.estado == ESTADO_MENU:
            self.menu_principal.desenhar(self.tela, self.fonte_botao, self.tempo_menu)
            dica = "Setas ou mouse para escolher  -  ENTER para confirmar"
        elif self.estado == ESTADO_DIFICULDADE:
            desenhar_texto_contorno(self.tela, self.fonte, "ESCOLHA A DIFICULDADE",
                                    COR_OURO, (meio, 244))
            self.menu_dificuldade.desenhar(self.tela, self.fonte_botao, self.tempo_menu,
                                           self.fonte_pequena)
            dica = "Muda só as vidas iniciais. Setas ou mouse  -  ENTER confirma  -  ESC volta"
        else:
            desenhar_texto_contorno(self.tela, self.fonte, "Escolha o modo de jogo",
                                    COR_OURO, (meio, 262))
            self.menu_modos.desenhar(self.tela, self.fonte_botao, self.tempo_menu)
            descricoes = ["As 5 fases fixas, terminando no covil do Dragão.",
                          "Fases aleatórias sem fim. Até onde você chega?",
                          "Fuja do Guardião das Trevas, compre melhorias e escape.",
                          "Voltar ao menu principal."]
            dica = descricoes[self.menu_modos.selecionado]
        desenhar_texto_contorno(self.tela, self.fonte_pequena, dica, COR_TEXTO,
                                (meio, ALTURA_JANELA - 24), (10, 8, 14), 2)

    def desenhar_pausa(self):
        """Véu escuro, título pulsante e botões; a cena continua visível ao fundo."""
        self.veu.fill((0, 0, 0, 165))
        self.tela.blit(self.veu, (0, 0))
        meio = LARGURA_JANELA // 2
        pulso = int(abs(math.sin(self.tempo_menu * 3)) * 40)
        desenhar_texto_contorno(self.tela, self.fonte_logo, "PAUSADO",
                                (240, 200 + pulso // 2, 60 + pulso), (meio, 220),
                                (60, 30, 5), 4)
        self.menu_pausa.desenhar(self.tela, self.fonte_botao, self.tempo_menu)
        desenhar_texto_contorno(self.tela, self.fonte_pequena,
                                "P ou ESC para continuar", COR_TEXTO, (meio, 500),
                                (10, 8, 14), 2)

    def desenhar_tela_final(self, titulo, cor):
        """Tela de fim de jogo: o véu escurece aos poucos e o título 'cai' na tela."""
        alfa = min(190, int(self.tempo_fim * 400))
        self.veu.fill((0, 0, 0, alfa))
        self.tela.blit(self.veu, (0, 0))
        progresso = min(1.0, self.tempo_fim / 0.6)
        queda = int((1 - progresso) ** 2 * 120)           # desacelera ao chegar
        centro = LARGURA_JANELA // 2
        pulso = 1.0 + 0.04 * math.sin(self.tempo_fim * 4)
        imagem = self.fonte_gigante.render(titulo, True, cor)
        tamanho = (int(imagem.get_width() * pulso), int(imagem.get_height() * pulso))
        imagem = pygame.transform.scale(imagem, tamanho)
        imagem.set_alpha(int(255 * progresso))
        self.tela.blit(imagem, imagem.get_rect(center=(centro, 240 - queda)))
        if progresso >= 1.0:
            self.desenhar_texto(f"Pontuação final: {self.pontos}", self.fonte_titulo,
                                COR_OURO, (centro, 330), centralizar=True)
            if self.modo_infinito:
                self.desenhar_texto(
                    f"Você chegou à fase {self.numero_fase}  |  Recorde: fase {self.recorde_fase}",
                    self.fonte, COR_TEXTO, (centro, 372), centralizar=True)
            elif self.perseguicao is not None:
                self.perseguicao.desenhar_estatisticas(self)
            self.menu_fim.desenhar(self.tela, self.fonte_botao, self.tempo_fim)
            self.desenhar_texto("R: jogar novamente   |   M ou ESC: voltar ao menu",
                                self.fonte_pequena, COR_TEXTO, (centro, 590),
                                centralizar=True)

    def desenhar_fade(self):
        """Escurece (saindo) ou clareia (entrando) a tela inteira."""
        if self.transicao is None:
            return
        fracao = min(1.0, self.tempo_transicao / TEMPO_FADE)
        if self.transicao == TRANSICAO_ENTRANDO:
            fracao = 1.0 - fracao
        self.veu.fill((0, 0, 0, int(255 * fracao)))
        self.tela.blit(self.veu, (0, 0))

    def executar(self):
        while self.rodando:
            dt_real = self.relogio.tick(FPS) / 1000.0   # tempo real do quadro
            dt = min(dt_real, 0.05)  # movimento: evita "saltos" se o jogo travar
            self.tratar_eventos()
            self.atualizar(dt, dt_real)
            self.desenhar()
        pygame.quit()
        sys.exit()


def main():
    # O modo (campanha ou infinito) é escolhido no menu inicial
    Jogo().executar()


if __name__ == "__main__":
    main()