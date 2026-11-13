"""
Interface do jogo: botões, menus, painéis, fundo animado do menu inicial
e tela de instruções. Aqui só há apresentação: as regras ficam em main.py.
"""

import math
import random

import pygame

from constantes import (
    ALTURA_JANELA, COR_OURO, COR_OURO_ESCURO, COR_TEXTO, LARGURA_JANELA,
    TAMANHO_TILE,
)
from desenho import (
    desenhar_armadilha, desenhar_bau, desenhar_chao, desenhar_chave,
    desenhar_dragao, desenhar_esqueleto, desenhar_goblin, desenhar_halo,
    desenhar_jogador, desenhar_moeda, desenhar_parede, desenhar_porta,
    desenhar_tocha,
)
from efeitos import Iluminacao, SistemaParticulas, criar_vinheta

_CACHE_TEXTOS = {}


# ----------------------------------------------------------------------
# Texto com contorno e painéis
# ----------------------------------------------------------------------
def _texto_com_contorno(fonte, texto, cor, contorno, espessura):
    """Renderiza o texto com um contorno escuro (fica legível sobre qualquer fundo)."""
    chave = (id(fonte), texto, cor, contorno, espessura)
    if chave not in _CACHE_TEXTOS:
        if len(_CACHE_TEXTOS) > 200:
            _CACHE_TEXTOS.clear()
        base = fonte.render(texto, True, cor)
        sombra = fonte.render(texto, True, contorno)
        imagem = pygame.Surface((base.get_width() + 2 * espessura,
                                 base.get_height() + 2 * espessura), pygame.SRCALPHA)
        for dx in (-espessura, 0, espessura):
            for dy in (-espessura, 0, espessura):
                if dx or dy:
                    imagem.blit(sombra, (espessura + dx, espessura + dy))
        imagem.blit(base, (espessura, espessura))
        _CACHE_TEXTOS[chave] = imagem
    return _CACHE_TEXTOS[chave]


def desenhar_texto_contorno(tela, fonte, texto, cor, centro, contorno=(15, 10, 5),
                            espessura=2, alfa=255):
    imagem = _texto_com_contorno(fonte, texto, cor, contorno, espessura)
    if alfa < 255:
        imagem = imagem.copy()
        imagem.set_alpha(max(0, alfa))
    tela.blit(imagem, imagem.get_rect(center=centro))


def desenhar_painel(tela, retangulo, alfa=215):
    """Painel escuro e translúcido com moldura dourada."""
    fundo = pygame.Surface((retangulo.w, retangulo.h), pygame.SRCALPHA)
    fundo.fill((20, 16, 28, alfa))
    tela.blit(fundo, retangulo.topleft)
    pygame.draw.rect(tela, COR_OURO_ESCURO, retangulo, 3, border_radius=12)
    pygame.draw.rect(tela, (90, 66, 28), retangulo.inflate(-10, -10), 1, border_radius=9)


# ----------------------------------------------------------------------
# Botões e menus
# ----------------------------------------------------------------------
class Botao:
    def __init__(self, texto, acao, retangulo, subtitulo=""):
        self.texto = texto
        self.acao = acao              # texto que identifica o que o botão faz
        self.retangulo = retangulo
        self.subtitulo = subtitulo    # linha pequena opcional sob o texto (ex.: "5 VIDAS")


class MenuVertical:
    """Lista de botões empilhados, navegável pelo teclado e pelo mouse."""

    def __init__(self, opcoes, centro_x, y_inicial, largura=360, altura=52, espaco=16):
        self.botoes = []
        for i, opcao in enumerate(opcoes):
            texto, acao = opcao[0], opcao[1]
            subtitulo = opcao[2] if len(opcao) > 2 else ""     # (texto, acao[, subtitulo])
            retangulo = pygame.Rect(0, 0, largura, altura)
            retangulo.center = (centro_x, y_inicial + altura // 2 + i * (altura + espaco))
            self.botoes.append(Botao(texto, acao, retangulo, subtitulo))
        self.selecionado = 0

    def mover(self, delta):
        self.selecionado = (self.selecionado + delta) % len(self.botoes)

    def acao_selecionada(self):
        return self.botoes[self.selecionado].acao

    def passar_mouse(self, posicao):
        """Seleciona o botão sob o mouse. Retorna True se havia algum."""
        for i, botao in enumerate(self.botoes):
            if botao.retangulo.collidepoint(posicao):
                self.selecionado = i
                return True
        return False

    def clicar(self, posicao):
        """Retorna a ação do botão clicado (ou None)."""
        for botao in self.botoes:
            if botao.retangulo.collidepoint(posicao):
                return botao.acao
        return None

    def desenhar(self, tela, fonte, tempo, fonte_sub=None):
        for i, botao in enumerate(self.botoes):
            ativo = i == self.selecionado
            r = botao.retangulo
            pygame.draw.rect(tela, (10, 8, 12), r.move(3, 4), border_radius=10)       # sombra
            pygame.draw.rect(tela, (96, 74, 40) if ativo else (54, 48, 66), r, border_radius=10)
            pygame.draw.rect(tela, (126, 98, 52) if ativo else (74, 68, 90),
                             (r.x + 4, r.y + 4, r.w - 8, r.h // 2 - 4), border_radius=8)
            pygame.draw.rect(tela, COR_OURO if ativo else (124, 108, 146), r, 3, border_radius=10)
            if ativo:
                pulso = int(abs(math.sin(tempo * 5)) * 4)
                pygame.draw.rect(tela, (255, 232, 140), r.inflate(pulso * 2, pulso * 2), 1,
                                 border_radius=12)
                desenhar_tocha(tela, r.left - 28, r.centery + 4, tempo, i)           # tochas laterais
                desenhar_tocha(tela, r.right + 28, r.centery + 4, tempo, i + 3)
            cor = (255, 240, 180) if ativo else COR_TEXTO
            if botao.subtitulo and fonte_sub is not None:
                desenhar_texto_contorno(tela, fonte, botao.texto, cor, (r.centerx, r.centery - 11))
                desenhar_texto_contorno(tela, fonte_sub, botao.subtitulo, COR_OURO,
                                        (r.centerx, r.centery + 16), (10, 8, 14), 1)
            else:
                desenhar_texto_contorno(tela, fonte, botao.texto, cor, r.center)


# ----------------------------------------------------------------------
# Título e fundo animado do menu inicial
# ----------------------------------------------------------------------
def desenhar_titulo(tela, fonte_grande, fonte_media, tempo):
    """Título 'LABIRINTO / A FUGA' que cai na tela e brilha."""
    progresso = min(1.0, tempo / 0.8)
    queda = int((1 - progresso) ** 2 * 140)
    alfa = int(255 * progresso)
    desenhar_halo(tela, (LARGURA_JANELA // 2, 130), 230, COR_OURO,
                  int(34 + 10 * math.sin(tempo * 2)))
    desenhar_texto_contorno(tela, fonte_grande, "LABIRINTO", COR_OURO,
                            (LARGURA_JANELA // 2, 100 - queda), (60, 30, 5), 4, alfa)
    desenhar_texto_contorno(tela, fonte_media, "A  FUGA", (238, 226, 198),
                            (LARGURA_JANELA // 2, 178 - queda), (40, 24, 10), 3, alfa)
    # filete dourado com losango no centro
    y = 214 - queda
    meio = LARGURA_JANELA // 2
    pygame.draw.line(tela, COR_OURO_ESCURO, (meio - 180, y), (meio - 14, y), 2)
    pygame.draw.line(tela, COR_OURO_ESCURO, (meio + 14, y), (meio + 180, y), 2)
    pygame.draw.polygon(tela, COR_OURO, [(meio - 9, y), (meio, y - 7), (meio + 9, y), (meio, y + 7)])


class FundoMenu:
    """Cenário animado do menu: parede de tijolos, tochas, personagens e luz que segue o mouse."""

    LINHAS_PAREDE = 10        # linhas de parede; o resto da tela é chão

    def __init__(self):
        self.base = self._pre_renderizar()
        self.iluminacao = Iluminacao()
        self.particulas = SistemaParticulas()
        self.vinheta = criar_vinheta()
        self.cena = pygame.Surface((LARGURA_JANELA, ALTURA_JANELA))
        self.temporaria = pygame.Surface((96, 96), pygame.SRCALPHA)    # personagem a ampliar
        self.moldura = pygame.Rect(0, 0, 28, 28)
        self.moldura.center = (48, 48)
        self.tochas = [(140, 210), (400, 210), (560, 210), (820, 210)]
        self.luzes_extras = [(480, 100), (150, 570), (480, 585), (780, 575)]
        self.luz = [LARGURA_JANELA / 2, 330.0]
        self.tempo = 0.0

    def _pre_renderizar(self):
        base = pygame.Surface((LARGURA_JANELA, ALTURA_JANELA))
        for linha in range(ALTURA_JANELA // TAMANHO_TILE):
            for coluna in range(LARGURA_JANELA // TAMANHO_TILE):
                x, y = coluna * TAMANHO_TILE, linha * TAMANHO_TILE
                if linha < self.LINHAS_PAREDE:
                    desenhar_parede(base, x, y, True, (coluna * 7 + linha * 13) % 8)
                else:
                    desenhar_chao(base, x, y, linha, coluna, linha == self.LINHAS_PAREDE)
        return base

    def atualizar(self, dt, posicao_mouse):
        self.tempo += dt
        self.particulas.atualizar(dt)
        for x, y in self.tochas:
            if random.random() < dt * 3:
                self.particulas.brasa(x, y - 8)
        alvo = posicao_mouse if posicao_mouse is not None else (LARGURA_JANELA // 2, 330)
        suavizar = min(1.0, dt * 6)
        self.luz[0] += (alvo[0] - self.luz[0]) * suavizar
        self.luz[1] += (alvo[1] - self.luz[1]) * suavizar

    def _ampliado(self, cena, desenhar, centro, escala=2):
        """Desenha um personagem numa superfície pequena e o amplia (pixels 'gordinhos')."""
        self.temporaria.fill((0, 0, 0, 0))
        desenhar(self.temporaria)
        lado = self.temporaria.get_width() * escala
        imagem = pygame.transform.scale(self.temporaria, (lado, lado))
        cena.blit(imagem, imagem.get_rect(center=centro))

    def _desenhar_personagens(self, cena):
        t = self.tempo
        m = self.moldura
        c = (48, 48)
        self._ampliado(cena, lambda s: desenhar_jogador(s, m, "direita", t, False), (110, 570))
        self._ampliado(cena, lambda s: desenhar_bau(s, c, t), (260, 580))
        self._ampliado(cena, lambda s: desenhar_chave(s, c, t + 1), (340, 575))
        self._ampliado(cena, lambda s: desenhar_moeda(s, c, t + 2), (410, 585))
        oscilar = math.sin(t * 0.9)
        espelhar = math.cos(t * 0.9) < 0
        self._ampliado(cena, lambda s: desenhar_esqueleto(s, m, t, espelhar),
                       (int(570 + 70 * oscilar), 570))
        alerta = int(t / 2) % 2 == 0
        self._ampliado(cena, lambda s: desenhar_goblin(s, m, t, True, alerta), (730, 570))
        self._ampliado(cena, lambda s: desenhar_dragao(s, m, t, True, alerta), (860, 560))

    def desenhar(self, tela):
        cena = self.cena
        cena.blit(self.base, (0, 0))
        for x, y in self.tochas:
            desenhar_tocha(cena, x, y, self.tempo, x)
        self._desenhar_personagens(cena)
        self.particulas.desenhar(cena, None)
        self.iluminacao.desenhar(cena, (int(self.luz[0]), int(self.luz[1])),
                                 self.tochas + self.luzes_extras, self.tempo, 125)
        cena.blit(self.vinheta, (0, 0))
        tela.blit(cena, (0, 0))


# ----------------------------------------------------------------------
# Tela de instruções
# ----------------------------------------------------------------------
def desenhar_instrucoes(tela, fonte_titulo, fonte_secao, fonte_texto, tempo):
    """Painel com controles, objetivo, itens, perigos e modos de jogo."""
    painel = pygame.Rect(70, 30, LARGURA_JANELA - 140, 580)
    desenhar_painel(tela, painel, 228)
    desenhar_texto_contorno(tela, fonte_titulo, "INSTRUÇÕES", COR_OURO, (LARGURA_JANELA // 2, 72),
                            (60, 30, 5), 3)
    moldura = pygame.Rect(0, 0, 28, 28)

    def icone_chave(x, y):
        desenhar_chave(tela, (x, y), tempo)

    def icone_porta(x, y):
        desenhar_porta(tela, x - 20, y - 20, True, 1.0, tempo)

    def icone_moeda(x, y):
        desenhar_moeda(tela, (x, y), tempo)

    def icone_bau(x, y):
        desenhar_bau(tela, (x, y), tempo)

    def icone_esqueleto(x, y):
        moldura.center = (x, y)
        desenhar_esqueleto(tela, moldura, tempo)

    def icone_espinhos(x, y):
        desenhar_armadilha(tela, x - 20, y - 20, "ativa", 1.0, tempo)

    linhas = [
        ("secao", "CONTROLES"),
        ("texto", "Setas ou W A S D: mover o aventureiro"),
        ("texto", "P ou ESC: pausar          L: ligar / desligar a luz"),
        ("secao", "OBJETIVO"),
        ("item", icone_chave, "Encontre a chave: ela destranca a porta de saída"),
        ("item", icone_porta, "Atravesse a porta aberta para ir à próxima fase"),
        ("item", icone_moeda, "Moeda: 10 pontos"),
        ("item", icone_bau, "Baú de tesouro: 50 pontos"),
        ("secao", "PERIGOS"),
        ("item", icone_esqueleto, "Esqueletos patrulham; goblins perseguem se te virem"),
        ("item", icone_espinhos, "Espinhos: não pise quando estiverem vermelhos ou erguidos"),
        ("texto", "Tocar num monstro ou deixar o tempo acabar custa 1 vida (são 3)"),
        ("secao", "MODOS DE JOGO"),
        ("texto", "Campanha: 5 fases fixas, terminando no covil do Dragão"),
        ("texto", "Infinito: fases sem fim (escolha Fácil, Médio ou Difícil); chefe dá +1 vida"),
        ("texto", "Perseguição: fuja do Guardião; E abre o santuário; teclas 1 a 5 usam itens"),
    ]
    y = 112
    for linha in linhas:
        if linha[0] == "secao":
            y += 4
            desenhar_texto_contorno(tela, fonte_secao, linha[1], COR_OURO, (LARGURA_JANELA // 2, y + 10))
            y += 26
        elif linha[0] == "texto":
            desenhar_texto_contorno(tela, fonte_texto, linha[1], COR_TEXTO,
                                    (LARGURA_JANELA // 2, y + 10), (10, 8, 14), 1)
            y += 26
        else:
            linha[1](130, y + 10)
            imagem = _texto_com_contorno(fonte_texto, linha[2], COR_TEXTO, (10, 8, 14), 1)
            tela.blit(imagem, imagem.get_rect(midleft=(170, y + 10)))
            y += 26
    alfa = int(150 + 105 * (math.sin(tempo * 3) + 1) / 2)
    desenhar_texto_contorno(tela, fonte_texto, "ENTER, ESPAÇO ou ESC para voltar", COR_OURO,
                            (LARGURA_JANELA // 2, 588), (10, 8, 14), 1, alfa)