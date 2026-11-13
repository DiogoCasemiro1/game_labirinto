"""
Funções de desenho (pixel art feita com formas do próprio Pygame).
Este módulo só DESENHA: não contém regras do jogo.
Se existir uma imagem PNG em assets/imagens/, ela substitui o desenho
geométrico correspondente (veja assets.py).
"""

import math

import pygame

from assets import sprites
from constantes import (
    ALTURA_HUD, COR_ALERTA, COR_CHAO, COR_CHAO_DETALHE, COR_CHAO_JUNTA,
    COR_OURO, COR_OURO_ESCURO, COR_PAREDE, COR_PAREDE_CLARA, COR_PAREDE_ESCURA,
    COR_CONTORNO_PAREDE, COR_PORTA, COR_PORTA_ESCURA, COR_SUCESSO,
    COR_TOPO_LAJE, COR_TOPO_PAREDE, COR_VIDA, LARGURA_JANELA, TAMANHO_TILE,
)

# ----------------------------------------------------------------------
# Auxiliares: sombras, halos e brilhos (guardados em cache para ficarem rápidos)
# ----------------------------------------------------------------------
_CACHE_SOMBRAS = {}
_CACHE_HALOS = {}
_CACHE_SOMBRA_PAREDE = []


def _blit_centralizado(superficie, quadro, centro):
    """Desenha uma imagem com o centro no ponto indicado."""
    superficie.blit(quadro, quadro.get_rect(center=centro))


def desenhar_sombra(superficie, cx, y_base, largura, alfa=90):
    """Sombra oval translúcida sob os pés de personagens e itens."""
    altura = max(4, largura // 3)
    chave = (largura, altura, alfa)
    if chave not in _CACHE_SOMBRAS:
        sombra = pygame.Surface((largura, altura), pygame.SRCALPHA)
        pygame.draw.ellipse(sombra, (0, 0, 0, alfa), (0, 0, largura, altura))
        _CACHE_SOMBRAS[chave] = sombra
    superficie.blit(_CACHE_SOMBRAS[chave], (cx - largura // 2, y_base - altura // 2))


def desenhar_halo(superficie, centro, raio, cor, alfa_maximo):
    """Brilho suave e colorido ao redor de um ponto."""
    chave = (raio, cor, alfa_maximo)
    if chave not in _CACHE_HALOS:
        halo = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
        for r in range(raio, 0, -2):
            alfa = int(alfa_maximo * (1 - r / raio) ** 1.5)
            pygame.draw.circle(halo, (cor[0], cor[1], cor[2], alfa), (raio, raio), r)
        _CACHE_HALOS[chave] = halo
    superficie.blit(_CACHE_HALOS[chave], (centro[0] - raio, centro[1] - raio))


def _estrelinha(superficie, cx, cy, tamanho, cor):
    """Pequeno brilho em forma de cruz (efeito de reflexo)."""
    pygame.draw.line(superficie, cor, (cx - tamanho, cy), (cx + tamanho, cy), 1)
    pygame.draw.line(superficie, cor, (cx, cy - tamanho), (cx, cy + tamanho), 1)


def _sombra_de_parede():
    """Faixa de sombra projetada pelas paredes sobre o chão logo abaixo delas."""
    if not _CACHE_SOMBRA_PAREDE:
        faixa = pygame.Surface((TAMANHO_TILE, 12), pygame.SRCALPHA)
        for i in range(12):
            alfa = int(120 * (1 - i / 12) ** 2)
            pygame.draw.line(faixa, (0, 0, 0, alfa), (0, i), (TAMANHO_TILE, i))
        _CACHE_SOMBRA_PAREDE.append(faixa)
    return _CACHE_SOMBRA_PAREDE[0]


# ----------------------------------------------------------------------
# Cenário: paredes, chão, tochas, porta e armadilhas
# ----------------------------------------------------------------------
def desenhar_parede(superficie, x, y, face=True, variante=0, bordas=(False,) * 4):
    """
    Parede vista de cima, em dois estilos:
      face=True  -> face frontal de tijolos (tem chão aberto logo abaixo)
      face=False -> topo da parede: lajes azuladas em relevo
    'variante' (0-7) espalha pequenas diferenças (rachaduras, musgo, tijolos claros).
    'bordas' = (esquerda, direita, cima, baixo): True onde o vizinho é chão; ali
    é desenhado um contorno escuro, para a parede nunca "se misturar" com o piso.
    """
    quadro = sprites.obter("parede")
    if quadro is not None:
        superficie.blit(quadro, (x, y))
        return
    t = TAMANHO_TILE
    if not face:
        pygame.draw.rect(superficie, COR_TOPO_PAREDE, (x, y, t, t))
        pygame.draw.rect(superficie, COR_TOPO_LAJE, (x + 4, y + 4, t - 8, t - 8))   # laje em relevo
        pygame.draw.rect(superficie, COR_PAREDE_ESCURA, (x + 4, y + 4, t - 8, t - 8), 1)
        pygame.draw.line(superficie, COR_PAREDE_CLARA, (x, y), (x + t - 1, y), 2)   # luz
        pygame.draw.line(superficie, COR_PAREDE_CLARA, (x, y), (x, y + t - 1), 2)
        pygame.draw.line(superficie, COR_PAREDE_ESCURA, (x, y + t - 1), (x + t - 1, y + t - 1), 2)
        pygame.draw.line(superficie, COR_PAREDE_ESCURA, (x + t - 1, y), (x + t - 1, y + t - 1), 2)
        if variante in (1, 5):
            pygame.draw.line(superficie, COR_PAREDE_ESCURA, (x + 9, y + 11), (x + 20, y + 17), 1)
            pygame.draw.line(superficie, COR_PAREDE_ESCURA, (x + 20, y + 17), (x + 24, y + 28), 1)
    else:
        # --- face de tijolos: 3 fileiras com as juntas deslocadas ---
        pygame.draw.rect(superficie, COR_PAREDE, (x, y, t, t))
        juntas_verticais = [(10, 30), (0, 20, 40), (10, 30)]
        for fila in range(3):
            topo = y + fila * 13
            if (variante + fila) % 3 == 0:     # um tijolo mais claro por fileira, de vez em quando
                pygame.draw.rect(superficie, (142, 134, 152), (x + 11, topo + 1, 18, 11))
            if fila > 0:
                pygame.draw.line(superficie, COR_PAREDE_ESCURA, (x, topo), (x + t, topo), 2)
            for junta in juntas_verticais[fila]:
                pygame.draw.line(superficie, COR_PAREDE_ESCURA,
                                 (x + junta, topo), (x + junta, topo + 13), 2)
        if variante == 3:                       # musgo escorrendo
            pygame.draw.ellipse(superficie, (58, 98, 62), (x + 4, y + 24, 16, 9))
            pygame.draw.ellipse(superficie, (74, 120, 74), (x + 8, y + 26, 8, 4))
        if variante == 6:                       # rachadura
            pygame.draw.lines(superficie, COR_PAREDE_ESCURA, False,
                              [(x + 22, y + 2), (x + 18, y + 12), (x + 24, y + 20), (x + 20, y + 30)], 2)
        pygame.draw.line(superficie, COR_PAREDE_CLARA, (x, y), (x + t - 1, y), 2)
        pygame.draw.rect(superficie, (52, 46, 62), (x, y + t - 5, t, 5))            # base escura
    # contorno escuro nos lados que encostam no chão
    esquerda, direita, cima, baixo = bordas
    if esquerda:
        pygame.draw.line(superficie, COR_CONTORNO_PAREDE, (x, y), (x, y + t - 1), 3)
    if direita:
        pygame.draw.line(superficie, COR_CONTORNO_PAREDE, (x + t - 1, y), (x + t - 1, y + t - 1), 3)
    if cima:
        pygame.draw.line(superficie, COR_CONTORNO_PAREDE, (x, y), (x + t - 1, y), 3)
    if baixo:
        pygame.draw.line(superficie, COR_CONTORNO_PAREDE, (x, y + t - 1), (x + t - 1, y + t - 1), 3)


def desenhar_chao(superficie, x, y, linha, coluna, sombra_topo=False):
    """Piso de pedra com pequenas variações (rachaduras, pedrinhas, manchas)."""
    quadro = sprites.obter("chao")
    if quadro is not None:
        superficie.blit(quadro, (x, y))
        return
    t = TAMANHO_TILE
    cor = COR_CHAO if (linha + coluna) % 2 == 0 else COR_CHAO_DETALHE
    pygame.draw.rect(superficie, cor, (x, y, t, t))
    pygame.draw.rect(superficie, COR_CHAO_JUNTA, (x, y, t, t), 1)
    detalhe = (coluna * 7 + linha * 13) % 11
    if detalhe == 0:                        # rachadura
        pygame.draw.lines(superficie, COR_CHAO_JUNTA, False,
                          [(x + 6, y + 30), (x + 15, y + 24), (x + 20, y + 28), (x + 31, y + 14)], 1)
    elif detalhe == 1:                      # pedrinhas
        pygame.draw.circle(superficie, (66, 60, 72), (x + 12, y + 26), 2)
        pygame.draw.circle(superficie, (62, 56, 68), (x + 27, y + 12), 1)
        pygame.draw.circle(superficie, (66, 60, 72), (x + 30, y + 30), 2)
    elif detalhe == 2:                      # mancha escura
        pygame.draw.ellipse(superficie, (38, 33, 44), (x + 8, y + 10, 22, 14))
    if sombra_topo:
        superficie.blit(_sombra_de_parede(), (x, y))


def desenhar_tocha(superficie, cx, cy, tempo, semente):
    """Tocha na parede: suporte de ferro e chama que balança."""
    pygame.draw.rect(superficie, (46, 38, 34), (cx - 2, cy + 2, 4, 10))        # haste
    pygame.draw.rect(superficie, (92, 70, 48), (cx - 4, cy - 2, 8, 5), border_radius=1)
    oscilacao = math.sin(tempo * 9 + semente * 1.7)
    ponta = int(math.sin(tempo * 13 + semente * 0.9) * 2)
    altura = int(10 + oscilacao * 2)
    pygame.draw.polygon(superficie, (255, 120, 30),
                        [(cx - 4, cy - 2), (cx + 4, cy - 2), (cx + ponta, cy - 2 - altura)])
    pygame.draw.polygon(superficie, (255, 205, 90),
                        [(cx - 2, cy - 2), (cx + 2, cy - 2), (cx + ponta // 2, cy - 2 - int(altura * 0.62))])


def desenhar_porta(superficie, x, y, aberta, progresso, tempo):
    """
    Porta de saída. 'progresso' vai de 0 (fechada) a 1 (aberta): a porta
    de madeira sobe como uma grade, revelando a passagem escura.
    """
    quadro = sprites.obter("porta_aberta" if aberta else "porta_fechada")
    if quadro is not None:
        superficie.blit(quadro, (x, y))
        return
    t = TAMANHO_TILE
    pygame.draw.rect(superficie, COR_PAREDE_CLARA, (x + 2, y + 2, t - 4, t - 2), border_radius=6)
    pygame.draw.rect(superficie, (6, 5, 9), (x + 6, y + 6, t - 12, t - 6))      # passagem
    if progresso >= 1.0:                    # saída liberada: brilho verde pulsante
        desenhar_halo(superficie, (x + t // 2, y + t // 2), 24, COR_SUCESSO,
                      int(55 + 30 * math.sin(tempo * 4)))
        pygame.draw.rect(superficie, COR_SUCESSO, (x + 6, y + 6, t - 12, t - 6), 1)
    altura_painel = int((t - 6) * (1 - min(1.0, progresso)))
    if altura_painel > 0:
        pygame.draw.rect(superficie, COR_PORTA, (x + 6, y + 6, t - 12, altura_painel))
        for tabua in (13, 20, 27):          # divisões das tábuas
            pygame.draw.line(superficie, COR_PORTA_ESCURA, (x + tabua, y + 6),
                             (x + tabua, y + 6 + altura_painel), 1)
        if altura_painel > 12:              # ferragens
            pygame.draw.line(superficie, (60, 56, 64), (x + 6, y + 12), (x + t - 7, y + 12), 2)
        if progresso == 0.0:                # cadeado balançando de leve
            balanco = int(math.sin(tempo * 3))
            pygame.draw.rect(superficie, COR_OURO,
                             (x + t // 2 - 5 + balanco, y + t // 2, 10, 8), border_radius=2)
            pygame.draw.arc(superficie, COR_OURO,
                            pygame.Rect(x + t // 2 - 4 + balanco, y + t // 2 - 7, 8, 12),
                            0, math.pi, 2)


def desenhar_armadilha(superficie, x, y, estado, altura=0.0, tempo=0.0):
    """
    Armadilha de espinhos. 'altura' (0 a 1) é o quanto os espinhos já subiram;
    no estado 'alerta' eles tremem e ficam avermelhados.
    """
    baixo = sprites.obter("espinhos_baixo")
    cima = sprites.obter("espinhos_cima")
    if baixo is not None and cima is not None:
        superficie.blit(cima if estado == "ativa" else baixo, (x, y))
        if estado == "alerta":      # contorno vermelho avisa que vai subir
            pygame.draw.rect(superficie, COR_ALERTA,
                             (x + 2, y + 2, TAMANHO_TILE - 4, TAMANHO_TILE - 4), 2)
        return
    t = TAMANHO_TILE
    pygame.draw.rect(superficie, (34, 28, 38), (x + 4, y + 4, t - 8, t - 8), border_radius=3)
    pygame.draw.rect(superficie, (72, 66, 80), (x + 4, y + 4, t - 8, t - 8), 1, border_radius=3)
    tremor = int(math.sin(tempo * 55) * 1.5) if estado == "alerta" else 0
    for px in (10, 20, 30):
        for py in (10, 20, 30):
            cx, cy = x + px, y + py
            pygame.draw.circle(superficie, (14, 11, 18), (cx, cy), 3)          # buraco
            altura_pixels = int(11 * altura)
            if altura_pixels > 0:
                cor = (225, 95, 85) if estado == "alerta" else (205, 210, 222)
                pygame.draw.polygon(superficie, cor,
                                    [(cx - 3 + tremor, cy + 2), (cx + 3 + tremor, cy + 2),
                                     (cx + tremor, cy + 2 - altura_pixels)])
                pygame.draw.line(superficie, (250, 250, 255), (cx - 1 + tremor, cy + 1),
                                 (cx + tremor, cy + 2 - altura_pixels), 1)


# ----------------------------------------------------------------------
# Itens
# ----------------------------------------------------------------------
def desenhar_moeda(superficie, centro, tempo):
    """Moeda que gira, flutua e reflete a luz de vez em quando."""
    quadro = sprites.obter("moeda", tempo)
    if quadro is not None:
        _blit_centralizado(superficie, quadro, centro)
        return
    cx, cy = centro
    desenhar_sombra(superficie, cx, cy + 11, 14)
    cy += int(math.sin(tempo * 3) * 2)
    desenhar_halo(superficie, (cx, cy), 16, COR_OURO, 45)
    largura = max(2, int(abs(math.cos(tempo * 4)) * 8))
    pygame.draw.ellipse(superficie, COR_OURO, (cx - largura, cy - 8, largura * 2, 16))
    pygame.draw.ellipse(superficie, COR_OURO_ESCURO, (cx - largura, cy - 8, largura * 2, 16), 2)
    if largura > 4:
        pygame.draw.line(superficie, (255, 240, 150), (cx - largura + 3, cy - 4),
                         (cx - largura + 3, cy + 2), 1)
    if int(tempo * 3) % 4 == 0:
        _estrelinha(superficie, cx + 6, cy - 8, 3, (255, 250, 200))


def desenhar_chave(superficie, centro, tempo):
    """Chave dourada que flutua e brilha."""
    cx, cy = centro
    cy += int(math.sin(tempo * 3) * 3)
    quadro = sprites.obter("chave", tempo)
    if quadro is not None:
        _blit_centralizado(superficie, quadro, (cx, cy))
        return
    desenhar_sombra(superficie, cx, centro[1] + 12, 16)
    desenhar_halo(superficie, (cx, cy), 20, COR_OURO, 60)
    pygame.draw.circle(superficie, COR_OURO, (cx - 7, cy), 6, 3)       # argola
    pygame.draw.circle(superficie, COR_OURO_ESCURO, (cx - 7, cy), 6, 1)
    pygame.draw.rect(superficie, COR_OURO, (cx - 2, cy - 1, 14, 3))    # haste
    pygame.draw.rect(superficie, COR_OURO, (cx + 7, cy + 1, 3, 5))     # dentes
    pygame.draw.rect(superficie, COR_OURO, (cx + 11, cy + 1, 3, 4))
    _estrelinha(superficie, cx - 10 + int((tempo * 14) % 22), cy - 2, 2, (255, 252, 210))


def desenhar_bau(superficie, centro, tempo):
    """Baú com a tampa que se entreabre, luz dourada saindo e faíscas."""
    quadro = sprites.obter("bau", tempo)
    if quadro is not None:
        _blit_centralizado(superficie, quadro, centro)
        return
    cx, cy = centro
    desenhar_sombra(superficie, cx, cy + 12, 26)
    desenhar_halo(superficie, (cx, cy), 22, COR_OURO, 55)
    abre = int(abs(math.sin(tempo * 2)) * 3)
    pygame.draw.rect(superficie, (118, 70, 30), (cx - 11, cy - 2, 22, 13), border_radius=2)
    if abre > 0:                            # luz dourada na fresta
        pygame.draw.rect(superficie, (255, 225, 120), (cx - 9, cy - 3, 18, abre + 1))
    pygame.draw.rect(superficie, (150, 92, 40), (cx - 11, cy - 9 - abre, 22, 8), border_radius=4)
    pygame.draw.rect(superficie, COR_OURO_ESCURO, (cx - 11, cy - 2, 22, 13), 2, border_radius=2)
    pygame.draw.line(superficie, COR_OURO_ESCURO, (cx - 6, cy - 9 - abre), (cx - 6, cy + 10), 2)
    pygame.draw.line(superficie, COR_OURO_ESCURO, (cx + 6, cy - 9 - abre), (cx + 6, cy + 10), 2)
    pygame.draw.rect(superficie, COR_OURO, (cx - 3, cy - 3, 6, 6))
    _estrelinha(superficie, cx + int(9 * math.cos(tempo * 2)),
                cy - 13 + int(3 * math.sin(tempo * 2.7)), 3, (255, 250, 200))


# ----------------------------------------------------------------------
# Personagens
# ----------------------------------------------------------------------
def _pernas(superficie, cx, cy, perna, calca, bota):
    """Pernas vistas de frente/costas; 'perna' (-3 a 3) alterna o passo."""
    pygame.draw.rect(superficie, calca, (cx - 6, cy + 6, 5, 7 + perna))
    pygame.draw.rect(superficie, bota, (cx - 6, cy + 12 + perna, 5, 3))
    pygame.draw.rect(superficie, calca, (cx + 1, cy + 6, 5, 7 - perna))
    pygame.draw.rect(superficie, bota, (cx + 1, cy + 12 - perna, 5, 3))


def desenhar_jogador(superficie, retangulo, direcao, tempo_animacao, andando):
    """
    Aventureiro com capuz verde, túnica vermelha e capa. Tem sprites diferentes
    para frente, costas e lado; ao andar balança pernas, braços e capa; parado, 'respira'.
    """
    nome = "jogador_andando" if andando and sprites.tem("jogador_andando") else "jogador"
    quadro = sprites.obter(nome, tempo_animacao, espelhar=(direcao == "esquerda"))
    if quadro is not None:
        _blit_centralizado(superficie, quadro, retangulo.center)
        return
    cx, cy = retangulo.center
    desenhar_sombra(superficie, cx, cy + 14, 20)
    if andando:
        ciclo = math.sin(tempo_animacao * 14)
        cy -= int(abs(ciclo) * 2)
    else:
        ciclo = 0.0
        cy -= int((math.sin(tempo_animacao * 3) + 1) * 0.6)    # respiração
    perna = int(ciclo * 3)
    pele, capuz, tunica = (236, 196, 156), (46, 110, 62), (165, 42, 46)
    capa, calca, bota, cinto = (112, 26, 32), (84, 60, 44), (46, 34, 28), (96, 64, 32)

    if direcao in ("esquerda", "direita"):
        lado = -1 if direcao == "esquerda" else 1
        flutuar = int(abs(ciclo) * 3) if andando else 0
        pygame.draw.polygon(superficie, capa,
                            [(cx - lado * 3, cy - 5), (cx - lado * (10 + flutuar), cy + 3 - flutuar),
                             (cx - lado * (9 + flutuar), cy + 10), (cx - lado * 3, cy + 8)])
        for deslocamento in (perna, -perna):
            pygame.draw.rect(superficie, calca, (cx - 2 + deslocamento, cy + 6, 5, 7))
            pygame.draw.rect(superficie, bota, (cx - 2 + deslocamento, cy + 12, 6, 3))
        pygame.draw.rect(superficie, tunica, (cx - 5, cy - 5, 11, 12), border_radius=3)
        pygame.draw.rect(superficie, cinto, (cx - 5, cy + 2, 11, 3))
        pygame.draw.rect(superficie, (130, 30, 34), (cx - 1 - int(ciclo * 3), cy - 3, 4, 8))   # braço
        pygame.draw.circle(superficie, capuz, (cx, cy - 11), 8)
        pygame.draw.circle(superficie, pele, (cx + lado * 2, cy - 9), 6)
        pygame.draw.circle(superficie, (20, 20, 20), (cx + lado * 4, cy - 9), 1)
    elif direcao == "cima":
        _pernas(superficie, cx, cy, perna, calca, bota)
        pygame.draw.rect(superficie, capa, (cx - 9, cy - 5, 18, 14), border_radius=3)
        pygame.draw.line(superficie, (84, 18, 24), (cx, cy - 4), (cx, cy + 8), 1)
        pygame.draw.circle(superficie, capuz, (cx, cy - 10), 8)
        pygame.draw.circle(superficie, (36, 88, 50), (cx, cy - 9), 5)
    else:
        pygame.draw.polygon(superficie, capa,
                            [(cx - 10, cy - 5), (cx + 10, cy - 5), (cx + 11, cy + 10), (cx - 11, cy + 10)])
        _pernas(superficie, cx, cy, perna, calca, bota)
        pygame.draw.rect(superficie, tunica, (cx - 8, cy - 5, 16, 12), border_radius=3)
        pygame.draw.rect(superficie, cinto, (cx - 8, cy + 2, 16, 3))
        pygame.draw.rect(superficie, COR_OURO, (cx - 1, cy + 2, 3, 3))               # fivela
        pygame.draw.rect(superficie, pele, (cx - 11, cy - 4 - int(ciclo * 2), 3, 8))  # braços
        pygame.draw.rect(superficie, pele, (cx + 8, cy - 4 + int(ciclo * 2), 3, 8))
        pygame.draw.circle(superficie, capuz, (cx, cy - 11), 8)
        pygame.draw.circle(superficie, pele, (cx, cy - 9), 6)
        pygame.draw.circle(superficie, (20, 20, 20), (cx - 2, cy - 9), 1)
        pygame.draw.circle(superficie, (20, 20, 20), (cx + 2, cy - 9), 1)


def desenhar_esqueleto(superficie, retangulo, tempo, espelhar=False, perseguindo=False):
    """Esqueleto que balança, bate o queixo, tem olhos vermelhos brilhando e uma espada."""
    quadro = sprites.obter("esqueleto", tempo, espelhar)
    if quadro is not None:
        _blit_centralizado(superficie, quadro, retangulo.center)
        return
    cx, cy = retangulo.center
    desenhar_sombra(superficie, cx, cy + 14, 20)
    lado = -1 if espelhar else 1
    balanco = int(math.sin(tempo * 8) * 2)
    oscilar = int(math.sin(tempo * 4) * 1.5)
    osso, osso_escuro = (228, 223, 208), (170, 165, 150)
    pygame.draw.rect(superficie, osso, (cx - 6, cy + 6, 4, 8 + balanco))        # pernas
    pygame.draw.rect(superficie, osso, (cx + 2, cy + 6, 4, 8 - balanco))
    pygame.draw.rect(superficie, osso, (cx - 7 + oscilar, cy - 3, 14, 11), 2)   # costelas
    pygame.draw.line(superficie, osso, (cx - 7 + oscilar, cy + 1), (cx + 7 + oscilar, cy + 1), 1)
    pygame.draw.line(superficie, osso, (cx - 7 + oscilar, cy + 5), (cx + 7 + oscilar, cy + 5), 1)
    pygame.draw.line(superficie, osso_escuro, (cx + oscilar, cy - 3), (cx + oscilar, cy + 8), 1)
    braco = int(math.sin(tempo * 8 + 1) * 3)
    pygame.draw.line(superficie, osso, (cx + lado * 7 + oscilar, cy - 2),
                     (cx + lado * 12, cy + 3 + braco), 2)                       # braço da espada
    pygame.draw.line(superficie, (190, 195, 205), (cx + lado * 12, cy + 3 + braco),
                     (cx + lado * 13, cy - 9 + braco), 2)                        # lâmina
    pygame.draw.line(superficie, (120, 90, 50), (cx + lado * 10, cy + 3 + braco),
                     (cx + lado * 14, cy + 3 + braco), 2)                        # guarda
    cabeca_x = cx + oscilar
    pygame.draw.circle(superficie, osso, (cabeca_x, cy - 10), 8)                 # caveira
    mandibula = int(abs(math.sin(tempo * 5)) * 2)                                # queixo batendo
    pygame.draw.rect(superficie, osso, (cabeca_x - 4, cy - 5, 8, 3 + mandibula))
    pygame.draw.line(superficie, (40, 36, 40), (cabeca_x - 2, cy - 5), (cabeca_x - 2, cy - 3 + mandibula), 1)
    pygame.draw.line(superficie, (40, 36, 40), (cabeca_x + 2, cy - 5), (cabeca_x + 2, cy - 3 + mandibula), 1)
    pygame.draw.circle(superficie, (15, 10, 15), (cabeca_x - 3, cy - 11), 2)
    pygame.draw.circle(superficie, (15, 10, 15), (cabeca_x + 3, cy - 11), 2)
    brilho = int(150 + 80 * math.sin(tempo * 6))                                 # olhos brilhando
    pygame.draw.circle(superficie, (brilho, 30, 30), (cabeca_x - 3, cy - 11), 1)
    pygame.draw.circle(superficie, (brilho, 30, 30), (cabeca_x + 3, cy - 11), 1)


def _exclamacao(superficie, cx, y):
    """Sinal de alerta '!' sobre inimigos que perceberam o jogador."""
    pygame.draw.rect(superficie, COR_ALERTA, (cx - 1, y, 3, 8))
    pygame.draw.rect(superficie, COR_ALERTA, (cx - 1, y + 10, 3, 3))


def desenhar_goblin(superficie, retangulo, tempo, espelhar=False, perseguindo=False):
    """Goblin saltitante de orelhas que balançam; mostra '!' quando persegue."""
    quadro = sprites.obter("goblin", tempo, espelhar)
    if quadro is not None:
        _blit_centralizado(superficie, quadro, retangulo.center)
        return
    cx, cy = retangulo.center
    desenhar_sombra(superficie, cx, cy + 14, 20)
    lado = -1 if espelhar else 1
    velocidade = 13 if perseguindo else 9
    cy -= int(abs(math.sin(tempo * velocidade)) * (3 if perseguindo else 2))
    pele = (90, 160, 70)
    orelha = int(math.sin(tempo * 10) * 2)
    pygame.draw.rect(superficie, (90, 60, 30), (cx - 8, cy - 1, 16, 13), border_radius=3)
    pygame.draw.rect(superficie, (60, 40, 20), (cx - 8, cy + 5, 16, 3))          # cinto
    pygame.draw.rect(superficie, (70, 130, 55), (cx - 6, cy + 11, 4, 4))         # pés
    pygame.draw.rect(superficie, (70, 130, 55), (cx + 2, cy + 11, 4, 4))
    pygame.draw.line(superficie, (200, 205, 215), (cx + lado * 9, cy + 6),
                     (cx + lado * 15, cy - 2 + orelha), 2)                       # adaga
    pygame.draw.polygon(superficie, pele, [(cx - 7, cy - 9), (cx - 16, cy - 14 - orelha), (cx - 8, cy - 4)])
    pygame.draw.polygon(superficie, pele, [(cx + 7, cy - 9), (cx + 16, cy - 14 - orelha), (cx + 8, cy - 4)])
    pygame.draw.circle(superficie, pele, (cx, cy - 8), 9)
    olho = (255, 70, 70) if perseguindo else (230, 40, 40)
    raio_olho = 3 if perseguindo else 2
    pygame.draw.circle(superficie, olho, (cx - 3, cy - 9), raio_olho)
    pygame.draw.circle(superficie, olho, (cx + 3, cy - 9), raio_olho)
    pygame.draw.line(superficie, (20, 40, 15), (cx - 4, cy - 3), (cx + 4, cy - 3), 2)
    pygame.draw.line(superficie, (240, 240, 220), (cx - 3, cy - 3), (cx - 3, cy - 1), 1)   # presas
    pygame.draw.line(superficie, (240, 240, 220), (cx + 3, cy - 3), (cx + 3, cy - 1), 1)
    if perseguindo:
        _exclamacao(superficie, cx, cy - 31)


def desenhar_dragao(superficie, retangulo, tempo, espelhar=False, perseguindo=False):
    """Dragão com aura pulsante, asas batendo e chamas na boca quando persegue."""
    quadro = sprites.obter("dragao", tempo, espelhar)
    if quadro is not None:
        _blit_centralizado(superficie, quadro, retangulo.center)
        return
    cx, cy = retangulo.center
    desenhar_sombra(superficie, cx, cy + 17, 30)
    desenhar_halo(superficie, (cx, cy), 30, (255, 60, 30),
                  int(50 + 25 * math.sin(tempo * 5)) + (30 if perseguindo else 0))
    bater = int(math.sin(tempo * 6) * 5)
    corpo, escuro = (170, 30, 30), (110, 20, 25)
    pygame.draw.polygon(superficie, escuro,
                        [(cx - 6, cy - 2), (cx - 21, cy - 12 - bater), (cx - 17, cy - 2 - bater // 2),
                         (cx - 12, cy + 5)])
    pygame.draw.polygon(superficie, escuro,
                        [(cx + 6, cy - 2), (cx + 21, cy - 12 - bater), (cx + 17, cy - 2 - bater // 2),
                         (cx + 12, cy + 5)])
    pygame.draw.polygon(superficie, escuro, [(cx - 7, cy + 12), (cx, cy + 19 + bater // 3), (cx + 7, cy + 12)])
    pygame.draw.ellipse(superficie, corpo, (cx - 12, cy - 4, 24, 20))
    pygame.draw.ellipse(superficie, (205, 150, 70), (cx - 6, cy + 1, 12, 12))      # barriga
    pygame.draw.circle(superficie, corpo, (cx, cy - 8), 10)
    pygame.draw.polygon(superficie, (235, 225, 190), [(cx - 8, cy - 14), (cx - 12, cy - 22), (cx - 4, cy - 16)])
    pygame.draw.polygon(superficie, (235, 225, 190), [(cx + 8, cy - 14), (cx + 12, cy - 22), (cx + 4, cy - 16)])
    pygame.draw.circle(superficie, (255, 220, 40), (cx - 4, cy - 9), 2)
    pygame.draw.circle(superficie, (255, 220, 40), (cx + 4, cy - 9), 2)
    pygame.draw.rect(superficie, (40, 10, 10), (cx - 4, cy - 3, 8, 2))
    if perseguindo:                          # chamas saindo da boca
        chama = int(4 + abs(math.sin(tempo * 18)) * 5)
        pygame.draw.polygon(superficie, (255, 130, 30), [(cx - 3, cy - 2), (cx + 3, cy - 2), (cx, cy - 2 + chama + 3)])
        pygame.draw.polygon(superficie, (255, 220, 90), [(cx - 1, cy - 2), (cx + 1, cy - 2), (cx, cy - 2 + chama)])


# ----------------------------------------------------------------------
# Interface (HUD)
# ----------------------------------------------------------------------
def criar_fundo_hud():
    """Pré-renderiza o painel de pedra da barra superior."""
    fundo = pygame.Surface((LARGURA_JANELA, ALTURA_HUD))
    for yy in range(ALTURA_HUD):
        f = yy / ALTURA_HUD
        pygame.draw.line(fundo, (int(44 - 16 * f), int(36 - 14 * f), int(52 - 16 * f)),
                         (0, yy), (LARGURA_JANELA, yy))
    for xx in range(0, LARGURA_JANELA, 120):             # emendas das pedras
        pygame.draw.line(fundo, (26, 21, 32), (xx, 0), (xx, ALTURA_HUD - 3), 1)
    pygame.draw.line(fundo, (170, 126, 48), (0, ALTURA_HUD - 3), (LARGURA_JANELA, ALTURA_HUD - 3), 2)
    pygame.draw.line(fundo, (90, 66, 28), (0, ALTURA_HUD - 1), (LARGURA_JANELA, ALTURA_HUD - 1), 2)
    pygame.draw.line(fundo, (96, 90, 108), (0, 0), (LARGURA_JANELA, 0), 2)
    return fundo


def desenhar_coracao(superficie, x, y, cheio, pulso=0.0):
    """Coração de vida (cheio ou vazio). 'pulso' (0 a 1) faz o coração 'bater'."""
    cor = COR_VIDA if cheio else (70, 50, 60)
    r = 6 + int(pulso * 2)
    pygame.draw.circle(superficie, cor, (x + 6, y + 6), r)
    pygame.draw.circle(superficie, cor, (x + 16, y + 6), r)
    pygame.draw.polygon(superficie, cor, [(x - int(pulso * 2), y + 8), (x + 22 + int(pulso * 2), y + 8),
                                          (x + 11, y + 21 + int(pulso * 2))])
    if cheio:
        pygame.draw.circle(superficie, (255, 150, 150), (x + 4, y + 4), 2)          # reflexo


def desenhar_icone_moeda(superficie, x, y, tempo):
    """Ícone de moeda girando ao lado da pontuação."""
    cx, cy = x + 11, y + 11
    largura = max(3, int(abs(math.cos(tempo * 3)) * 9))
    pygame.draw.ellipse(superficie, COR_OURO, (cx - largura, cy - 9, largura * 2, 18))
    pygame.draw.ellipse(superficie, COR_OURO_ESCURO, (cx - largura, cy - 9, largura * 2, 18), 2)


def desenhar_icone_relogio(superficie, x, y, cor, tempo):
    """Ícone de relógio com ponteiro que gira."""
    cx, cy = x + 11, y + 11
    pygame.draw.circle(superficie, cor, (cx, cy), 10, 2)
    pygame.draw.line(superficie, cor, (cx, cy), (cx, cy - 6), 2)
    angulo = tempo * 2
    pygame.draw.line(superficie, cor, (cx, cy),
                     (cx + int(math.sin(angulo) * 7), cy - int(math.cos(angulo) * 7)), 1)


def desenhar_icone_chave(superficie, x, y, ativa):
    """Ícone de chave: dourado se já coletada, apagado se ainda não."""
    cor = COR_OURO if ativa else (84, 74, 64)
    pygame.draw.circle(superficie, cor, (x + 6, y + 11), 6, 3)
    pygame.draw.rect(superficie, cor, (x + 10, y + 10, 13, 3))
    pygame.draw.rect(superficie, cor, (x + 18, y + 12, 3, 5))