"""
Efeitos visuais: partículas, textos flutuantes, iluminação e vinheta.
Nada aqui altera as regras do jogo: é só "maquiagem" animada.
"""

import math
import random

import pygame

from constantes import (
    ALTURA_JANELA, COR_TOCHA, LARGURA_JANELA, MAX_PARTICULAS,
    RAIO_LUZ_JOGADOR, RAIO_LUZ_TOCHA,
)


class Particula:
    """Um pontinho colorido que se move, perde velocidade e encolhe até sumir."""

    def __init__(self, x, y, vx, vy, vida, cor, tamanho, gravidade=0.0, atrito=0.0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.vida = vida
        self.vida_total = vida
        self.cor = cor
        self.tamanho = tamanho
        self.gravidade = gravidade
        self.atrito = atrito

    @property
    def viva(self):
        return self.vida > 0

    def atualizar(self, dt):
        self.vida -= dt
        self.vy += self.gravidade * dt
        fator = max(0.0, 1.0 - self.atrito * dt)
        self.vx *= fator
        self.vy *= fator
        self.x += self.vx * dt
        self.y += self.vy * dt

    def desenhar(self, tela):
        raio = max(1, round(self.tamanho * self.vida / self.vida_total))
        pygame.draw.circle(tela, self.cor, (int(self.x), int(self.y)), raio)


class TextoFlutuante:
    """Texto (ex.: '+10') que sobe e desaparece."""

    def __init__(self, x, y, texto, cor, vida=1.0):
        self.x = x
        self.y = y
        self.texto = texto
        self.cor = cor
        self.vida = vida
        self.vida_total = vida

    @property
    def vivo(self):
        return self.vida > 0

    def atualizar(self, dt):
        self.vida -= dt
        self.y -= 36 * dt

    def desenhar(self, tela, fonte):
        transparencia = max(0.0, min(1.0, self.vida / (self.vida_total * 0.5)))
        sombra = fonte.render(self.texto, True, (0, 0, 0))
        imagem = fonte.render(self.texto, True, self.cor)
        sombra.set_alpha(int(255 * transparencia))
        imagem.set_alpha(int(255 * transparencia))
        centro = (int(self.x), int(self.y))
        tela.blit(sombra, sombra.get_rect(center=(centro[0] + 1, centro[1] + 1)))
        tela.blit(imagem, imagem.get_rect(center=centro))


class SistemaParticulas:
    """Cria, atualiza e desenha todas as partículas e textos do jogo."""

    def __init__(self):
        self.particulas = []
        self.textos = []

    def limpar(self):
        self.particulas = []
        self.textos = []

    def _adicionar(self, particula):
        if len(self.particulas) < MAX_PARTICULAS:
            self.particulas.append(particula)

    def explosao(self, x, y, cores, quantidade=14, velocidade=110, vida=0.55):
        """Jato de partículas em todas as direções (coleta de itens, dano...)."""
        for _ in range(quantidade):
            angulo = random.uniform(0, 2 * math.pi)
            rapidez = random.uniform(0.3, 1.0) * velocidade
            self._adicionar(Particula(
                x, y, math.cos(angulo) * rapidez, math.sin(angulo) * rapidez,
                random.uniform(0.6, 1.0) * vida, random.choice(cores),
                random.randint(2, 4), gravidade=160, atrito=2.0))

    def poeira(self, x, y):
        """Nuvenzinha de poeira atrás dos pés de quem anda."""
        self._adicionar(Particula(
            x + random.uniform(-4, 4), y, random.uniform(-14, 14),
            random.uniform(-18, -6), 0.35, (128, 120, 134), 3, atrito=3.0))

    def brasa(self, x, y):
        """Faísca que sobe de uma tocha."""
        cor = random.choice([COR_TOCHA, (255, 120, 40), (255, 220, 120)])
        self._adicionar(Particula(
            x + random.uniform(-3, 3), y, random.uniform(-8, 8),
            random.uniform(-40, -20), random.uniform(0.6, 1.1), cor, 2))

    def texto(self, x, y, texto, cor):
        self.textos.append(TextoFlutuante(x, y, texto, cor))

    def atualizar(self, dt):
        for particula in self.particulas:
            particula.atualizar(dt)
        self.particulas = [p for p in self.particulas if p.viva]
        for texto in self.textos:
            texto.atualizar(dt)
        self.textos = [t for t in self.textos if t.vivo]

    def desenhar(self, tela, fonte):
        for particula in self.particulas:
            particula.desenhar(tela)
        for texto in self.textos:
            texto.desenhar(tela, fonte)


def _criar_luz(raio):
    """Círculo de luz: opaco no centro e transparente na borda (usado para 'furar' a escuridão)."""
    luz = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
    for r in range(raio, 0, -2):
        proximidade = 1 - r / raio                       # 0 na borda, 1 no centro
        alfa = min(255, int(255 * proximidade * 1.6))    # centro mais "chapado"
        pygame.draw.circle(luz, (255, 255, 255, alfa), (raio, raio), r)
    return luz


def _criar_brilho(raio, cor, alfa_maximo):
    """Halo colorido suave (o clarão alaranjado das tochas)."""
    brilho = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
    for r in range(raio, 0, -2):
        alfa = int(alfa_maximo * (1 - r / raio) ** 1.5)
        pygame.draw.circle(brilho, (cor[0], cor[1], cor[2], alfa), (raio, raio), r)
    return brilho


def criar_vinheta():
    """Cantos da tela levemente escurecidos, para dar clima."""
    vinheta = pygame.Surface((LARGURA_JANELA, ALTURA_JANELA), pygame.SRCALPHA)
    vinheta.fill((0, 0, 0, 120))
    passos = 22
    for i in range(passos):
        fracao = i / (passos - 1)
        alfa = int(120 * (1 - fracao) ** 1.6)
        largura = int(LARGURA_JANELA * 1.45 * (1 - fracao * 0.78))
        altura = int(ALTURA_JANELA * 1.45 * (1 - fracao * 0.78))
        retangulo = pygame.Rect(0, 0, largura, altura)
        retangulo.center = (LARGURA_JANELA // 2, ALTURA_JANELA // 2)
        pygame.draw.ellipse(vinheta, (0, 0, 0, alfa), retangulo)
    return vinheta


class Iluminacao:
    """
    Escurece a masmorra e "fura" a escuridão ao redor do jogador e das tochas.
    As tochas cintilam: a cada instante usam um raio de luz ligeiramente diferente.
    """

    DESLOCAMENTO_TOCHA = 16   # a luz da tocha fica um pouco abaixo da chama

    def __init__(self):
        self.escuridao = pygame.Surface((LARGURA_JANELA, ALTURA_JANELA), pygame.SRCALPHA)
        self.luz_jogador = _criar_luz(RAIO_LUZ_JOGADOR)
        self.luzes_tocha = [_criar_luz(RAIO_LUZ_TOCHA + d) for d in (-8, -3, 2, 7)]
        self.brilho_tocha = _criar_brilho(RAIO_LUZ_TOCHA - 20, COR_TOCHA, 60)

    def _furar(self, luz, centro):
        raio = luz.get_width() // 2
        self.escuridao.blit(luz, (centro[0] - raio, centro[1] - raio),
                            special_flags=pygame.BLEND_RGBA_SUB)

    def desenhar(self, cena, centro_jogador, tochas, tempo, nivel_escuridao):
        # 1) clarão alaranjado ao redor das tochas
        raio_brilho = self.brilho_tocha.get_width() // 2
        for x, y in tochas:
            cena.blit(self.brilho_tocha,
                      (x - raio_brilho, y + self.DESLOCAMENTO_TOCHA - raio_brilho))
        # 2) escuridão com buracos de luz
        self.escuridao.fill((0, 0, 0, nivel_escuridao))
        self._furar(self.luz_jogador, centro_jogador)
        for x, y in tochas:
            cintilar = int((math.sin(tempo * 9 + x * 0.13) + 1) * 1.99)   # 0..3
            self._furar(self.luzes_tocha[cintilar], (x, y + self.DESLOCAMENTO_TOCHA))
        cena.blit(self.escuridao, (0, 0))