"""
Modo Perseguição - O Guardião das Trevas.

ModoPerseguicao guarda TODOS os dados exclusivos deste modo (saldo, inventário,
efeitos temporários, capturas, Guardião...). Um objeto novo é criado a cada
partida, então nada vaza entre partidas nem para os outros modos.
A classe Jogo (main.py) apenas chama os "ganchos" abaixo nos pontos certos.
"""

import math
import random

import pygame

from constantes import (
    ALTURA_HUD, ALTURA_JANELA, COR_ALERTA, COR_OURO, COR_SUCESSO, COR_TEXTO,
    ESTADO_GAME_OVER, ESTADO_JOGANDO, LARGURA_JANELA,
    TAMANHO_TILE, TEMPO_INVULNERAVEL, TEMPO_TREMOR, TEMPO_FLASH_DANO,
    TIPO_CHAVE, VIDAS_INICIAIS,
)
from constantes_perseguicao import (
    AMOSTRAS_REPOSICIONAMENTO, BONUS_SEM_CAPTURA, CATALOGO, DISTANCIA_ALERTA,
    DISTANCIA_CALMA, DISTANCIA_INTERACAO_SANTUARIO, DISTANCIA_PERIGO,
    DISTANCIA_REAPARECER_GUARDIAO, DISTANCIA_SEGURA_JOGADOR, DURACAO_BUSSOLA,
    DURACAO_INVISIBILIDADE, DURACAO_VELOCIDADE, FATOR_VELOCIDADE_POCAO,
    INTERVALO_BUSSOLA, INTERVALO_PROXIMIDADE, ITEM_BUSSOLA, ITEM_CURA,
    ITEM_ESCUDO, ITEM_INVISIBILIDADE, ITEM_VELOCIDADE, LIMITE_BFS,
    NOME_MODO, PONTOS_ESCAPAR, ROTULO_ESTAGIO, SIMBOLO_GUARDIAO,
    SIMBOLO_SANTUARIO, TEMPO_ATORDOADO,
)
from desenho import desenhar_coracao, desenhar_icone_chave, desenhar_icone_moeda
from desenho_perseguicao import (
    criar_vinheta_perigo, desenhar_aura_escudo,
    desenhar_aura_invisivel, desenhar_aura_velocidade,
    desenhar_icone_item, desenhar_indicador_proximidade,
    desenhar_olhos_guardiao, desenhar_santuario, desenhar_seta_bussola,
)
from guardiao import GuardiaoDasTrevas
from interface import desenhar_texto_contorno
from inventario import Inventario
from loja import Loja

TECLAS_ITENS = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2, pygame.K_4: 3, pygame.K_5: 4}


def formatar_tempo(segundos):
    segundos = int(segundos)
    return f"{segundos // 60}:{segundos % 60:02d}"


class RecordesPerseguicao:
    """Recordes DESTE modo (vivem enquanto o programa estiver aberto)."""

    def __init__(self):
        self.melhor_pontuacao = 0
        self.mais_mapas = 0
        self.maior_tempo = 0.0

    def registrar(self, pontos, mapas, tempo):
        self.melhor_pontuacao = max(self.melhor_pontuacao, pontos)
        self.mais_mapas = max(self.mais_mapas, mapas)
        self.maior_tempo = max(self.maior_tempo, tempo)


class ModoPerseguicao:
    def __init__(self, recordes):
        self.recordes = recordes
        self.inventario = Inventario()
        self.loja = Loja()
        self.guardiao = None
        self.santuarios = []                 # Rects dos santuários
        # --- dados da partida ---
        self.saldo = 0                       # moedas para gastar (separado da pontuação)
        self.moedas_coletadas = 0            # total já coletado (estatística)
        self.capturas = 0                    # total da partida
        self.tempo_sobrevivencia = 0.0       # total da partida (não zera ao trocar de mapa)
        self.pontos_vistos = 0               # para detectar quanto foi coletado a cada quadro
        self.bonus_total = 0
        self.mapas_concluidos = 0
        # --- dados do mapa atual (zerados a cada novo mapa em preparar()) ---
        self.tempo_mapa = 0.0
        self.capturas_no_mapa = 0
        # --- efeitos temporários (contados em tempo real) ---
        self.velocidade_restante = 0.0
        self.invisibilidade_restante = 0.0
        self.bussola_restante = 0.0
        self.escudo_ativo = False
        # --- indicadores ---
        self.distancia_guardiao = None
        self.nivel_proximidade = 0.0
        self.espera_proximidade = 0.0
        self.angulo_bussola = None
        self.espera_bussola = 0.0
        self.perto_do_santuario = False
        self._vinheta_perigo = None
        self._escurecer_icone = None

    # ------------------------------------------------------------------
    # Preparação do mapa
    # ------------------------------------------------------------------
    def preparar(self, jogo):
        """
        Chamado a cada mapa novo: lê o mapa, cria o Guardião (com a dificuldade do mapa)
        e registra os santuários. Mantém vidas, moedas, pontos, inventário e efeitos.
        """
        self.santuarios = []
        self.tempo_mapa = 0.0
        self.capturas_no_mapa = 0
        self.distancia_guardiao = None
        self.nivel_proximidade = 0.0
        self.espera_proximidade = 0.0
        self.angulo_bussola = None
        self.espera_bussola = 0.0
        self.perto_do_santuario = False
        self.loja.fechar()
        for linha, texto in enumerate(jogo.nivel["mapa"]):
            for coluna, simbolo in enumerate(texto):
                if simbolo == SIMBOLO_GUARDIAO:
                    self.guardiao = GuardiaoDasTrevas(coluna, linha)
                    dificuldade = jogo.nivel["guardiao"]
                    self.guardiao.fator_mapa = dificuldade["fator_velocidade"]
                    self.guardiao.raio_deteccao = dificuldade["raio_deteccao"]
                    self.guardiao.tempo_furia = dificuldade["tempo_furia"]
                elif simbolo == SIMBOLO_SANTUARIO:
                    self.santuarios.append(pygame.Rect(
                        coluna * TAMANHO_TILE, ALTURA_HUD + linha * TAMANHO_TILE,
                        TAMANHO_TILE, TAMANHO_TILE))
        self.pontos_vistos = jogo.pontos

    # ------------------------------------------------------------------
    # Atualização (chamada todo quadro enquanto se joga)
    # ------------------------------------------------------------------
    def atualizar(self, jogo, dt, dt_real):
        self.tempo_sobrevivencia += dt_real
        self.tempo_mapa += dt_real

        # saldo de moedas = valor dos itens coletados (a pontuação fica intacta)
        ganho = jogo.pontos - self.pontos_vistos
        if ganho > 0:
            self.saldo += ganho
            self.moedas_coletadas += ganho
        self.pontos_vistos = jogo.pontos

        # efeitos temporários (tempo real, não dependem do FPS)
        self.velocidade_restante = max(0.0, self.velocidade_restante - dt_real)
        self.invisibilidade_restante = max(0.0, self.invisibilidade_restante - dt_real)
        self.bussola_restante = max(0.0, self.bussola_restante - dt_real)
        jogo.jogador.fator_velocidade = (FATOR_VELOCIDADE_POCAO
                                         if self.velocidade_restante > 0 else 1.0)
        jogo.jogador.bloqueado = self.loja.aberta     # com a loja aberta o jogador fica parado

        # Guardião (continua ativo mesmo com a loja aberta)
        guardiao = self.guardiao
        guardiao.tempo = self.tempo_mapa          # a progressão por tempo recomeça a cada mapa
        guardiao.jogador_visivel = self.invisibilidade_restante <= 0
        guardiao.atualizar(dt, jogo.labirinto, jogo.jogador)

        self._atualizar_proximidade(jogo, dt, dt_real)
        self._atualizar_santuario(jogo)
        self._atualizar_bussola(jogo, dt_real)
        self.loja.atualizar(dt_real)
        self._verificar_captura(jogo)

    def _atualizar_proximidade(self, jogo, dt, dt_real):
        """Mede a distância (em tiles de caminho) a cada INTERVALO_PROXIMIDADE segundos."""
        self.espera_proximidade -= dt_real
        if self.espera_proximidade <= 0:
            self.espera_proximidade = INTERVALO_PROXIMIDADE
            labirinto = jogo.labirinto
            origem = (self.guardiao.coluna, self.guardiao.linha)
            alvo = labirinto.tile_do_ponto(jogo.jogador.retangulo.center)
            caminho = labirinto.caminho_bfs(origem, alvo, DISTANCIA_CALMA)
            self.distancia_guardiao = None if caminho is None else len(caminho)
        d = self.distancia_guardiao
        if d is None:
            alvo_nivel = 0.0
        elif d <= DISTANCIA_PERIGO:
            alvo_nivel = 1.0
        else:
            alvo_nivel = max(0.0, 1.0 - (d - DISTANCIA_PERIGO) / (DISTANCIA_CALMA - DISTANCIA_PERIGO))
        self.nivel_proximidade += (alvo_nivel - self.nivel_proximidade) * min(1.0, dt_real * 6)

    def rotulo_proximidade(self):
        d = self.distancia_guardiao
        if d is not None and d <= DISTANCIA_PERIGO:
            return "PERIGO!", COR_ALERTA
        if d is not None and d <= DISTANCIA_ALERTA:
            return "ALERTA", COR_OURO
        return "Tranquilo", COR_SUCESSO

    def _atualizar_santuario(self, jogo):
        """Descobre se o jogador está perto de um santuário; fecha a loja se ele se afastou."""
        zona = jogo.jogador.retangulo.inflate(DISTANCIA_INTERACAO_SANTUARIO * 2,
                                              DISTANCIA_INTERACAO_SANTUARIO * 2)
        self.perto_do_santuario = any(zona.colliderect(s) for s in self.santuarios)
        if self.loja.aberta and not self.perto_do_santuario:
            self.loja.fechar()

    def _alvo_da_bussola(self, jogo):
        """Tile da chave (se ainda não pegou) ou do corredor junto à porta."""
        labirinto = jogo.labirinto
        if jogo.chaves_coletadas < jogo.chaves_necessarias:
            for item in jogo.itens:
                if item.tipo == TIPO_CHAVE:
                    return labirinto.tile_do_ponto(item.retangulo.center)
        coluna, linha = labirinto.tile_do_ponto(labirinto.porta.center)
        for d_coluna, d_linha in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if labirinto.tile_livre(coluna + d_coluna, linha + d_linha):
                return (coluna + d_coluna, linha + d_linha)
        return (coluna, linha)

    def _atualizar_bussola(self, jogo, dt_real):
        if self.bussola_restante <= 0:
            self.angulo_bussola = None
            return
        self.espera_bussola -= dt_real
        if self.espera_bussola > 0:
            return
        self.espera_bussola = INTERVALO_BUSSOLA
        labirinto = jogo.labirinto
        origem = labirinto.tile_do_ponto(jogo.jogador.retangulo.center)
        alvo = self._alvo_da_bussola(jogo)
        caminho = labirinto.caminho_bfs(origem, alvo, LIMITE_BFS)
        px, py = jogo.jogador.retangulo.center
        if caminho:
            proximo = caminho[0]
            destino = (proximo[0] * TAMANHO_TILE + TAMANHO_TILE // 2,
                       ALTURA_HUD + proximo[1] * TAMANHO_TILE + TAMANHO_TILE // 2)
        else:
            destino = (alvo[0] * TAMANHO_TILE + TAMANHO_TILE // 2,
                       ALTURA_HUD + alvo[1] * TAMANHO_TILE + TAMANHO_TILE // 2)
        self.angulo_bussola = math.atan2(destino[1] - py, destino[0] - px)

    # ------------------------------------------------------------------
    # Captura, escudo e reposicionamento
    # ------------------------------------------------------------------
    def _verificar_captura(self, jogo):
        jogador = jogo.jogador
        guardiao = self.guardiao
        if jogador.invulneravel or guardiao.atordoado > 0:
            return
        if not guardiao.hitbox.colliderect(jogador.hitbox):
            return
        # o escudo ativo (ou um da bolsa, usado automaticamente) bloqueia a captura
        if self.escudo_ativo or self.inventario.consumir(ITEM_ESCUDO):
            self.escudo_ativo = False
            self._bloquear_com_escudo(jogo)
        else:
            self._capturar(jogo)

    def _bloquear_com_escudo(self, jogo):
        """O escudo se desfaz; o jogador ganha um instante de proteção e o Guardião fica atordoado."""
        jogo.jogador.invulneravel_restante = TEMPO_INVULNERAVEL
        self.guardiao.atordoado = TEMPO_ATORDOADO
        x, y = jogo.jogador.retangulo.center
        jogo.particulas.explosao(x, y, [(120, 180, 255), (200, 230, 255), (70, 110, 220)], 22, 150)
        jogo.particulas.texto(x, y - 24, "ESCUDO!", (150, 200, 255))
        jogo.tremor = TEMPO_TREMOR / 2
        jogo.mostrar_mensagem("O escudo bloqueou o Guardião!")

    def _capturar(self, jogo):
        """O Guardião pegou o jogador: perde uma vida e a perseguição recomeça longe dali."""
        self.capturas += 1
        self.capturas_no_mapa += 1
        jogo.jogador.perder_vida()                   # também ativa a invulnerabilidade
        jogo.tremor = TEMPO_TREMOR
        jogo.flash_dano = TEMPO_FLASH_DANO
        x, y = jogo.jogador.retangulo.center
        jogo.particulas.explosao(x, y, [(96, 36, 160), (30, 10, 50), (200, 80, 255), (180, 30, 50)],
                                 26, 150, 0.7)
        self.loja.fechar()
        if jogo.jogador.vidas <= 0:
            jogo.estado = ESTADO_GAME_OVER
            jogo.tempo_fim = 0.0
            self.recordes.registrar(jogo.pontos, self.mapas_concluidos, self.tempo_sobrevivencia)
            return
        jogo.mostrar_mensagem("O Guardião das Trevas te capturou!")
        self._reposicionar(jogo)

    def _distancia(self, labirinto, origem, destino):
        caminho = labirinto.caminho_bfs(origem, destino, LIMITE_BFS)
        return None if caminho is None else len(caminho)

    def _tiles_validos(self, jogo):
        """Tiles livres, sem armadilha: candidatos a reposicionamento."""
        labirinto = jogo.labirinto
        armadilhas = {labirinto.tile_do_ponto(a.retangulo.center) for a in jogo.armadilhas}
        return [(coluna, linha)
                for linha, texto in enumerate(labirinto.desenho)
                for coluna in range(len(texto))
                if labirinto.tile_livre(coluna, linha) and (coluna, linha) not in armadilhas]

    def _escolher_distante(self, labirinto, origem, candidatos, minimo):
        """Sorteia um tile a pelo menos 'minimo' passos de 'origem' (ou o mais distante achado)."""
        amostra = random.sample(candidatos, min(AMOSTRAS_REPOSICIONAMENTO, len(candidatos)))
        medidos = []
        for tile in amostra:
            distancia = self._distancia(labirinto, origem, tile)
            if distancia is not None:
                medidos.append((distancia, tile))
        bons = [tile for distancia, tile in medidos if distancia >= minimo]
        if bons:
            return random.choice(bons)
        return max(medidos)[1] if medidos else origem

    def _reposicionar(self, jogo):
        """Jogador num ponto seguro e longe do Guardião; depois o Guardião, longe do jogador."""
        labirinto = jogo.labirinto
        validos = self._tiles_validos(jogo)
        origem_guardiao = (self.guardiao.coluna, self.guardiao.linha)
        ponto_jogador = self._escolher_distante(labirinto, origem_guardiao, validos,
                                                DISTANCIA_SEGURA_JOGADOR)
        jogo.jogador.posicionar((ponto_jogador[0] * TAMANHO_TILE,
                                 ALTURA_HUD + ponto_jogador[1] * TAMANHO_TILE))
        ponto_guardiao = self._escolher_distante(labirinto, ponto_jogador, validos,
                                                 DISTANCIA_REAPARECER_GUARDIAO)
        self.guardiao.posicionar(*ponto_guardiao)

    # ------------------------------------------------------------------
    # Loja e inventário
    # ------------------------------------------------------------------
    def comprar(self, jogo, indice):
        """Compra o item 'indice' do catálogo. Retorna True se a compra foi feita."""
        item = CATALOGO[indice]
        if self.saldo < item["preco"]:
            self.loja.avisar("Moedas insuficientes!", erro=True)
            return False
        if self.inventario.cheio(item["id"]):
            self.loja.avisar("Você já carrega o máximo desse item.", erro=True)
            return False
        self.saldo -= item["preco"]                   # saldo atualizado na hora
        self.inventario.adicionar(item["id"])
        self.loja.avisar(f"Comprou: {item['nome']}")
        x, y = jogo.jogador.retangulo.center
        jogo.particulas.explosao(x, y, [COR_OURO, (255, 240, 150)], 10, 90, 0.5)
        return True

    def usar_item(self, jogo, item_id):
        """Usa um item do inventário (só se existir e se fizer sentido usá-lo agora)."""
        nome = next(i["nome"] for i in CATALOGO if i["id"] == item_id)
        if not self.inventario.tem(item_id):
            jogo.mostrar_mensagem(f"Você não tem: {nome}.")
            return False
        x, y = jogo.jogador.retangulo.center
        if item_id == ITEM_CURA:
            if jogo.jogador.vidas >= VIDAS_INICIAIS:
                jogo.mostrar_mensagem("Suas vidas já estão completas.")
                return False
            jogo.jogador.vidas += 1
            jogo.particulas.explosao(x, y, [(255, 120, 130), (255, 220, 220)], 16, 100)
            jogo.particulas.texto(x, y - 20, "+1 VIDA", (255, 120, 130))
        elif item_id == ITEM_VELOCIDADE:
            if self.velocidade_restante > 0:
                jogo.mostrar_mensagem("A poção da velocidade já está ativa.")
                return False
            self.velocidade_restante = DURACAO_VELOCIDADE
            jogo.particulas.texto(x, y - 20, "VELOZ!", (255, 235, 110))
        elif item_id == ITEM_ESCUDO:
            if self.escudo_ativo:
                jogo.mostrar_mensagem("O escudo já está ativo.")
                return False
            self.escudo_ativo = True
            jogo.particulas.texto(x, y - 20, "ESCUDO", (150, 200, 255))
        elif item_id == ITEM_INVISIBILIDADE:
            if self.invisibilidade_restante > 0:
                jogo.mostrar_mensagem("Você já está invisível.")
                return False
            self.invisibilidade_restante = DURACAO_INVISIBILIDADE
            jogo.particulas.texto(x, y - 20, "INVISÍVEL", (210, 225, 255))
        elif item_id == ITEM_BUSSOLA:
            if self.bussola_restante > 0:
                jogo.mostrar_mensagem("A bússola já está ativa.")
                return False
            self.bussola_restante = DURACAO_BUSSOLA
            self.espera_bussola = 0.0
        self.inventario.consumir(item_id)
        return True

    # ------------------------------------------------------------------
    # Fim de partida
    # ------------------------------------------------------------------
    def ao_escapar(self, jogo):
        """
        O jogador atravessou a porta: conta o mapa, soma os bônus e registra os recordes.
        O próximo mapa é gerado pelo Jogo; tudo o que é do jogador continua com ele.
        """
        self.mapas_concluidos += 1
        bonus = PONTOS_ESCAPAR
        if self.capturas_no_mapa == 0:
            bonus += BONUS_SEM_CAPTURA              # mapa sem nenhuma captura
        self.bonus_total += bonus
        jogo.pontos += bonus
        self.pontos_vistos = jogo.pontos            # bônus de pontuação não vira moeda
        self.loja.fechar()
        x, y = jogo.jogador.retangulo.center
        jogo.particulas.texto(x, y - 24, f"MAPA {self.mapas_concluidos} CONCLUÍDO +{bonus}", COR_SUCESSO)
        self.recordes.registrar(jogo.pontos, self.mapas_concluidos, self.tempo_sobrevivencia)

    def passar_tempo_transicao(self, dt_real):
        """Durante a troca de mapa o jogo congela, mas os efeitos temporários continuam expirando."""
        self.velocidade_restante = max(0.0, self.velocidade_restante - dt_real)
        self.invisibilidade_restante = max(0.0, self.invisibilidade_restante - dt_real)
        self.bussola_restante = max(0.0, self.bussola_restante - dt_real)

    # ------------------------------------------------------------------
    # Entrada (teclado e mouse)
    # ------------------------------------------------------------------
    def tratar_tecla(self, jogo, tecla):
        """Retorna True se a tecla foi consumida por este modo."""
        if jogo.estado != ESTADO_JOGANDO or jogo.transicao is not None:
            return False
        if self.loja.aberta:
            if tecla in (pygame.K_UP, pygame.K_w):
                self.loja.mover(-1)
            elif tecla in (pygame.K_DOWN, pygame.K_s):
                self.loja.mover(1)
            elif tecla in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.comprar(jogo, self.loja.selecionado)
            elif tecla in TECLAS_ITENS:
                self.comprar(jogo, TECLAS_ITENS[tecla])
            elif tecla in (pygame.K_e, pygame.K_ESCAPE):
                self.loja.fechar()
            else:
                return False
            return True
        if tecla in TECLAS_ITENS:
            self.usar_item(jogo, CATALOGO[TECLAS_ITENS[tecla]]["id"])
            return True
        if tecla == pygame.K_e and self.perto_do_santuario:
            self.loja.abrir()
            return True
        return False

    def tratar_mouse(self, jogo, evento):
        """Cliques e movimento do mouse na loja. Retorna True se consumiu o evento."""
        if not self.loja.aberta or jogo.estado != ESTADO_JOGANDO:
            return False
        if evento.type == pygame.MOUSEMOTION:
            indice = self.loja.indice_em(evento.pos)
            if indice is not None:
                self.loja.selecionado = indice
            return True
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if self.loja.botao_fechar.collidepoint(evento.pos):
                self.loja.fechar()
            else:
                indice = self.loja.indice_em(evento.pos)
                if indice is not None:
                    self.loja.selecionado = indice
                    self.comprar(jogo, indice)
            return True
        return False

    # ------------------------------------------------------------------
    # Desenho (ganchos chamados por Jogo.desenhar)
    # ------------------------------------------------------------------
    def desenhar_mundo(self, jogo, cena):
        """Santuários e Guardião (antes do jogador)."""
        for santuario in self.santuarios:
            desenhar_santuario(cena, santuario.x, santuario.y, jogo.tempo_animacao,
                               self.perto_do_santuario)
        self.guardiao.desenhar(cena)

    def desenhar_sobre_jogador(self, jogo, cena):
        """Auras dos efeitos ativos e seta da bússola (depois do jogador)."""
        centro = jogo.jogador.retangulo.center
        t = jogo.tempo_animacao
        if self.escudo_ativo:
            desenhar_aura_escudo(cena, centro, t)
        if self.velocidade_restante > 0:
            desenhar_aura_velocidade(cena, centro, t)
        if self.invisibilidade_restante > 0:
            desenhar_aura_invisivel(cena, centro, t)
        if self.bussola_restante > 0 and self.angulo_bussola is not None:
            desenhar_seta_bussola(cena, centro, self.angulo_bussola, t)

    def desenhar_apos_luz(self, jogo, cena):
        """Olhos do Guardião (visíveis no escuro) e moldura vermelha de perigo."""
        desenhar_olhos_guardiao(cena, self.guardiao.retangulo, jogo.tempo_animacao,
                                self.guardiao.estagio)
        if self.nivel_proximidade > 0.45:
            if self._vinheta_perigo is None:
                self._vinheta_perigo = criar_vinheta_perigo()
            intensidade = (self.nivel_proximidade - 0.45) / 0.55
            pulso = 0.65 + 0.35 * math.sin(jogo.tempo_animacao * (6 + 6 * intensidade))
            self._vinheta_perigo.set_alpha(int(190 * intensidade * pulso))
            cena.blit(self._vinheta_perigo, (0, 0))

    def desenhar_hud(self, jogo):
        """Barra superior do modo (substitui a barra padrão)."""
        tela = jogo.tela
        t = jogo.tempo_animacao
        tela.blit(jogo.fundo_hud, (0, 0))
        jogo.desenhar_texto(NOME_MODO.upper(), jogo.fonte_titulo, COR_TEXTO, (20, 8))
        jogo.desenhar_texto(f"Mapa {jogo.numero_fase}", jogo.fonte, COR_OURO, (215, 11))
        jogo.desenhar_texto(f"Tempo {formatar_tempo(self.tempo_sobrevivencia)}", jogo.fonte,
                            COR_TEXTO, (320, 11))
        estagio = self.guardiao.estagio
        cor_estagio = COR_ALERTA if estagio != "vigilancia" else (180, 160, 210)
        jogo.desenhar_texto(ROTULO_ESTAGIO[estagio], jogo.fonte_pequena, cor_estagio, (470, 14))
        rotulo, cor_rotulo = self.rotulo_proximidade()
        jogo.desenhar_texto(rotulo, jogo.fonte_pequena, cor_rotulo, (590, 14))
        desenhar_indicador_proximidade(tela, 690, 14, 250, self.nivel_proximidade, t)

        y = 44
        jogo.desenhar_texto(f"PTS {int(jogo.pontos_exibidos)}", jogo.fonte, COR_OURO, (20, y))
        desenhar_icone_moeda(tela, 150, y, t)
        jogo.desenhar_texto(str(self.saldo), jogo.fonte, COR_OURO, (178, y))
        for i in range(VIDAS_INICIAIS):
            desenhar_coracao(tela, 250 + i * 30, y + 1, i < jogo.jogador.vidas)
        desenhar_icone_chave(tela, 352, y, jogo.chaves_coletadas >= jogo.chaves_necessarias)
        jogo.desenhar_texto(f"{jogo.chaves_coletadas}/{jogo.chaves_necessarias}",
                            jogo.fonte_pequena, COR_OURO, (380, y + 4))

        # inventário: [tecla] ícone xquantidade (apagado se vazio; barra mostra o efeito ativo)
        if self._escurecer_icone is None:
            self._escurecer_icone = pygame.Surface((28, 28), pygame.SRCALPHA)
            self._escurecer_icone.fill((20, 16, 28, 160))
        restantes = {ITEM_VELOCIDADE: (self.velocidade_restante, DURACAO_VELOCIDADE),
                     ITEM_INVISIBILIDADE: (self.invisibilidade_restante, DURACAO_INVISIBILIDADE),
                     ITEM_BUSSOLA: (self.bussola_restante, DURACAO_BUSSOLA)}
        for i, item in enumerate(CATALOGO):
            x = 432 + i * 100
            quantidade = self.inventario.quantidade(item["id"])
            desenhar_icone_item(tela, item["id"], x + 14, y + 12, t)
            if quantidade == 0:
                tela.blit(self._escurecer_icone, (x, y - 2))
            jogo.desenhar_texto(f"{i + 1}:x{quantidade}", jogo.fonte_pequena,
                                COR_TEXTO if quantidade else (130, 120, 140), (x + 32, y + 3))
            if item["id"] == ITEM_ESCUDO and self.escudo_ativo:
                pygame.draw.rect(tela, (120, 180, 255), (x, y + 26, 60, 4))
            elif item["id"] in restantes and restantes[item["id"]][0] > 0:
                restante, total = restantes[item["id"]]
                pygame.draw.rect(tela, COR_SUCESSO, (x, y + 26, int(60 * restante / total), 4))

    def desenhar_interface(self, jogo):
        """Aviso do santuário e a loja, por cima de tudo (o jogo segue rodando por baixo)."""
        tela = jogo.tela
        if self.perto_do_santuario and not self.loja.aberta:
            desenhar_texto_contorno(tela, jogo.fonte, "Pressione E: Santuário do Aventureiro",
                                    COR_OURO, (LARGURA_JANELA // 2, ALTURA_JANELA - 74),
                                    (10, 8, 14), 2)
        if self.loja.aberta:
            self.loja.desenhar(tela, (jogo.fonte_titulo, jogo.fonte, jogo.fonte_pequena),
                               self.saldo, self.inventario, jogo.tempo_animacao)

    def desenhar_estatisticas(self, jogo):
        """Linhas extras da tela de Game Over (o modo é infinito: só termina ao perder)."""
        centro = LARGURA_JANELA // 2
        recordes = self.recordes
        linhas = [
            f"Mapas concluídos: {self.mapas_concluidos}"
            f"   |   Tempo de sobrevivência: {formatar_tempo(self.tempo_sobrevivencia)}",
            f"Moedas coletadas: {self.moedas_coletadas}   |   Capturas sofridas: {self.capturas}",
            f"Recorde: {recordes.melhor_pontuacao} pontos  |  {recordes.mais_mapas} mapas  |  "
            f"{formatar_tempo(recordes.maior_tempo)}",
        ]
        for i, texto in enumerate(linhas):
            jogo.desenhar_texto(texto, jogo.fonte_pequena, COR_TEXTO if i < 2 else (190, 160, 90),
                                (centro, 366 + i * 24), centralizar=True)