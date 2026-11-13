"""
Modo Perseguição - O Guardião das Trevas.

PartidaPerseguicao guarda TODOS os dados de uma partida deste modo (jogador,
Guardião, pontos, ouro, inventário, efeitos e temporizadores). A classe Jogo
(main.py) cria uma partida nova ao entrar no modo e a descarta (None) ao voltar
ao menu ou ao escolher outro modo, então nada vaza para a campanha/infinito.

Reaproveita do projeto: Jogador, Item, Armadilha, Labirinto.caminho_bfs,
SistemaParticulas, Iluminacao, vinheta, fundo do HUD, menus de pausa/fim,
fontes, cores e funções de desenho.
"""

import math
import random
from array import array

import pygame

from constantes import (
    ALTURA_HUD, ALTURA_JANELA, BONUS_SEM_CAPTURA, COR_ALERTA, COR_FUNDO,
    COR_GUARDIAO, COR_OURO, COR_SUCESSO, COR_TEXTO, COR_VIDA,
    DISTANCIA_SANTUARIO, DIST_MIN_GUARDIAO_RESPAWN, DIST_MIN_RESPAWN,
    DURACAO_BUSSOLA, DURACAO_ESCONDERIJO, DURACAO_INVISIBILIDADE,
    DURACAO_LENTIDAO, DURACAO_VELOCIDADE, ESTAGIO_CACADA, ESTAGIO_FURIA,
    ESTADO_GAME_OVER, ESTADO_JOGANDO, ESTADO_PAUSADO, ESTADO_VITORIA,
    FATOR_LENTIDAO, FATOR_POCAO_VELOCIDADE, INTENSIDADE_TREMOR,
    INTERVALO_BATIMENTO_ALERTA, INTERVALO_BATIMENTO_PERIGO, INTERVALO_BUSSOLA,
    INTERVALO_POEIRA, INTERVALO_PROXIMIDADE, LARGURA_JANELA, LIMITE_BFS_TOTAL,
    MAX_VIDAS_PERSEGUICAO, NOME_MODO_PERSEGUICAO, OURO_MOEDA, OURO_TESOURO,
    PAREDE, PASSAGEM_SECRETA, PONTOS_FUGA, PROXIMIDADE_ALERTA,
    PROXIMIDADE_PERIGO, RECARGA_ESCONDERIJO, SAIDA, TAMANHO_TILE,
    TEMPO_ANIMACAO_CAPTURA, TEMPO_ATORDOADO_ARMADILHA, TEMPO_ATORDOADO_ESCUDO,
    TEMPO_DESPERTAR_APOS_CAPTURA, TEMPO_FADE, TEMPO_FLASH_DANO,
    TEMPO_INVULNERAVEL, TEMPO_MENSAGEM, TEMPO_TITULO_FASE, TEMPO_TREMOR,
    TIPO_CHAVE, TIPO_MOEDA, TIPO_TESOURO, VIDAS_PERSEGUICAO,
)
from desenho import (
    desenhar_coracao, desenhar_icone_chave, desenhar_icone_moeda,
    desenhar_icone_relogio, desenhar_jogador,
)
from desenho_perseguicao import (
    cor_proximidade, desenhar_aura_escudo, desenhar_esconderijo,
    desenhar_icone_item, desenhar_olho_proximidade, desenhar_olhos_guardiao,
    desenhar_santuario, desenhar_seta_bussola,
)
from efeitos import criar_vinheta
from entidades import Jogador, Labirinto
from gerador import _distancias
from guardiao import Guardiao
from interface import desenhar_texto_contorno
from loja import CATALOGO, ITENS_POR_ID, Inventario, Loja, comprar
from mapa_perseguicao import LabirintoPerseguicao, gerar_mapa_perseguicao

# Teclas de uso dos itens (1 a 5, também no teclado numérico)
TECLAS_ITENS = {
    pygame.K_1: "cura", pygame.K_KP1: "cura",
    pygame.K_2: "velocidade", pygame.K_KP2: "velocidade",
    pygame.K_3: "escudo", pygame.K_KP3: "escudo",
    pygame.K_4: "invisibilidade", pygame.K_KP4: "invisibilidade",
    pygame.K_5: "bussola", pygame.K_KP5: "bussola",
}
COR_INVISIVEL = (170, 120, 240)
COR_ESCUDO = (120, 170, 255)


# ----------------------------------------------------------------------
# Sons sintetizados (opcionais: sem placa de som, o jogo segue em silêncio)
# ----------------------------------------------------------------------
_SONS = {}


def _sintetizar(nome):
    """Cria o som na hora (sem arquivos). Retorna None se o áudio não estiver disponível."""
    info = pygame.mixer.get_init()
    if not info or info[1] != -16:
        return None
    frequencia, _, canais = info
    amostras = array("h")

    def tom(duracao, freq, volume, ruido=0.0, deslize=0.0):
        total = int(frequencia * duracao)
        fase = 0.0
        for i in range(total):
            progresso = i / total
            envelope = min(1.0, progresso * 25) * (1 - progresso) ** 2
            fase += 2 * math.pi * (freq + deslize * progresso) / frequencia
            valor = math.sin(fase) + 0.35 * math.sin(fase * 2)
            if ruido:
                valor = valor * (1 - ruido) + random.uniform(-1, 1) * ruido
            amostra = int(max(-1.0, min(1.0, valor * volume * envelope)) * 32000)
            amostras.extend([amostra] * canais)

    def silencio(duracao):
        amostras.extend([0] * int(frequencia * duracao) * canais)

    if nome == "batimento":            # "tum-tum" grave de coração
        tom(0.10, 58, 0.9)
        silencio(0.09)
        tom(0.09, 52, 0.6)
    elif nome == "rugido":             # rosnado quando o Guardião te encontra
        tom(0.75, 75, 0.7, ruido=0.45, deslize=-35)
    elif nome == "compra":
        tom(0.07, 880, 0.35)
        tom(0.10, 1320, 0.30)
    else:
        return None
    return pygame.mixer.Sound(buffer=amostras.tobytes())


def tocar_som(nome, volume=0.6):
    try:
        if nome not in _SONS:
            _SONS[nome] = _sintetizar(nome)
        som = _SONS[nome]
        if som is not None:
            som.set_volume(volume)
            som.play()
    except (pygame.error, ValueError, TypeError):
        _SONS[nome] = None


# ----------------------------------------------------------------------
class PartidaPerseguicao:
    """Uma partida completa do modo Perseguição."""

    def __init__(self, jogo, semente=None):
        self.jogo = jogo
        self.nivel = gerar_mapa_perseguicao(semente)
        self.labirinto = LabirintoPerseguicao(self.nivel["mapa"])
        self.itens = list(self.labirinto.itens)
        self.armadilhas = self.labirinto.armadilhas
        # Dados da partida (isolados dos outros modos)
        self.jogador = Jogador()
        self.jogador.vidas = VIDAS_PERSEGUICAO
        self.jogador.posicionar(self.labirinto.posicao_inicial)
        self.tile_jogador = Labirinto.tile_do_ponto(self.jogador.retangulo.center)
        self.guardiao = Guardiao(*self.labirinto.guardiao_inicial)
        self.inventario = Inventario()
        self.loja = Loja()
        self.pontos = 0
        self.pontos_exibidos = 0.0
        self.ouro = 0                      # saldo da loja (separado da pontuação)
        self.ouro_ganho = 0
        self.moedas_coletadas = 0
        self.tesouros_coletados = 0
        self.capturas = 0
        self.bloqueios_escudo = 0
        self.tem_chave = False
        self.bonus = []                    # (descrição, pontos) mostrados na vitória
        self.novo_recorde = False
        # Temporizadores (todos em segundos, descontados com dt)
        self.tempo_partida = 0.0
        self.tempo_animacao = 0.0
        self.efeito_velocidade = 0.0
        self.efeito_invisivel = 0.0
        self.efeito_bussola = 0.0
        self.lentidao = 0.0
        self.escondido = 0.0
        self.esconderijo_atual = None
        self.recargas = {pos: 0.0 for pos in self.labirinto.esconderijos}
        self.animacao_captura = 0.0
        self.tremor = 0.0
        self.flash = 0.0
        self.cor_flash = COR_VIDA
        self.mensagem = ""
        self.tempo_mensagem = 0.0
        self.tempo_titulo = TEMPO_TITULO_FASE + 0.8
        self.tempo_fade = TEMPO_FADE
        self.tempo_poeira = 0.0
        # Proximidade do Guardião e bússola
        self.distancia_guardiao = None
        self.proximidade = 0.0             # alvo (0 tranquilo ... 1 colado)
        self.proximidade_exibida = 0.0     # valor suavizado mostrado no HUD
        self.tempo_proximidade = 0.0
        self.tempo_batimento = 0.0
        self.angulo_bussola = None
        self.trilha_bussola = []
        self.tempo_calculo_bussola = 0.0
        self.frente_porta = self._tiles_frente_porta()
        self.vinheta_perigo = self._criar_vinheta_perigo()
        self.superficie_fantasma = pygame.Surface((64, 64), pygame.SRCALPHA)

        jogo.particulas.limpar()
        jogo.estado = ESTADO_JOGANDO
        jogo.tempo_fim = 0.0
        self.mostrar_mensagem("Silêncio... o Guardião das Trevas está despertando!")
        print(f"Perseguição: {self.nivel['nome']} (semente {self.nivel['semente']})")

    # ------------------------------------------------------------------
    # auxiliares
    # ------------------------------------------------------------------
    @staticmethod
    def _criar_vinheta_perigo():
        vinheta = criar_vinheta()
        vinheta.fill((170, 0, 30, 0), special_flags=pygame.BLEND_RGBA_ADD)
        return vinheta

    @staticmethod
    def centro_do_tile(tile):
        coluna, linha = tile
        return (coluna * TAMANHO_TILE + TAMANHO_TILE // 2,
                ALTURA_HUD + linha * TAMANHO_TILE + TAMANHO_TILE // 2)

    @property
    def detectavel(self):
        """O Guardião só detecta quem não está invisível nem escondido."""
        return self.efeito_invisivel <= 0 and self.escondido <= 0

    def mostrar_mensagem(self, texto):
        self.mensagem = texto
        self.tempo_mensagem = TEMPO_MENSAGEM

    def _tiles_frente_porta(self):
        porta = Labirinto.tile_do_ponto(self.labirinto.porta.center)
        return [(porta[0] + dc, porta[1] + dl) for dc, dl in ((1, 0), (-1, 0), (0, 1), (0, -1))
                if self.labirinto.tile_livre(porta[0] + dc, porta[1] + dl)]

    def _mapa_distancias(self, tile):
        """
        Distância (em passos) de 'tile' até cada tile por onde o Guardião anda.
        Reaproveita a busca em largura do gerador (_distancias), tratando
        porta e passagens secretas como paredes.
        """
        grade = [linha.replace(PASSAGEM_SECRETA, PAREDE).replace(SAIDA, PAREDE)
                 for linha in self.labirinto.desenho]
        distancias = _distancias(grade, (tile[1], tile[0]))
        return {(coluna, linha): d for (linha, coluna), d in distancias.items()}

    def _tile_seguro(self, coluna, linha):
        """Tile onde alguém pode reaparecer: livre, sem armadilha, sem esconderijo."""
        return self.labirinto.tile_livre(coluna, linha) \
            and not self.labirinto.eh_perigoso(coluna, linha) \
            and (coluna, linha) not in self.recargas

    # ------------------------------------------------------------------
    # atualização
    # ------------------------------------------------------------------
    def atualizar(self, dt, dt_real):
        jogo = self.jogo
        self._atualizar_visuais(dt, dt_real)
        if jogo.estado != ESTADO_JOGANDO:          # telas finais: só a animação continua
            jogo.tempo_fim += dt_real
            return
        if self.animacao_captura > 0:
            self._animar_captura(dt_real)
            return
        self.tempo_partida += dt_real
        self._atualizar_efeitos(dt)

        # Jogador (parado enquanto escolhe na loja; o resto do jogo continua)
        if self.loja.aberta:
            self.jogador.invulneravel_restante = max(0.0, self.jogador.invulneravel_restante - dt)
            self.jogador.andando = False
        else:
            self.jogador.fator_velocidade = self.fator_velocidade_jogador()
            self.jogador.atualizar(dt, self.labirinto)
            self._soltar_poeira(dt)
        tile = Labirinto.tile_do_ponto(self.jogador.retangulo.center)
        if self.labirinto.tile_livre(*tile):
            self.tile_jogador = tile
        self.coletar_itens()
        self._verificar_esconderijos(tile, dt)
        if self.verificar_saida():
            return
        for armadilha in self.armadilhas:
            armadilha.atualizar(dt)
        self._verificar_armadilhas()

        # Guardião: continua ativo SEMPRE (inclusive com a loja aberta)
        self.guardiao.atualizar_perseguicao(dt, self.labirinto, self.jogador, self.tempo_partida,
                                            self.tile_jogador, self.detectavel)
        self._tratar_eventos_guardiao()
        self._atualizar_proximidade(dt)
        self._atualizar_bussola(dt)
        self.verificar_captura()

    def _atualizar_visuais(self, dt, dt_real):
        jogo = self.jogo
        self.tempo_animacao += dt
        jogo.particulas.atualizar(dt)
        self.labirinto.atualizar(dt)
        self.loja.atualizar(dt_real)
        self.tremor = max(0.0, self.tremor - dt_real)
        self.flash = max(0.0, self.flash - dt_real)
        self.tempo_mensagem = max(0.0, self.tempo_mensagem - dt_real)
        self.tempo_titulo = max(0.0, self.tempo_titulo - dt_real)
        self.tempo_fade = max(0.0, self.tempo_fade - dt_real)
        self.proximidade_exibida += (self.proximidade - self.proximidade_exibida) * min(1.0, dt * 5)
        diferenca = self.pontos - self.pontos_exibidos
        if diferenca > 0:
            self.pontos_exibidos += min(diferenca, max(60 * dt_real, diferenca * 8 * dt_real))
        for x, y in self.labirinto.tochas:
            if random.random() < dt * 2.5:
                jogo.particulas.brasa(x, y - 8)

    def _atualizar_efeitos(self, dt):
        """Efeitos temporários controlados por tempo real (dt), não por quadros."""
        avisos = []
        for nome, texto in (("efeito_velocidade", "A Poção da Velocidade acabou."),
                            ("efeito_invisivel", "Você está visível de novo!"),
                            ("efeito_bussola", "A Bússola Mágica parou de girar."),
                            ("lentidao", None)):
            valor = getattr(self, nome)
            if valor > 0:
                valor = max(0.0, valor - dt)
                setattr(self, nome, valor)
                if valor == 0 and texto:
                    avisos.append(texto)
        for posicao, restante in self.recargas.items():
            if restante > 0 and not (posicao == self.esconderijo_atual and self.escondido > 0):
                self.recargas[posicao] = max(0.0, restante - dt)
        if self.efeito_bussola <= 0:
            self.angulo_bussola = None
            self.trilha_bussola = []
        if avisos:
            self.mostrar_mensagem(avisos[-1])

    def fator_velocidade_jogador(self):
        fator = 1.0
        if self.efeito_velocidade > 0:
            fator *= FATOR_POCAO_VELOCIDADE
        if self.lentidao > 0:
            fator *= FATOR_LENTIDAO
        return fator

    def _soltar_poeira(self, dt):
        if not self.jogador.andando:
            return
        self.tempo_poeira -= dt
        if self.tempo_poeira <= 0:
            retangulo = self.jogador.retangulo
            self.jogo.particulas.poeira(retangulo.centerx, retangulo.bottom - 2)
            self.tempo_poeira = INTERVALO_POEIRA / (1.6 if self.efeito_velocidade > 0 else 1)

    # ------------------------------------------------------------------
    # itens, chave e saída
    # ------------------------------------------------------------------
    def coletar_itens(self):
        particulas = self.jogo.particulas
        for item in self.itens[:]:
            if not self.jogador.retangulo.colliderect(item.retangulo):
                continue
            self.itens.remove(item)
            x, y = item.retangulo.center
            self.pontos += item.pontos
            if item.tipo == TIPO_CHAVE:
                self.tem_chave = True
                self.labirinto.abrir_porta()
                particulas.explosao(x, y, [COR_OURO, (255, 245, 170)], 22, 140, 0.8)
                particulas.texto(x, y - 10, "CHAVE!", COR_OURO)
                self.mostrar_mensagem("Chave encontrada! A porta de saída foi destrancada.")
                continue
            ouro = OURO_MOEDA if item.tipo == TIPO_MOEDA else OURO_TESOURO
            self.ouro += ouro                       # saldo atualizado na hora
            self.ouro_ganho += ouro
            if item.tipo == TIPO_MOEDA:
                self.moedas_coletadas += 1
            elif item.tipo == TIPO_TESOURO:
                self.tesouros_coletados += 1
            particulas.explosao(x, y, [COR_OURO, (255, 240, 150), (200, 150, 30)],
                                10 if item.tipo == TIPO_MOEDA else 20)
            particulas.texto(x, y - 10, f"+{item.pontos}", COR_OURO)

    def verificar_saida(self):
        """True se o jogador escapou (vitória)."""
        if not self.jogador.retangulo.inflate(4, 4).colliderect(self.labirinto.porta):
            return False
        if not self.labirinto.porta_aberta:
            aviso = "A porta está trancada! Encontre a chave primeiro."
            if self.mensagem != aviso or self.tempo_mensagem <= 0.5:
                self.mostrar_mensagem(aviso)
            return False
        self._vencer()
        return True

    def _vencer(self):
        self.bonus = [("Fuga da masmorra", PONTOS_FUGA)]
        if self.capturas == 0:
            self.bonus.append(("Fuga sem captura", BONUS_SEM_CAPTURA))
        self.pontos += sum(p for _, p in self.bonus)
        x, y = self.labirinto.porta.center
        self.jogo.particulas.explosao(x, y, [COR_SUCESSO, (200, 255, 200), COR_OURO], 30, 150, 0.9)
        self._finalizar(ESTADO_VITORIA)

    def _finalizar(self, estado):
        jogo = self.jogo
        self.loja.fechar()
        self.novo_recorde = self.pontos > jogo.recorde_perseguicao
        jogo.recorde_perseguicao = max(jogo.recorde_perseguicao, self.pontos)
        jogo.estado = estado
        jogo.tempo_fim = 0.0

    # ------------------------------------------------------------------
    # elementos especiais
    # ------------------------------------------------------------------
    def _verificar_esconderijos(self, tile, dt):
        posicao = tile if tile in self.recargas else None
        if posicao != self.esconderijo_atual:
            anterior = self.esconderijo_atual
            if anterior is not None and self.escondido > 0:
                self.escondido = 0.0
                self.recargas[anterior] = RECARGA_ESCONDERIJO
                self.mostrar_mensagem("Você saiu do esconderijo.")
            self.esconderijo_atual = posicao
            if posicao is not None:
                if self.recargas[posicao] <= 0:
                    self.escondido = DURACAO_ESCONDERIJO
                    x, y = self.centro_do_tile(posicao)
                    self.jogo.particulas.explosao(x, y, [(120, 78, 40), (90, 70, 50)], 10, 70)
                    self.mostrar_mensagem(f"Escondido! O Guardião perde seu rastro "
                                          f"({DURACAO_ESCONDERIJO:g} s).")
                else:
                    self.mostrar_mensagem("Este esconderijo ainda não é seguro.")
        elif posicao is not None and self.escondido > 0:
            self.escondido = max(0.0, self.escondido - dt)
            if self.escondido == 0:
                self.recargas[posicao] = RECARGA_ESCONDERIJO
                self.mostrar_mensagem("O esconderijo deixou de ser seguro. Corra!")

    def _verificar_armadilhas(self):
        """Espinhos: deixam o jogador lento e atrasam (atordoam) o Guardião."""
        particulas = self.jogo.particulas
        for armadilha in self.armadilhas:
            if armadilha.estado != "ativa":
                continue
            area = armadilha.area_dano
            if self.lentidao <= 0 and not self.jogador.invulneravel and self.escondido <= 0 \
                    and area.colliderect(self.jogador.hitbox):
                self.lentidao = DURACAO_LENTIDAO
                self.tremor = TEMPO_TREMOR * 0.6
                self.flash, self.cor_flash = TEMPO_FLASH_DANO * 0.6, COR_VIDA
                x, y = self.jogador.retangulo.center
                particulas.explosao(x, y, [COR_VIDA, (255, 130, 130)], 12, 110)
                self.mostrar_mensagem("Espinhos! Você ficou mais lento por alguns segundos.")
            if area.colliderect(self.guardiao.hitbox) and \
                    self.guardiao.pisou_em_armadilha(TEMPO_ATORDOADO_ARMADILHA):
                x, y = self.guardiao.retangulo.center
                particulas.explosao(x, y, [COR_GUARDIAO, (200, 200, 220)], 14, 120)
                particulas.texto(x, y - 24, "ATRASADO!", COR_SUCESSO)

    def santuario_proximo(self):
        """Santuário ao alcance do jogador (ou None)."""
        cx, cy = self.jogador.retangulo.center
        for tile in self.labirinto.santuarios:
            sx, sy = self.centro_do_tile(tile)
            if math.hypot(sx - cx, sy - cy) <= DISTANCIA_SANTUARIO:
                return tile
        return None

    # ------------------------------------------------------------------
    # Guardião: eventos, proximidade, captura
    # ------------------------------------------------------------------
    def _tratar_eventos_guardiao(self):
        x, y = self.guardiao.retangulo.center
        particulas = self.jogo.particulas
        for evento in self.guardiao.eventos:
            if evento == "despertou":
                particulas.explosao(x, y, [COR_GUARDIAO, (40, 20, 60)], 18, 90)
                if self.tempo_partida < 10:
                    self.mostrar_mensagem("O Guardião das Trevas despertou e está te procurando...")
            elif evento == "detectou":
                particulas.texto(x, y - 30, "GRRRR!", COR_ALERTA)
                self.mostrar_mensagem("CAÇADA! O Guardião te encontrou. Fuja!")
                tocar_som("rugido", 0.5)
            elif evento == "perdeu":
                particulas.texto(x, y - 30, "?", (200, 180, 255))
                self.mostrar_mensagem("O Guardião perdeu seu rastro... por enquanto.")
            elif evento == "furia":
                particulas.explosao(x, y, [(255, 80, 30), (255, 190, 60)], 30, 160, 0.9)
                self.tremor = TEMPO_TREMOR
                self.mostrar_mensagem("FÚRIA! O Guardião está muito mais rápido!")
                tocar_som("rugido", 0.8)

    def _atualizar_proximidade(self, dt):
        """Distância REAL pelos corredores (BFS existente), em intervalos controlados."""
        self.tempo_proximidade -= dt
        if self.tempo_proximidade <= 0:
            self.tempo_proximidade = INTERVALO_PROXIMIDADE
            caminho = self.labirinto.caminho_bfs(self.guardiao.tile, self.tile_jogador,
                                                 PROXIMIDADE_ALERTA)
            self.distancia_guardiao = None if caminho is None else len(caminho)
            if self.distancia_guardiao is None:
                self.proximidade = 0.0
            else:
                self.proximidade = max(0.0, min(1.0, (PROXIMIDADE_ALERTA - self.distancia_guardiao)
                                                / (PROXIMIDADE_ALERTA - 1)))
        # batimento cardíaco cada vez mais rápido
        distancia = self.distancia_guardiao
        if distancia is not None and distancia < PROXIMIDADE_ALERTA and self.guardiao.dormindo <= 0:
            self.tempo_batimento -= dt
            if self.tempo_batimento <= 0:
                perigo = distancia < PROXIMIDADE_PERIGO
                self.tempo_batimento = INTERVALO_BATIMENTO_PERIGO if perigo \
                    else INTERVALO_BATIMENTO_ALERTA
                tocar_som("batimento", 0.9 if perigo else 0.5)
        else:
            self.tempo_batimento = 0.0

    @property
    def rotulo_proximidade(self):
        d = self.distancia_guardiao
        if d is None or d >= PROXIMIDADE_ALERTA:
            return "Tranquilo"
        if d >= PROXIMIDADE_PERIGO:
            return "Alerta"
        return "PERIGO!"

    def verificar_captura(self):
        guardiao, jogador = self.guardiao, self.jogador
        if not guardiao.ativo or jogador.invulneravel or self.escondido > 0:
            return
        if not guardiao.hitbox.colliderect(jogador.hitbox):
            return
        x, y = jogador.retangulo.center
        particulas = self.jogo.particulas
        if self.inventario.consumir("escudo"):
            # O escudo bloqueia esta captura e é consumido (proteção NÃO permanente)
            self.bloqueios_escudo += 1
            jogador.invulneravel_restante = TEMPO_INVULNERAVEL
            self._repelir_guardiao()
            self.flash, self.cor_flash = TEMPO_FLASH_DANO, COR_ESCUDO
            particulas.explosao(x, y, [COR_ESCUDO, (220, 235, 255), COR_OURO], 26, 160, 0.7)
            particulas.texto(x, y - 18, "BLOQUEADO!", COR_ESCUDO)
            self.mostrar_mensagem("O Escudo Mágico bloqueou a captura e se desfez!")
            return
        # Captura: perde uma vida (já ativa a invulnerabilidade existente) e anima
        self.capturas += 1
        self.loja.fechar()
        jogador.perder_vida()
        jogador.andando = False
        self.animacao_captura = TEMPO_ANIMACAO_CAPTURA
        self.tremor = TEMPO_TREMOR
        self.flash, self.cor_flash = TEMPO_FLASH_DANO * 1.5, (90, 20, 140)
        particulas.explosao(x, y, [(40, 10, 60), COR_GUARDIAO, (10, 5, 15)], 34, 150, 0.9)
        self.mostrar_mensagem("Capturado pelo Guardião! Você perdeu uma vida.")
        tocar_som("rugido", 0.9)

    def _repelir_guardiao(self):
        """O escudo empurra o Guardião alguns tiles para trás e o deixa atordoado."""
        guardiao = self.guardiao
        distancias = self._mapa_distancias(self.tile_jogador)
        opcoes = [t for t, d in distancias.items() if 3 <= d <= 5 and self._tile_seguro(*t)]
        if opcoes:
            gx, gy = guardiao.tile
            destino = min(opcoes, key=lambda t: abs(t[0] - gx) + abs(t[1] - gy))
            x, y = guardiao.retangulo.center
            self.jogo.particulas.explosao(x, y, [COR_ESCUDO, COR_GUARDIAO], 16, 120)
            guardiao.teleportar(*destino)
        guardiao.atordoar(TEMPO_ATORDOADO_ESCUDO)

    def _animar_captura(self, dt_real):
        self.animacao_captura -= dt_real
        if random.random() < 0.6:
            x, y = self.jogador.retangulo.center
            self.jogo.particulas.explosao(x, y, [(30, 10, 45), COR_GUARDIAO], 2, 60, 0.5)
        if self.animacao_captura > 0:
            return
        self.animacao_captura = 0.0
        if self.jogador.vidas <= 0:
            self._finalizar(ESTADO_GAME_OVER)
        else:
            self.reposicionar_apos_captura()

    def reposicionar_apos_captura(self):
        """Jogador num ponto seguro longe do Guardião; Guardião numa região distante."""
        dist_guardiao = self._mapa_distancias(self.guardiao.tile)
        seguros = [t for t in dist_guardiao if self._tile_seguro(*t)]
        inicio = Labirinto.tile_do_ponto(
            (self.labirinto.posicao_inicial[0] + 1, self.labirinto.posicao_inicial[1] + 1))
        if dist_guardiao.get(inicio, 0) >= DIST_MIN_RESPAWN:
            destino_jogador = inicio
        else:
            candidatos = [t for t in seguros if dist_guardiao[t] >= DIST_MIN_RESPAWN]
            if not candidatos:
                candidatos = sorted(seguros, key=lambda t: -dist_guardiao[t])[:5]
            candidatos.sort(key=lambda t: -dist_guardiao[t])
            destino_jogador = random.choice(candidatos[:max(1, len(candidatos) // 3)])
        coluna, linha = destino_jogador
        self.jogador.posicionar((coluna * TAMANHO_TILE, ALTURA_HUD + linha * TAMANHO_TILE))
        self.tile_jogador = destino_jogador

        dist_jogador = self._mapa_distancias(destino_jogador)
        candidatos = [t for t in dist_jogador if self._tile_seguro(*t)
                      and dist_jogador[t] >= DIST_MIN_GUARDIAO_RESPAWN]
        if not candidatos:
            candidatos = sorted((t for t in dist_jogador if self._tile_seguro(*t)),
                                key=lambda t: -dist_jogador[t])[:5]
        candidatos.sort(key=lambda t: -dist_jogador[t])
        destino_guardiao = random.choice(candidatos[:max(1, len(candidatos) // 2)])
        self.guardiao.teleportar(*destino_guardiao, tempo_dormir=TEMPO_DESPERTAR_APOS_CAPTURA)
        self.distancia_guardiao = None
        self.tempo_proximidade = 0.0
        x, y = self.jogador.retangulo.center
        self.jogo.particulas.explosao(x, y, [(200, 200, 255), COR_TEXTO], 16, 100)
        self.mostrar_mensagem(f"Você escapou das garras! Restam {self.jogador.vidas} vida(s).")

    # ------------------------------------------------------------------
    # bússola
    # ------------------------------------------------------------------
    def alvo_bussola(self):
        """Tile da chave (se ainda não foi pega) ou da frente da porta."""
        for item in self.itens:
            if item.tipo == TIPO_CHAVE:
                return Labirinto.tile_do_ponto(item.retangulo.center)
        return self.frente_porta[0] if self.frente_porta else None

    def _atualizar_bussola(self, dt):
        if self.efeito_bussola <= 0:
            return
        self.tempo_calculo_bussola -= dt
        if self.tempo_calculo_bussola > 0:
            return
        self.tempo_calculo_bussola = INTERVALO_BUSSOLA
        alvo = self.alvo_bussola()
        if alvo is None:
            return
        caminho = self.labirinto.caminho_bfs(self.tile_jogador, alvo, LIMITE_BFS_TOTAL)
        if caminho:
            self.trilha_bussola = caminho[:6]
            referencia = self.centro_do_tile(caminho[min(2, len(caminho) - 1)])
        else:
            self.trilha_bussola = []
            referencia = self.centro_do_tile(alvo)
        cx, cy = self.jogador.retangulo.center
        if (referencia[0], referencia[1]) != (cx, cy):
            self.angulo_bussola = math.atan2(referencia[1] - cy, referencia[0] - cx)

    # ------------------------------------------------------------------
    # inventário e loja
    # ------------------------------------------------------------------
    def usar_item(self, identificador):
        """Usa um item do inventário. Retorna True se ele foi consumido."""
        nome = ITENS_POR_ID[identificador]["nome"]
        if self.inventario.quantidade(identificador) <= 0:
            self.mostrar_mensagem(f"Você não tem {nome}. Compre no Santuário.")
            return False
        x, y = self.jogador.retangulo.center
        particulas = self.jogo.particulas
        if identificador == "cura":
            if self.jogador.vidas >= MAX_VIDAS_PERSEGUICAO:
                self.mostrar_mensagem("Suas vidas já estão no máximo.")
                return False
            self.inventario.consumir("cura")
            self.jogador.vidas += 1
            particulas.explosao(x, y, [COR_VIDA, (255, 160, 170)], 18, 100)
            particulas.texto(x, y - 18, "+1 VIDA", COR_VIDA)
            self.mostrar_mensagem("Poção de Cura: você recuperou uma vida.")
        elif identificador == "escudo":
            self.mostrar_mensagem(f"O Escudo Mágico protege sozinho na próxima captura "
                                  f"(você tem {self.inventario.quantidade('escudo')}).")
            return False
        else:
            atributo, duracao, cor, texto = {
                "velocidade": ("efeito_velocidade", DURACAO_VELOCIDADE, (230, 200, 40),
                               "Poção da Velocidade! Corra!"),
                "invisibilidade": ("efeito_invisivel", DURACAO_INVISIBILIDADE, COR_INVISIVEL,
                                   "Invisível! O Guardião não consegue te detectar."),
                "bussola": ("efeito_bussola", DURACAO_BUSSOLA, COR_OURO,
                            "A Bússola Mágica aponta o caminho."),
            }[identificador]
            if getattr(self, atributo) > 0:
                self.mostrar_mensagem(f"{nome} ainda está fazendo efeito.")
                return False
            self.inventario.consumir(identificador)
            setattr(self, atributo, duracao)
            if identificador == "bussola":
                self.tempo_calculo_bussola = 0.0
                self._atualizar_bussola(0.0)
            particulas.explosao(x, y, [cor, (255, 255, 255)], 16, 100)
            self.mostrar_mensagem(texto)
        return True

    def comprar_selecionado(self):
        acao = self.loja.acao_selecionada()
        if acao == "fechar":
            self.loja.fechar()
            return
        self.ouro, sucesso, mensagem = comprar(acao, self.ouro, self.inventario)
        self.loja.avisar(mensagem, sucesso)
        if sucesso:
            tocar_som("compra", 0.4)
            x, y = self.jogador.retangulo.center
            self.jogo.particulas.explosao(x, y, [COR_OURO, (255, 250, 200)], 14, 90)

    def alternar_loja(self):
        if self.loja.aberta:
            self.loja.fechar()
            return
        if self.escondido > 0:
            return
        if self.santuario_proximo() is None:
            self.mostrar_mensagem("Encontre um Santuário (altar com cristal) para abrir a loja.")
            return
        self.loja.abrir()

    # ------------------------------------------------------------------
    # entrada (teclado e mouse)
    # ------------------------------------------------------------------
    def tratar_tecla(self, tecla):
        """Teclas do modo durante o jogo. Retorna True se a tecla foi usada aqui."""
        if self.animacao_captura > 0:
            return tecla not in (pygame.K_ESCAPE, pygame.K_p)
        if tecla in TECLAS_ITENS:
            self.usar_item(TECLAS_ITENS[tecla])
            return True
        if tecla == pygame.K_e:
            self.alternar_loja()
            return True
        if tecla == pygame.K_l:
            self.jogo.luz_ativada = not self.jogo.luz_ativada
            self.mostrar_mensagem("Iluminação ligada" if self.jogo.luz_ativada
                                  else "Iluminação desligada")
            return True
        if not self.loja.aberta:
            return False
        if tecla in (pygame.K_UP, pygame.K_w):
            self.loja.mover(-1)
        elif tecla in (pygame.K_DOWN, pygame.K_s):
            self.loja.mover(1)
        elif tecla in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            self.comprar_selecionado()
        elif tecla == pygame.K_ESCAPE:
            self.loja.fechar()
        else:
            return False
        return True

    def mover_mouse(self, posicao):
        if self.loja.aberta:
            indice = self.loja.opcao_no_ponto(posicao)
            if indice is not None:
                self.loja.selecionado = indice

    def clicar(self, posicao):
        if not self.loja.aberta:
            return
        indice = self.loja.opcao_no_ponto(posicao)
        if indice is not None:
            self.loja.selecionado = indice
            self.comprar_selecionado()

    # ------------------------------------------------------------------
    # desenho
    # ------------------------------------------------------------------
    def desenhar(self):
        jogo = self.jogo
        cena, tela, t = jogo.cena, jogo.tela, self.tempo_animacao
        self.labirinto.desenhar(cena, t)
        perto = self.santuario_proximo()
        for tile in self.labirinto.santuarios:
            x, y = tile[0] * TAMANHO_TILE, ALTURA_HUD + tile[1] * TAMANHO_TILE
            desenhar_santuario(cena, x, y, t, tile == perto)
        for tile, recarga in self.recargas.items():
            x, y = tile[0] * TAMANHO_TILE, ALTURA_HUD + tile[1] * TAMANHO_TILE
            ocupado = tile == self.esconderijo_atual and self.escondido > 0
            desenhar_esconderijo(cena, x, y, t, recarga <= 0 or ocupado, ocupado,
                                 recarga / RECARGA_ESCONDERIJO)
        for armadilha in self.armadilhas:
            armadilha.desenhar(cena)
        for item in self.itens:
            item.desenhar(cena, t)
        for i, tile in enumerate(self.trilha_bussola):
            raio = 3 + int(abs(math.sin(t * 5 - i * 0.6)) * 2)
            pygame.draw.circle(cena, COR_OURO, self.centro_do_tile(tile), raio)
        self.guardiao.desenhar(cena)
        self._desenhar_jogador(cena)
        if self.animacao_captura > 0:
            self._desenhar_garras(cena)
        jogo.particulas.desenhar(cena, jogo.fonte_pequena)
        if jogo.luz_ativada:
            luzes = self.labirinto.tochas + [self.centro_do_tile(s) for s in self.labirinto.santuarios]
            jogo.iluminacao.desenhar(cena, self.jogador.retangulo.center, luzes, t,
                                     self.nivel["escuridao"])
            # No breu, só os olhos do Guardião aparecem
            desenhar_olhos_guardiao(cena, self.guardiao.retangulo, self.guardiao.tempo_animacao,
                                    self.guardiao.estagio, self.guardiao.dormindo > 0)
        if self.angulo_bussola is not None and self.efeito_bussola > 0:
            desenhar_seta_bussola(cena, self.jogador.retangulo.center, self.angulo_bussola, t)
        cena.blit(jogo.vinheta, (0, 0))
        if self.proximidade_exibida > 0.55 and jogo.estado == ESTADO_JOGANDO:
            intensidade = (self.proximidade_exibida - 0.55) / 0.45
            pulso = 0.6 + 0.4 * abs(math.sin(t * (4 + 6 * intensidade)))
            self.vinheta_perigo.set_alpha(int(255 * intensidade * pulso))
            cena.blit(self.vinheta_perigo, (0, 0))

        tela.fill(COR_FUNDO)
        tela.blit(cena, self._deslocamento_tremor())
        if perto is not None and not self.loja.aberta and jogo.estado == ESTADO_JOGANDO:
            sx, sy = self.centro_do_tile(perto)
            desenhar_texto_contorno(tela, jogo.fonte_pequena, "E: abrir o Santuário", COR_OURO,
                                    (sx, sy - 34), (10, 8, 14), 2)
        self._desenhar_hud()
        self._desenhar_barra_inferior()
        if self.flash > 0:
            alfa = int(130 * self.flash / TEMPO_FLASH_DANO)
            jogo.veu.fill((*self.cor_flash, min(200, alfa)))
            tela.blit(jogo.veu, (0, 0))
        if jogo.estado == ESTADO_JOGANDO:
            if self.animacao_captura > 0:
                self._desenhar_texto_captura()
            if self.loja.aberta:
                self.loja.desenhar(tela, (jogo.fonte_titulo, jogo.fonte, jogo.fonte_pequena),
                                   self.ouro, self.inventario)
            if self.tempo_titulo > 0 and not self.loja.aberta:
                self._desenhar_titulo()
            if self.tempo_mensagem > 0:
                self._desenhar_mensagem()
        elif jogo.estado == ESTADO_PAUSADO:
            jogo.desenhar_pausa()
        elif jogo.estado in (ESTADO_VITORIA, ESTADO_GAME_OVER):
            self._desenhar_tela_final()
        if self.tempo_fade > 0:
            jogo.veu.fill((0, 0, 0, int(255 * self.tempo_fade / TEMPO_FADE)))
            tela.blit(jogo.veu, (0, 0))

    def _deslocamento_tremor(self):
        if self.tremor <= 0:
            return (0, 0)
        forca = int(INTENSIDADE_TREMOR * self.tremor / TEMPO_TREMOR)
        return (random.randint(-forca, forca), random.randint(-forca, forca))

    def _desenhar_jogador(self, cena):
        jogador = self.jogador
        if self.escondido > 0:
            return                                  # dentro do barril (os olhos aparecem nele)
        centro = jogador.retangulo.center
        if self.inventario.quantidade("escudo") > 0:
            desenhar_aura_escudo(cena, centro, self.tempo_animacao)
        if self.efeito_invisivel > 0:
            fantasma = self.superficie_fantasma
            fantasma.fill((0, 0, 0, 0))
            local = jogador.retangulo.copy()
            local.center = (32, 32)
            desenhar_jogador(fantasma, local, jogador.direcao, jogador.tempo_animacao,
                             jogador.andando)
            piscar = self.efeito_invisivel < 1.5 and int(self.efeito_invisivel * 8) % 2 == 0
            fantasma.set_alpha(150 if piscar else 75)
            cena.blit(fantasma, (centro[0] - 32, centro[1] - 32))
        else:
            jogador.desenhar(cena)
        if self.efeito_velocidade > 0 and jogador.andando:
            for i in range(3):
                pygame.draw.line(cena, (240, 220, 120),
                                 (centro[0] - 14 + i * 4, centro[1] + 6 + i * 3),
                                 (centro[0] - 22 + i * 4, centro[1] + 6 + i * 3), 1)

    def _desenhar_garras(self, cena):
        """Tentáculos de sombra fechando sobre o jogador durante a captura."""
        progresso = 1 - self.animacao_captura / TEMPO_ANIMACAO_CAPTURA
        cx, cy = self.jogador.retangulo.center
        for i in range(8):
            angulo = i * math.pi / 4 + self.tempo_animacao * 2
            externo = 46
            interno = 46 * (1 - progresso) + 6
            meio = (externo + interno) / 2
            torcao = math.sin(self.tempo_animacao * 9 + i) * 0.4
            pontos = [(cx + math.cos(angulo) * externo, cy + math.sin(angulo) * externo),
                      (cx + math.cos(angulo + torcao) * meio, cy + math.sin(angulo + torcao) * meio),
                      (cx + math.cos(angulo) * interno, cy + math.sin(angulo) * interno)]
            pygame.draw.lines(cena, (30, 8, 45), False, pontos, 4)
            pygame.draw.lines(cena, COR_GUARDIAO, False, pontos, 1)

    # ---------------- interface ----------------
    def _desenhar_hud(self):
        jogo = self.jogo
        tela, t = jogo.tela, self.tempo_animacao
        tela.blit(jogo.fundo_hud, (0, 0))
        jogo.desenhar_texto(NOME_MODO_PERSEGUICAO, jogo.fonte_titulo, COR_TEXTO, (20, 8))
        imagem = jogo.fonte_pequena.render(f"Recorde: {jogo.recorde_perseguicao} pts", True,
                                           (190, 160, 90))
        tela.blit(imagem, imagem.get_rect(topright=(LARGURA_JANELA - 20, 14)))
        y = 44
        # vidas (o coração bate com uma vida só)
        vidas = self.jogador.vidas
        pulso = (math.sin(t * 8) + 1) / 2 if vidas == 1 else 0.0
        for i in range(MAX_VIDAS_PERSEGUICAO):
            desenhar_coracao(tela, 20 + i * 32, y + 1, i < vidas, pulso if i < vidas else 0.0)
        # pontuação e ouro (valores separados)
        jogo.desenhar_texto(f"Pontos {int(self.pontos_exibidos)}", jogo.fonte, COR_TEXTO, (130, y))
        desenhar_icone_moeda(tela, 290, y, t)
        jogo.desenhar_texto(str(self.ouro), jogo.fonte, COR_OURO, (318, y))
        # chave
        desenhar_icone_chave(tela, 385, y, self.tem_chave)
        jogo.desenhar_texto("Chave!" if self.tem_chave else "Sem chave", jogo.fonte_pequena,
                            COR_OURO if self.tem_chave else (150, 140, 130), (414, y + 3))
        # tempo de sobrevivência
        segundos = int(self.tempo_partida)
        desenhar_icone_relogio(tela, 515, y, COR_TEXTO, t)
        jogo.desenhar_texto(f"{segundos // 60}:{segundos % 60:02d}", jogo.fonte, COR_TEXTO,
                            (543, y))
        # estágio do Guardião
        estagio = self.guardiao.estagio
        if self.guardiao.dormindo > 0:
            texto, cor = "dormindo", (150, 140, 190)
        else:
            texto = estagio
            cor = {ESTAGIO_CACADA: COR_ALERTA, ESTAGIO_FURIA: (255, 120, 40)}.get(estagio,
                                                                                  (200, 170, 255))
        jogo.desenhar_texto("Guardião:", jogo.fonte_pequena, COR_TEXTO, (625, y + 3))
        jogo.desenhar_texto(texto, jogo.fonte, cor, (710, y))

    def _desenhar_barra_inferior(self):
        """Inventário (esquerda), efeitos ativos (meio) e proximidade (direita)."""
        jogo = self.jogo
        tela, t = jogo.tela, self.tempo_animacao
        topo = ALTURA_JANELA - 40
        faixa = pygame.Surface((LARGURA_JANELA, 40), pygame.SRCALPHA)
        faixa.fill((14, 10, 20, 205))
        tela.blit(faixa, (0, topo))
        pygame.draw.line(tela, (170, 126, 48), (0, topo), (LARGURA_JANELA, topo), 2)
        # inventário
        for i, item in enumerate(CATALOGO):
            slot = pygame.Rect(10 + i * 46, topo + 3, 40, 34)
            quantidade = self.inventario.quantidade(item["id"])
            ativo = self._efeito_restante(item["id"]) > 0
            pygame.draw.rect(tela, (40, 34, 50) if quantidade else (26, 22, 32), slot,
                             border_radius=6)
            cor_borda = COR_OURO if ativo else ((124, 108, 146) if quantidade else (60, 54, 70))
            pygame.draw.rect(tela, cor_borda, slot, 2, border_radius=6)
            desenhar_icone_item(tela, item["id"], slot.center, t, 0.95)
            if not quantidade and not ativo:
                veu = pygame.Surface(slot.size, pygame.SRCALPHA)
                veu.fill((10, 8, 14, 150))
                tela.blit(veu, slot.topleft)
            tela.blit(jogo.fonte_pequena.render(item["tecla"], True, COR_OURO),
                      (slot.x + 3, slot.y - 2))
            qtd = jogo.fonte_pequena.render(str(quantidade), True, COR_TEXTO)
            tela.blit(qtd, qtd.get_rect(bottomright=(slot.right - 3, slot.bottom + 2)))
        # efeitos ativos
        efeitos = []
        if self.efeito_velocidade > 0:
            efeitos.append((f"Veloz {math.ceil(self.efeito_velocidade)}s", (230, 200, 40)))
        if self.efeito_invisivel > 0:
            efeitos.append((f"Invisível {math.ceil(self.efeito_invisivel)}s", COR_INVISIVEL))
        if self.efeito_bussola > 0:
            efeitos.append((f"Bússola {math.ceil(self.efeito_bussola)}s", COR_OURO))
        if self.escondido > 0:
            efeitos.append((f"Escondido {math.ceil(self.escondido)}s", COR_SUCESSO))
        if self.lentidao > 0:
            efeitos.append(("Lento", COR_ALERTA))
        x = 250
        for texto, cor in efeitos:
            imagem = jogo.fonte_pequena.render(texto, True, cor)
            tela.blit(imagem, (x, topo + 10))
            x += imagem.get_width() + 14
        # indicador de proximidade
        nivel = self.proximidade_exibida
        cor = cor_proximidade(nivel)
        desenhar_olho_proximidade(tela, (LARGURA_JANELA - 262, topo + 20), nivel, t)
        barra = pygame.Rect(LARGURA_JANELA - 240, topo + 13, 110, 14)
        pygame.draw.rect(tela, (30, 24, 36), barra, border_radius=7)
        cheio = barra.copy()
        cheio.width = max(6, int(barra.width * nivel))
        pygame.draw.rect(tela, cor, cheio, border_radius=7)
        pygame.draw.rect(tela, (230, 220, 200), barra, 1, border_radius=7)
        rotulo = self.rotulo_proximidade
        if rotulo == "PERIGO!" and int(t * 6) % 2 == 0:
            cor = (255, 255, 255)
        tela.blit(jogo.fonte.render(rotulo, True, cor), (LARGURA_JANELA - 120, topo + 7))

    def _efeito_restante(self, identificador):
        return {"velocidade": self.efeito_velocidade, "invisibilidade": self.efeito_invisivel,
                "bussola": self.efeito_bussola}.get(identificador, 0.0)

    def _desenhar_mensagem(self):
        jogo = self.jogo
        imagem = jogo.fonte.render(self.mensagem, True, COR_TEXTO)
        fundo = imagem.get_rect(center=(LARGURA_JANELA // 2, ALTURA_HUD + 22))
        fundo.inflate_ip(30, 12)
        superficie = pygame.Surface(fundo.size, pygame.SRCALPHA)
        superficie.fill((0, 0, 0, 200))
        jogo.tela.blit(superficie, fundo.topleft)
        pygame.draw.rect(jogo.tela, COR_OURO, fundo, 2, border_radius=8)
        jogo.tela.blit(imagem, imagem.get_rect(center=fundo.center))

    def _desenhar_titulo(self):
        """Faixa de abertura com o nome do modo e as dicas de controle."""
        jogo = self.jogo
        total = TEMPO_TITULO_FASE + 0.8
        t = self.tempo_titulo
        fator = max(0.0, min(1.0, (total - t) / 0.4, t / 0.5))
        faixa = pygame.Surface((LARGURA_JANELA, 120), pygame.SRCALPHA)
        faixa.fill((0, 0, 0, int(180 * fator)))
        jogo.tela.blit(faixa, (0, 260))
        textos = [("PERSEGUIÇÃO", jogo.fonte, COR_OURO, 284),
                  ("O Guardião das Trevas", jogo.fonte_titulo, COR_TEXTO, 318),
                  ("E: santuário/loja   1-5: usar itens   barris: esconderijos   "
                   "paredes rachadas: passagens secretas", jogo.fonte_pequena, (200, 190, 170), 354)]
        for texto, fonte, cor, y in textos:
            imagem = fonte.render(texto, True, cor)
            imagem.set_alpha(int(255 * fator))
            jogo.tela.blit(imagem, imagem.get_rect(center=(LARGURA_JANELA // 2, y)))

    def _desenhar_texto_captura(self):
        progresso = 1 - self.animacao_captura / TEMPO_ANIMACAO_CAPTURA
        alfa = int(255 * min(1.0, progresso * 3))
        desenhar_texto_contorno(self.jogo.tela, self.jogo.fonte_gigante, "CAPTURADO!",
                                (190, 120, 255), (LARGURA_JANELA // 2, 300), (20, 5, 30), 4, alfa)

    def _desenhar_tela_final(self):
        jogo = self.jogo
        tela = jogo.tela
        vitoria = jogo.estado == ESTADO_VITORIA
        alfa = min(195, int(jogo.tempo_fim * 400))
        jogo.veu.fill((0, 0, 0, alfa))
        tela.blit(jogo.veu, (0, 0))
        progresso = min(1.0, jogo.tempo_fim / 0.6)
        queda = int((1 - progresso) ** 2 * 120)
        centro = LARGURA_JANELA // 2
        titulo = "VOCÊ ESCAPOU!" if vitoria else "GAME OVER"
        cor = COR_SUCESSO if vitoria else COR_ALERTA
        imagem = jogo.fonte_gigante.render(titulo, True, cor)
        pulso = 1.0 + 0.04 * math.sin(jogo.tempo_fim * 4)
        imagem = pygame.transform.scale(imagem, (int(imagem.get_width() * pulso),
                                                 int(imagem.get_height() * pulso)))
        imagem.set_alpha(int(255 * progresso))
        tela.blit(imagem, imagem.get_rect(center=(centro, 150 - queda)))
        if progresso < 1.0:
            return
        subtitulo = "Você fugiu da masmorra do Guardião das Trevas." if vitoria \
            else "O Guardião das Trevas te arrastou para as sombras."
        jogo.desenhar_texto(subtitulo, jogo.fonte_pequena, COR_TEXTO, (centro, 202),
                            centralizar=True)
        segundos = int(self.tempo_partida)
        linhas = [(f"Pontuação final: {self.pontos}", jogo.fonte_titulo, COR_OURO),
                  (f"Tempo de sobrevivência: {segundos // 60}:{segundos % 60:02d}",
                   jogo.fonte, COR_TEXTO)]
        if vitoria:
            linhas.append((f"Capturas sofridas: {self.capturas}", jogo.fonte, COR_TEXTO))
            bonus = "   |   ".join(f"{nome} +{pontos}" for nome, pontos in self.bonus)
            linhas.append((f"Bônus: {bonus}", jogo.fonte, COR_SUCESSO))
        else:
            linhas.append((f"Moedas coletadas: {self.moedas_coletadas}   |   Tesouros: "
                           f"{self.tesouros_coletados}", jogo.fonte, COR_TEXTO))
            linhas.append((f"Capturas sofridas: {self.capturas}", jogo.fonte, COR_TEXTO))
        recorde = "NOVO RECORDE!" if self.novo_recorde else \
            f"Recorde do modo: {jogo.recorde_perseguicao} pts"
        linhas.append((recorde, jogo.fonte, COR_OURO if self.novo_recorde else (190, 160, 90)))
        for i, (texto, fonte, cor_linha) in enumerate(linhas):
            jogo.desenhar_texto(texto, fonte, cor_linha, (centro, 240 + i * 36), centralizar=True)
        jogo.menu_fim.desenhar(tela, jogo.fonte_botao, jogo.tempo_fim)
        jogo.desenhar_texto("R: jogar novamente   |   M ou ESC: voltar ao menu",
                            jogo.fonte_pequena, COR_TEXTO, (centro, 590), centralizar=True)
