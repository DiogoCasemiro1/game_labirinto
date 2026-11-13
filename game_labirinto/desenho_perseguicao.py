"""
Desenhos do modo Perseguição (pixel art feita com formas do Pygame):
Guardião das Trevas, santuário, ícones dos itens, bússola e indicador de
proximidade. Reaproveita os auxiliares de desenho.py (sombra e halo).
"""

import math

import pygame

from constantes import (
    ALTURA_JANELA, COR_ALERTA, COR_OURO, LARGURA_JANELA,
    TAMANHO_TILE,
)
from constantes_perseguicao import (
    ESTAGIO_FURIA, ITEM_BUSSOLA, ITEM_CURA, ITEM_ESCUDO, ITEM_INVISIBILIDADE,
    ITEM_VELOCIDADE,
)
from desenho import desenhar_halo, desenhar_sombra


# ----------------------------------------------------------------------
# Guardião das Trevas
# ----------------------------------------------------------------------
def desenhar_guardiao(superficie, retangulo, tempo, estagio, espelhar=False, atordoado=False):
    """Espectro encapuzado: manto de fumaça, olhos brilhantes e garras. Na fúria fica rubro."""
    cx, cy = retangulo.center
    furia = estagio == ESTAGIO_FURIA
    aura = (170, 20, 40) if furia else (96, 36, 160)
    olho = (255, 70, 70) if furia else (225, 90, 255)
    desenhar_sombra(superficie, cx, cy + 17, 30, 120)
    desenhar_halo(superficie, (cx, cy), 44, aura, 70 + int(25 * math.sin(tempo * 4)))
    cy += int(math.sin(tempo * 3) * 3) - 2           # flutua
    lado = -2 if espelhar else 2

    # manto com barra "esfumaçada" que ondula
    base = cy + 19
    ondas = [int(math.sin(tempo * 5 + i * 1.3) * 3) for i in range(6)]
    manto = [(cx - 14, cy - 4), (cx + 14, cy - 4), (cx + 19, base + ondas[0]),
             (cx + 12, base - 4 + ondas[1]), (cx + 5, base + ondas[2]),
             (cx - 1, base - 6 + ondas[3]), (cx - 7, base + ondas[4]),
             (cx - 13, base - 3 + ondas[5]), (cx - 19, base)]
    pygame.draw.polygon(superficie, (14, 10, 22), manto)
    pygame.draw.polygon(superficie, aura, manto, 2)

    # mãos com garras
    for sinal in (-1, 1):
        mx = cx + sinal * 18
        my = cy + 5 + int(math.sin(tempo * 4 + sinal) * 2)
        pygame.draw.circle(superficie, (70, 58, 84), (mx, my), 4)
        for garra in (-3, 0, 3):
            pygame.draw.line(superficie, (200, 190, 210), (mx + sinal * 2, my + garra),
                             (mx + sinal * 8, my + garra + 2), 1)

    # capuz com rosto vazio e olhos
    pygame.draw.circle(superficie, (14, 10, 22), (cx, cy - 10), 12)
    pygame.draw.circle(superficie, aura, (cx, cy - 10), 12, 1)
    pygame.draw.circle(superficie, (3, 2, 6), (cx + lado // 2, cy - 9), 8)
    brilho = 210 + int(45 * math.sin(tempo * 7))
    cor_olho = (min(255, brilho), olho[1], olho[2])
    for dx in (-4, 4):
        pygame.draw.circle(superficie, cor_olho, (cx + dx + lado, cy - 10), 2)
        desenhar_halo(superficie, (cx + dx + lado, cy - 10), 6, olho, 140)
    if atordoado:                                    # estrelinhas girando sobre a cabeça
        for i in range(3):
            ang = tempo * 6 + i * 2.1
            pygame.draw.circle(superficie, COR_OURO,
                               (cx + int(math.cos(ang) * 10), cy - 27 + int(math.sin(ang) * 3)), 2)


def desenhar_olhos_guardiao(superficie, retangulo, tempo, estagio):
    """Só os olhos brilhantes: desenhados DEPOIS da escuridão, para ficarem visíveis nas trevas."""
    cx, cy = retangulo.center
    cy += int(math.sin(tempo * 3) * 3) - 12
    cor = (255, 70, 70) if estagio == ESTAGIO_FURIA else (225, 90, 255)
    for dx in (-4, 4):
        desenhar_halo(superficie, (cx + dx, cy), 9, cor, 200)
        pygame.draw.circle(superficie, cor, (cx + dx, cy), 2)


# ----------------------------------------------------------------------
# Santuário
# ----------------------------------------------------------------------
def desenhar_santuario(superficie, x, y, tempo, perto):
    """Pedestal de pedra com um cristal flutuante; uma seta indica quando se pode interagir."""
    cx, cy = x + TAMANHO_TILE // 2, y + TAMANHO_TILE // 2
    desenhar_halo(superficie, (cx, cy), 40, (120, 200, 255), int(50 + 20 * math.sin(tempo * 2)))
    pygame.draw.rect(superficie, (96, 90, 108), (cx - 15, cy + 12, 30, 7), border_radius=2)
    pygame.draw.rect(superficie, (126, 118, 140), (cx - 11, cy + 2, 22, 12), border_radius=2)
    pygame.draw.rect(superficie, (70, 64, 82), (cx - 11, cy + 2, 22, 12), 1, border_radius=2)
    bob = int(math.sin(tempo * 2.5) * 3)
    cristal = [(cx, cy - 18 + bob), (cx + 7, cy - 8 + bob), (cx, cy + 1 + bob), (cx - 7, cy - 8 + bob)]
    pygame.draw.polygon(superficie, (150, 220, 255), cristal)
    pygame.draw.polygon(superficie, (230, 250, 255), cristal, 1)
    pygame.draw.line(superficie, (255, 255, 255), (cx - 2, cy - 12 + bob), (cx, cy - 6 + bob), 1)
    if perto:
        salto = int(abs(math.sin(tempo * 5)) * 4)
        pygame.draw.polygon(superficie, COR_OURO,
                            [(cx - 6, cy - 32 - salto), (cx + 6, cy - 32 - salto), (cx, cy - 25 - salto)])


# ----------------------------------------------------------------------
# Ícones dos itens (centrados em cx, cy; ocupam ~24 px)
# ----------------------------------------------------------------------
def _frasco(superficie, cx, cy, cor, vazio=False):
    pygame.draw.rect(superficie, (120, 90, 60), (cx - 3, cy - 11, 6, 3))           # rolha
    pygame.draw.rect(superficie, (200, 210, 220), (cx - 3, cy - 8, 6, 5))          # gargalo
    corpo = pygame.Rect(cx - 7, cy - 4, 14, 14)
    pygame.draw.rect(superficie, cor, corpo, border_radius=5)
    pygame.draw.rect(superficie, (230, 235, 245), corpo, 1, border_radius=5)
    if not vazio:
        pygame.draw.circle(superficie, (255, 255, 255), (cx - 3, cy), 1)


def desenhar_icone_item(superficie, item_id, cx, cy, tempo=0.0):
    """Ícone de cada item da loja/inventário."""
    if item_id == ITEM_CURA:
        _frasco(superficie, cx, cy, (200, 40, 56))
        pygame.draw.rect(superficie, (255, 240, 240), (cx - 1, cy + 1, 3, 7))
        pygame.draw.rect(superficie, (255, 240, 240), (cx - 4, cy + 3, 9, 3))
    elif item_id == ITEM_VELOCIDADE:
        _frasco(superficie, cx, cy, (70, 190, 90))
        pygame.draw.polygon(superficie, (255, 240, 90),
                            [(cx + 1, cy - 1), (cx - 3, cy + 5), (cx, cy + 5), (cx - 1, cy + 10),
                             (cx + 4, cy + 3), (cx + 1, cy + 3)])
    elif item_id == ITEM_ESCUDO:
        escudo = [(cx - 9, cy - 9), (cx + 9, cy - 9), (cx + 9, cy + 1), (cx, cy + 11), (cx - 9, cy + 1)]
        pygame.draw.polygon(superficie, (70, 120, 220), escudo)
        pygame.draw.polygon(superficie, (200, 220, 255), escudo, 2)
        pygame.draw.line(superficie, COR_OURO, (cx, cy - 7), (cx, cy + 7), 2)
        pygame.draw.line(superficie, COR_OURO, (cx - 6, cy - 2), (cx + 6, cy - 2), 2)
    elif item_id == ITEM_INVISIBILIDADE:
        _frasco(superficie, cx, cy, (110, 130, 170), vazio=True)
        for ang in range(0, 360, 60):                       # contorno "tracejado" de fantasma
            rad = math.radians(ang + tempo * 40)
            pygame.draw.circle(superficie, (210, 225, 255),
                               (cx + int(math.cos(rad) * 8), cy + 3 + int(math.sin(rad) * 8)), 1)
    elif item_id == ITEM_BUSSOLA:
        pygame.draw.circle(superficie, (170, 126, 48), (cx, cy), 11)
        pygame.draw.circle(superficie, (240, 232, 200), (cx, cy), 8)
        giro = tempo * 2
        pygame.draw.polygon(superficie, COR_ALERTA,
                            [(cx + int(math.sin(giro) * 7), cy - int(math.cos(giro) * 7)),
                             (cx + int(math.cos(giro) * 2), cy + int(math.sin(giro) * 2)),
                             (cx - int(math.cos(giro) * 2), cy - int(math.sin(giro) * 2))])
        pygame.draw.circle(superficie, (60, 50, 40), (cx, cy), 2)


# ----------------------------------------------------------------------
# Efeitos sobre o jogador, bússola e proximidade
# ----------------------------------------------------------------------
def desenhar_aura_escudo(superficie, centro, tempo):
    """Bolha azul pulsante ao redor do jogador com o escudo ativo."""
    raio = 22 + int(math.sin(tempo * 6) * 2)
    desenhar_halo(superficie, centro, 30, (90, 160, 255), 90)
    pygame.draw.circle(superficie, (150, 200, 255), centro, raio, 2)


def desenhar_aura_velocidade(superficie, centro, tempo):
    """Riscos amarelos atrás do jogador enquanto a poção da velocidade está ativa."""
    for i in range(3):
        deslocamento = int((tempo * 60 + i * 9) % 24)
        pygame.draw.line(superficie, (255, 235, 110), (centro[0] - 10 - deslocamento, centro[1] - 8 + i * 8),
                         (centro[0] - 20 - deslocamento, centro[1] - 8 + i * 8), 2)


def desenhar_aura_invisivel(superficie, centro, tempo):
    """Anel tracejado ao redor do jogador invisível."""
    for ang in range(0, 360, 30):
        rad = math.radians(ang + tempo * 60)
        pygame.draw.circle(superficie, (210, 225, 255),
                           (centro[0] + int(math.cos(rad) * 20), centro[1] + int(math.sin(rad) * 20)), 1)


def desenhar_seta_bussola(superficie, centro, angulo, tempo):
    """Seta dourada ao lado do jogador, apontando o caminho (ângulo em radianos)."""
    distancia = 34 + int(math.sin(tempo * 6) * 3)
    px = centro[0] + int(math.cos(angulo) * distancia)
    py = centro[1] + int(math.sin(angulo) * distancia)
    ponta = (px + int(math.cos(angulo) * 9), py + int(math.sin(angulo) * 9))
    esquerda = (px + int(math.cos(angulo + 2.4) * 8), py + int(math.sin(angulo + 2.4) * 8))
    direita = (px + int(math.cos(angulo - 2.4) * 8), py + int(math.sin(angulo - 2.4) * 8))
    desenhar_halo(superficie, (px, py), 16, COR_OURO, 80)
    pygame.draw.polygon(superficie, COR_OURO, [ponta, esquerda, direita])
    pygame.draw.polygon(superficie, (120, 80, 10), [ponta, esquerda, direita], 1)


def criar_vinheta_perigo():
    """Moldura vermelha nas bordas da tela (a intensidade é ajustada por quadro)."""
    vinheta = pygame.Surface((LARGURA_JANELA, ALTURA_JANELA), pygame.SRCALPHA)
    vinheta.fill((200, 10, 30, 200))
    passos = 18
    for i in range(passos):
        fracao = i / (passos - 1)
        alfa = int(200 * (1 - fracao) ** 1.8)
        retangulo = pygame.Rect(0, 0, int(LARGURA_JANELA * 1.5 * (1 - fracao * 0.72)),
                                int(ALTURA_JANELA * 1.5 * (1 - fracao * 0.72)))
        retangulo.center = (LARGURA_JANELA // 2, ALTURA_JANELA // 2)
        pygame.draw.ellipse(vinheta, (200, 10, 30, alfa), retangulo)
    return vinheta


def cor_da_proximidade(nivel):
    """Verde (tranquilo) -> amarelo (alerta) -> vermelho (perigo). nivel: 0 a 1."""
    nivel = max(0.0, min(1.0, nivel))
    if nivel < 0.5:
        f = nivel / 0.5
        return (int(90 + 150 * f), int(200 + 20 * f), int(110 - 60 * f))
    f = (nivel - 0.5) / 0.5
    return (int(240 + 10 * f), int(220 - 150 * f), int(50 + 10 * f))


def desenhar_indicador_proximidade(superficie, x, y, largura, nivel, tempo):
    """Barra que enche e muda de cor conforme o Guardião se aproxima, com um olho que se abre."""
    cor = cor_da_proximidade(nivel)
    barra = pygame.Rect(x + 26, y, largura - 26, 14)
    pygame.draw.rect(superficie, (20, 16, 26), barra, border_radius=6)
    cheio = int((barra.w - 4) * max(0.04, min(1.0, nivel)))
    pygame.draw.rect(superficie, cor, (barra.x + 2, barra.y + 2, cheio, barra.h - 4), border_radius=4)
    borda = COR_ALERTA if nivel >= 0.85 and int(tempo * 6) % 2 == 0 else (150, 110, 40)
    pygame.draw.rect(superficie, borda, barra, 2, border_radius=6)
    # olho: abre conforme o perigo aumenta
    ex, ey = x + 10, y + 7
    abertura = 2 + int(5 * nivel)
    pygame.draw.ellipse(superficie, (230, 225, 235), (ex - 9, ey - abertura, 18, abertura * 2))
    pygame.draw.circle(superficie, cor, (ex, ey), max(2, abertura - 1))
    pygame.draw.circle(superficie, (10, 6, 14), (ex, ey), 1)