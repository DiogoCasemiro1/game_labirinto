"""
Funções de desenho do modo Perseguição (mesma técnica de desenho.py:
pixel art com formas do Pygame, reaproveitando sombras, halos e cores do jogo).
Este módulo só DESENHA: não contém regras.
"""

import math

import pygame

from assets import sprites
from constantes import (
    COR_ALERTA, COR_GUARDIAO, COR_OURO, COR_OURO_ESCURO, COR_SUCESSO,
    COR_TRANQUILO, ESTAGIO_CACADA, ESTAGIO_FURIA, TAMANHO_TILE,
)
from desenho import desenhar_halo, desenhar_sombra


def _misturar(cor_a, cor_b, fracao):
    """Interpola duas cores (fracao 0 = cor_a, 1 = cor_b)."""
    fracao = max(0.0, min(1.0, fracao))
    return tuple(int(a + (b - a) * fracao) for a, b in zip(cor_a, cor_b))


def cor_proximidade(nivel):
    """0 (longe) = verde tranquilo -> 0.5 dourado (alerta) -> 1 vermelho (perigo)."""
    if nivel < 0.5:
        return _misturar(COR_TRANQUILO, COR_OURO, nivel * 2)
    return _misturar(COR_OURO, COR_ALERTA, (nivel - 0.5) * 2)


# ----------------------------------------------------------------------
# Guardião das Trevas
# ----------------------------------------------------------------------
def _cores_do_estagio(estagio, dormindo):
    if dormindo:
        return (70, 40, 110), (110, 90, 150)
    if estagio == ESTAGIO_FURIA:
        return (235, 50, 20), (255, 190, 60)
    if estagio == ESTAGIO_CACADA:
        return (170, 30, 70), (255, 60, 60)
    return COR_GUARDIAO, (200, 150, 255)


def _posicao_guardiao(retangulo, tempo):
    cx, cy = retangulo.center
    return cx, cy - 2 + int(math.sin(tempo * 3) * 2)     # flutua


def desenhar_guardiao(superficie, retangulo, tempo, espelhar=False, estagio=None,
                      atordoado=False, dormindo=False):
    """
    Espectro encapuzado com chifres, manto em farrapos que ondula, garras ósseas
    e olhos que mudam de cor conforme o estágio (vigilância, caçada, fúria).
    """
    cor_aura, cor_olhos = _cores_do_estagio(estagio, dormindo)
    furia = estagio == ESTAGIO_FURIA and not dormindo
    quadro = sprites.obter("guardiao", tempo, espelhar)
    cx, cy = _posicao_guardiao(retangulo, tempo)
    if quadro is not None:
        desenhar_halo(superficie, (cx, cy), 32, cor_aura, 60)
        superficie.blit(quadro, quadro.get_rect(center=(cx, cy)))
    else:
        desenhar_sombra(superficie, retangulo.centerx, retangulo.centery + 17, 30, 120)
        pulso = int(45 + 25 * math.sin(tempo * 4)) + (35 if furia else 0)
        desenhar_halo(superficie, (cx, cy), 32, cor_aura, pulso if not dormindo else 30)

        manto, manto_claro, osso = (26, 18, 38), (58, 40, 82), (205, 196, 176)
        # manto com a barra em farrapos (pontas ondulando)
        base = cy + 15
        farrapos = []
        for i in range(7):
            x = cx + 15 - i * 5
            y = base + (5 if i % 2 == 0 else 0) + int(math.sin(tempo * 7 + i) * 2)
            farrapos.append((x, y))
        pygame.draw.polygon(superficie, manto,
                            [(cx - 8, cy - 9), (cx + 8, cy - 9), (cx + 15, base)]
                            + farrapos + [(cx - 15, base)])
        pygame.draw.polygon(superficie, manto_claro,
                            [(cx - 3, cy - 6), (cx + 3, cy - 6), (cx + 5, base - 2),
                             (cx - 5, base - 2)])                         # dobra central
        pygame.draw.polygon(superficie, cor_aura,
                            [(cx, cy + 1), (cx + 3, cy + 5), (cx, cy + 9), (cx - 3, cy + 5)])  # runa
        # braços com garras
        balanco = int(math.sin(tempo * 5) * 2)
        for lado in (-1, 1):
            ombro = (cx + lado * 9, cy - 3)
            mao = (cx + lado * 17, cy + 6 + balanco * lado)
            pygame.draw.line(superficie, manto, ombro, mao, 5)
            for garra in (-3, 0, 3):
                pygame.draw.line(superficie, osso, mao,
                                 (mao[0] + lado * 4, mao[1] + 4 + garra), 1)
        # capuz com chifres
        for lado in (-1, 1):
            pygame.draw.polygon(superficie, (150, 140, 125),
                                [(cx + lado * 6, cy - 17), (cx + lado * 16, cy - 29),
                                 (cx + lado * 11, cy - 17)])
            pygame.draw.line(superficie, osso, (cx + lado * 7, cy - 18),
                             (cx + lado * 15, cy - 28), 1)
        pygame.draw.circle(superficie, manto, (cx, cy - 12), 10)
        pygame.draw.ellipse(superficie, (4, 2, 8), (cx - 7, cy - 17, 14, 12))   # rosto: só trevas
        if furia:                                                          # chamas no capuz
            for i, dx in enumerate((-6, 0, 6)):
                altura = 6 + int(abs(math.sin(tempo * 14 + i)) * 6)
                pygame.draw.polygon(superficie, (255, 110, 30),
                                    [(cx + dx - 3, cy - 20), (cx + dx + 3, cy - 20),
                                     (cx + dx, cy - 20 - altura)])
    desenhar_olhos_guardiao(superficie, retangulo, tempo, estagio, dormindo)
    if atordoado:
        for i in range(3):
            angulo = tempo * 5 + i * 2.094
            x = cx + int(math.cos(angulo) * 13)
            y = cy - 30 + int(math.sin(angulo) * 4)
            pygame.draw.line(superficie, (255, 240, 150), (x - 3, y), (x + 3, y), 1)
            pygame.draw.line(superficie, (255, 240, 150), (x, y - 3), (x, y + 3), 1)
    elif dormindo:
        for i in range(2):
            fase = (tempo * 0.8 + i * 0.5) % 1.0
            x, y, t = cx + 10 + int(fase * 8), cy - 26 - int(fase * 14), 3 + i
            cor = (170, 150, 220)
            pygame.draw.lines(superficie, cor, False,
                              [(x, y), (x + t, y), (x, y + t), (x + t, y + t)], 1)
    elif estagio in (ESTAGIO_CACADA, ESTAGIO_FURIA):
        pygame.draw.rect(superficie, COR_ALERTA, (cx - 1, cy - 44, 3, 8))     # "!"
        pygame.draw.rect(superficie, COR_ALERTA, (cx - 1, cy - 34, 3, 3))


def desenhar_olhos_guardiao(superficie, retangulo, tempo, estagio, dormindo=False):
    """
    Olhos brilhantes. Também são desenhados POR CIMA da escuridão:
    no breu o jogador vê só os olhos do Guardião se aproximando.
    """
    _, cor_olhos = _cores_do_estagio(estagio, dormindo)
    cx, cy = _posicao_guardiao(retangulo, tempo)
    if dormindo:
        pygame.draw.line(superficie, cor_olhos, (cx - 5, cy - 11), (cx - 2, cy - 11), 1)
        pygame.draw.line(superficie, cor_olhos, (cx + 2, cy - 11), (cx + 5, cy - 11), 1)
        return
    desenhar_halo(superficie, (cx, cy - 11), 10, cor_olhos, 70)
    brilho = int(2 + abs(math.sin(tempo * 6)))
    for lado in (-1, 1):
        pygame.draw.circle(superficie, cor_olhos, (cx + lado * 3, cy - 11), brilho)
        pygame.draw.circle(superficie, (255, 255, 230), (cx + lado * 3, cy - 11), 1)


# ----------------------------------------------------------------------
# Elementos do mapa
# ----------------------------------------------------------------------
def desenhar_rachaduras_passagem(superficie, x, y):
    """Rachaduras extras e frestas de luz: pista discreta de uma parede falsa."""
    escuro, luz = (40, 34, 48), (150, 120, 70)
    pygame.draw.lines(superficie, escuro, False,
                      [(x + 6, y + 4), (x + 12, y + 14), (x + 9, y + 24), (x + 15, y + 35)], 2)
    pygame.draw.lines(superficie, escuro, False,
                      [(x + 31, y + 6), (x + 27, y + 18), (x + 33, y + 30)], 2)
    pygame.draw.line(superficie, luz, (x + 12, y + 15), (x + 10, y + 22), 1)
    pygame.draw.line(superficie, luz, (x + 28, y + 19), (x + 31, y + 27), 1)


def desenhar_santuario(superficie, x, y, tempo, perto=False):
    """Altar de pedra com um cristal flutuante que gira e brilha."""
    t = TAMANHO_TILE
    cx, cy = x + t // 2, y + t // 2
    desenhar_halo(superficie, (cx, cy - 2), 26, (90, 210, 220), 70 if perto else 45)
    pygame.draw.rect(superficie, (70, 64, 82), (x + 6, y + 22, t - 12, 12), border_radius=3)
    pygame.draw.rect(superficie, (100, 94, 116), (x + 8, y + 22, t - 16, 4), border_radius=2)
    pygame.draw.rect(superficie, COR_OURO_ESCURO, (x + 6, y + 22, t - 12, 12), 1, border_radius=3)
    for i, dx in enumerate((-8, 0, 8)):                                # runas no altar
        if int(tempo * 2 + i) % 3 != 0:
            pygame.draw.rect(superficie, (90, 210, 220), (cx + dx - 1, y + 28, 2, 3))
    flutuar = int(math.sin(tempo * 2.5) * 3)
    largura = max(2, int(abs(math.cos(tempo * 2)) * 7))
    topo = cy - 14 + flutuar
    pontos = [(cx, topo - 8), (cx + largura, topo), (cx, topo + 8), (cx - largura, topo)]
    pygame.draw.polygon(superficie, (120, 230, 240), pontos)
    pygame.draw.polygon(superficie, (230, 255, 255), pontos, 1)
    if perto:
        pygame.draw.circle(superficie, COR_OURO, (cx, cy), 19, 1)


def desenhar_esconderijo(superficie, x, y, tempo, disponivel=True, ocupado=False,
                         recarga=0.0):
    """Barril de esconderijo. Ocupado: a tampa entreabre e dois olhos espiam."""
    t = TAMANHO_TILE
    cx, cy = x + t // 2, y + t // 2
    desenhar_sombra(superficie, cx, cy + 14, 30, 100)
    madeira = (120, 78, 40) if disponivel else (70, 50, 34)
    pygame.draw.circle(superficie, (70, 44, 20), (cx, cy), 15)
    pygame.draw.circle(superficie, madeira, (cx, cy), 13)
    pygame.draw.circle(superficie, (60, 56, 64), (cx, cy), 13, 2)          # aro de ferro
    pygame.draw.circle(superficie, (60, 56, 64), (cx, cy), 8, 1)
    for dx in (-5, 0, 5):
        pygame.draw.line(superficie, (90, 58, 28), (cx + dx, cy - 11), (cx + dx, cy + 11), 1)
    if ocupado:
        pygame.draw.ellipse(superficie, (8, 6, 10), (cx - 9, cy - 4, 18, 8))
        piscar = int(tempo * 2) % 5 != 0
        if piscar:
            pygame.draw.circle(superficie, (240, 230, 200), (cx - 3, cy), 1)
            pygame.draw.circle(superficie, (240, 230, 200), (cx + 3, cy), 1)
    elif not disponivel and recarga > 0:
        pygame.draw.arc(superficie, (150, 140, 160), pygame.Rect(cx - 17, cy - 17, 34, 34),
                        math.pi / 2, math.pi / 2 + 2 * math.pi * recarga, 2)
    elif disponivel:
        brilho = int(40 + 30 * math.sin(tempo * 3))
        desenhar_halo(superficie, (cx, cy), 18, COR_SUCESSO, brilho)


# ----------------------------------------------------------------------
# Itens da loja (ícones usados na loja e no inventário)
# ----------------------------------------------------------------------
def _frasco(superficie, cx, cy, cor, escala):
    r = int(7 * escala)
    pygame.draw.circle(superficie, (30, 26, 36), (cx, cy + 2), r + 1)
    pygame.draw.circle(superficie, cor, (cx, cy + 2), r)
    pygame.draw.rect(superficie, (190, 200, 210), (cx - int(2 * escala), cy - r - int(3 * escala),
                                                   int(5 * escala), int(5 * escala)))
    pygame.draw.rect(superficie, (130, 90, 50), (cx - int(2 * escala), cy - r - int(6 * escala),
                                                 int(5 * escala), int(3 * escala)))      # rolha
    pygame.draw.circle(superficie, (255, 255, 255), (cx - r // 2, cy - r // 3 + 2), max(1, r // 4))


def desenhar_icone_item(superficie, identificador, centro, tempo, escala=1.0):
    cx, cy = centro
    if identificador == "cura":
        _frasco(superficie, cx, cy, (210, 40, 60), escala)
        pygame.draw.line(superficie, (255, 200, 200), (cx - 3, cy + 2), (cx + 3, cy + 2), 2)
        pygame.draw.line(superficie, (255, 200, 200), (cx, cy - 1), (cx, cy + 5), 2)
    elif identificador == "velocidade":
        _frasco(superficie, cx, cy, (230, 200, 40), escala)
        pygame.draw.lines(superficie, (255, 255, 230), False,
                          [(cx + 2, cy - 3), (cx - 2, cy + 2), (cx + 2, cy + 2), (cx - 2, cy + 7)], 2)
    elif identificador == "escudo":
        e = escala
        pontos = [(cx - 9 * e, cy - 9 * e), (cx + 9 * e, cy - 9 * e),
                  (cx + 8 * e, cy + 2 * e), (cx, cy + 11 * e), (cx - 8 * e, cy + 2 * e)]
        pygame.draw.polygon(superficie, (60, 110, 200), pontos)
        pygame.draw.polygon(superficie, COR_OURO, pontos, 2)
        pygame.draw.line(superficie, (180, 210, 255), (cx, cy - 7 * e), (cx, cy + 8 * e), 2)
    elif identificador == "invisibilidade":
        _frasco(superficie, cx, cy, (140, 80, 210), escala)
        if int(tempo * 4) % 2 == 0:
            pygame.draw.circle(superficie, (230, 210, 255), (cx + 3, cy + 4), 1)
    elif identificador == "bussola":
        r = int(10 * escala)
        pygame.draw.circle(superficie, COR_OURO_ESCURO, (cx, cy), r)
        pygame.draw.circle(superficie, (235, 225, 195), (cx, cy), r - 2)
        angulo = math.sin(tempo * 1.7) * 0.8
        dx, dy = math.sin(angulo) * (r - 3), -math.cos(angulo) * (r - 3)
        pygame.draw.line(superficie, COR_ALERTA, (cx, cy), (cx + dx, cy + dy), 2)
        pygame.draw.line(superficie, (60, 60, 70), (cx, cy), (cx - dx, cy - dy), 2)
        pygame.draw.circle(superficie, COR_OURO, (cx, cy), 2)


# ----------------------------------------------------------------------
# Efeitos sobre o jogador e indicadores
# ----------------------------------------------------------------------
def desenhar_aura_escudo(superficie, centro, tempo):
    raio = 19 + int(math.sin(tempo * 4) * 1.5)
    desenhar_halo(superficie, centro, raio + 6, (90, 150, 255), 45)
    pygame.draw.circle(superficie, (150, 200, 255), centro, raio, 1)


def desenhar_seta_bussola(superficie, centro, angulo, tempo, cor=COR_OURO):
    """Seta dourada que orbita o jogador apontando a direção do objetivo."""
    distancia = 30 + math.sin(tempo * 6) * 2
    px = centro[0] + math.cos(angulo) * distancia
    py = centro[1] + math.sin(angulo) * distancia
    frente = (px + math.cos(angulo) * 9, py + math.sin(angulo) * 9)
    esquerda = (px + math.cos(angulo + 2.5) * 7, py + math.sin(angulo + 2.5) * 7)
    direita = (px + math.cos(angulo - 2.5) * 7, py + math.sin(angulo - 2.5) * 7)
    desenhar_halo(superficie, (int(px), int(py)), 14, cor, 60)
    pygame.draw.polygon(superficie, cor, [frente, esquerda, (px, py), direita])
    pygame.draw.polygon(superficie, (90, 60, 10), [frente, esquerda, (px, py), direita], 1)


def desenhar_olho_proximidade(superficie, centro, nivel, tempo):
    """Olho que se abre e avermelha conforme o Guardião se aproxima."""
    cx, cy = centro
    cor = cor_proximidade(nivel)
    abertura = 2 + int(7 * nivel)
    if nivel > 0.75:
        abertura += int(abs(math.sin(tempo * 10)) * 2)
    pygame.draw.ellipse(superficie, (20, 16, 26), (cx - 13, cy - 9, 26, 18))
    pygame.draw.ellipse(superficie, cor, (cx - 12, cy - abertura, 24, abertura * 2))
    pygame.draw.circle(superficie, (15, 10, 15), (cx, cy), max(1, abertura - 2))
    pygame.draw.ellipse(superficie, (230, 220, 200), (cx - 13, cy - 9, 26, 18), 1)
