"""Piloto automático para os testes: leva o jogador até um tile usando o BFS do Labirinto."""

TILE = 40
HUD = 80


def centro(tile):
    return tile[0] * TILE + TILE // 2, HUD + tile[1] * TILE + TILE // 2


def tile_de(ponto):
    return int(ponto[0]) // TILE, int(ponto[1] - HUD) // TILE


def direcao_para(labirinto, jogador, alvo_tile, alvo_pixel=None):
    """(dx, dy) para seguir o menor caminho até alvo_tile (e depois até alvo_pixel)."""
    cx, cy = jogador.retangulo.center
    atual = tile_de((cx, cy))
    if atual == alvo_tile or not labirinto.tile_livre(*atual):
        destino = alvo_pixel or centro(alvo_tile)
    else:
        caminho = labirinto.caminho_bfs(atual, alvo_tile, 400)
        if not caminho:
            destino = alvo_pixel or centro(alvo_tile)
        else:
            proximo = caminho[0]
            ax, ay = centro(atual)
            # alinha no eixo perpendicular antes de virar (evita raspar nas quinas)
            if proximo[0] != atual[0] and abs(cy - ay) > 2:
                destino = (cx, ay)
            elif proximo[1] != atual[1] and abs(cx - ax) > 2:
                destino = (ax, cy)
            else:
                destino = centro(proximo)
    dx = 0 if abs(destino[0] - cx) <= 1 else (1 if destino[0] > cx else -1)
    dy = 0 if abs(destino[1] - cy) <= 1 else (1 if destino[1] > cy else -1)
    return dx, dy


def frente_da_porta(labirinto):
    porta = tile_de(labirinto.porta.center)
    for dc, dl in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        if labirinto.tile_livre(porta[0] + dc, porta[1] + dl):
            return (porta[0] + dc, porta[1] + dl)
    return porta


def objetivo(labirinto, itens):
    """Tile da chave restante ou, sem chave no mapa, a frente da porta."""
    for item in itens:
        if item.tipo == "chave":
            return tile_de(item.retangulo.center), None
    return frente_da_porta(labirinto), labirinto.porta.center
