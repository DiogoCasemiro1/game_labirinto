"""
Carregamento OPCIONAL de sprites (imagens PNG).

Regra de ouro: o jogo NUNCA depende dos arquivos. Para cada sprite:
  - se a imagem existir em assets/imagens/, ela é usada;
  - se não existir, o desenho geométrico padrão (desenho.py) é usado.

Convenção de nomes (pasta assets/imagens/):
  nome.png                    -> imagem única
  nome_1.png, nome_2.png ...  -> quadros de uma animação (em ordem)
Também é possível apontar arquivos com outros nomes em MAPEAMENTO_ARQUIVOS.
"""

import os

import pygame

from constantes import (
    FPS_ANIMACAO, TAMANHO_SPRITE_CHEFE, TAMANHO_SPRITE_ITEM,
    TAMANHO_SPRITE_PERSONAGEM, TAMANHO_TILE,
)

PASTA_IMAGENS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "assets", "imagens")

_TILE = (TAMANHO_TILE, TAMANHO_TILE)
_PERSONAGEM = (TAMANHO_SPRITE_PERSONAGEM, TAMANHO_SPRITE_PERSONAGEM)
_CHEFE = (TAMANHO_SPRITE_CHEFE, TAMANHO_SPRITE_CHEFE)
_ITEM = (TAMANHO_SPRITE_ITEM, TAMANHO_SPRITE_ITEM)

# nome do sprite -> tamanho final na tela (largura, altura)
SPRITES_ESPERADOS = {
    "parede": _TILE,
    "chao": _TILE,
    "porta_fechada": _TILE,
    "porta_aberta": _TILE,
    "espinhos_baixo": _TILE,      # armadilha recolhida
    "espinhos_cima": _TILE,       # armadilha ativa
    "chave": _ITEM,
    "moeda": _ITEM,
    "bau": _ITEM,
    "jogador": _PERSONAGEM,       # parado
    "jogador_andando": _PERSONAGEM,
    "esqueleto": _PERSONAGEM,
    "goblin": _PERSONAGEM,
    "dragao": _CHEFE,
    "guardiao": _CHEFE,           # Guardião das Trevas (modo Perseguição)
}

# Para usar arquivos com OUTROS nomes, preencha aqui (caminhos dentro de assets/imagens).
# Exemplo:  "moeda": ["props/coin_1.png", "props/coin_2.png"],
MAPEAMENTO_ARQUIVOS = {}


def _caminhos_do_sprite(nome):
    """Lista os arquivos (um por quadro) que formam o sprite 'nome'."""
    if nome in MAPEAMENTO_ARQUIVOS:
        return [os.path.join(PASTA_IMAGENS, arq) for arq in MAPEAMENTO_ARQUIVOS[nome]]
    unico = os.path.join(PASTA_IMAGENS, nome + ".png")
    if os.path.isfile(unico):
        return [unico]
    caminhos = []
    numero = 1
    while True:
        caminho = os.path.join(PASTA_IMAGENS, f"{nome}_{numero}.png")
        if not os.path.isfile(caminho):
            break
        caminhos.append(caminho)
        numero += 1
    return caminhos


class Sprites:
    """Guarda as imagens carregadas e entrega o quadro certo para cada momento."""

    def __init__(self):
        self.quadros = {}       # nome -> lista de Surfaces
        self.espelhados = {}    # nome -> lista de Surfaces viradas para a esquerda

    def carregar(self):
        """Tenta carregar todos os sprites. Retorna (carregados, ausentes)."""
        carregados, ausentes = [], []
        for nome, tamanho in SPRITES_ESPERADOS.items():
            caminhos = _caminhos_do_sprite(nome)
            lista = self._carregar_quadros(caminhos, tamanho)
            if lista:
                self.quadros[nome] = lista
                carregados.append(nome)
            else:
                ausentes.append(nome)
        return carregados, ausentes

    @staticmethod
    def _carregar_quadros(caminhos, tamanho):
        """Carrega e redimensiona os arquivos. Qualquer erro cancela este sprite."""
        lista = []
        for caminho in caminhos:
            try:
                imagem = pygame.image.load(caminho).convert_alpha()
            except (pygame.error, FileNotFoundError, OSError):
                print(f"Aviso: não foi possível carregar {caminho}")
                return []
            # scale (sem suavização) preserva o visual de pixel art
            lista.append(pygame.transform.scale(imagem, tamanho))
        return lista

    def tem(self, nome):
        return nome in self.quadros

    def obter(self, nome, tempo=0.0, espelhar=False):
        """Retorna o quadro atual do sprite, ou None se ele não foi carregado."""
        lista = self.quadros.get(nome)
        if not lista:
            return None
        if espelhar:
            if nome not in self.espelhados:
                self.espelhados[nome] = [pygame.transform.flip(q, True, False)
                                         for q in lista]
            lista = self.espelhados[nome]
        indice = int(tempo * FPS_ANIMACAO) % len(lista)
        return lista[indice]


# Instância única usada por todo o jogo
sprites = Sprites()