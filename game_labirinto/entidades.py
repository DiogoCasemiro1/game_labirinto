"""
Classes das entidades do jogo: Item, Labirinto, Jogador e inimigos.
Cada classe cuida da própria lógica (atualizar) e do próprio desenho (desenhar).
"""

import math
import random
from collections import deque

import pygame

from constantes import (
    ALTURA_HUD, ALTURA_JANELA, ARMADILHA, CHANCE_VIRAR, CHEFE, COR_FUNDO,
    DIRECOES, DISTANCIA_MIN_TOCHAS, ESQUELETO, GOBLIN, INICIO, LARGURA_JANELA,
    MARGEM_ARMADILHA, MAX_TOCHAS, TEMPO_ABERTURA_PORTA,
    MARGEM_HITBOX_INIMIGO, MARGEM_HITBOX_JOGADOR, PAREDE, PONTOS_MOEDA,
    PONTOS_TESOURO, RAIO_CHEFE, RAIO_PERSEGUICAO, SAIDA, SIMBOLO_PARA_TIPO,
    TAMANHO_CHEFE, TAMANHO_INIMIGO, TAMANHO_ITEM, TAMANHO_JOGADOR, TAMANHO_TILE,
    TEMPO_ARMADILHA_ALERTA, TEMPO_ARMADILHA_ATIVA, TEMPO_ARMADILHA_RECOLHIDA,
    TEMPO_INVULNERAVEL, TIPO_CHAVE, TIPO_MOEDA, TIPO_TESOURO, VELOCIDADE_JOGADOR,
    VIDAS_INICIAIS,
)
from desenho import (
    desenhar_armadilha, desenhar_bau, desenhar_chao, desenhar_chave,
    desenhar_dragao, desenhar_esqueleto, desenhar_goblin, desenhar_jogador,
    desenhar_moeda, desenhar_parede, desenhar_porta, desenhar_tocha,
)


# ----------------------------------------------------------------------
# ITEM: chave, moeda ou tesouro
# ----------------------------------------------------------------------
class Item:
    def __init__(self, tipo, x, y):
        self.tipo = tipo
        folga = (TAMANHO_TILE - TAMANHO_ITEM) // 2
        self.retangulo = pygame.Rect(x + folga, y + folga, TAMANHO_ITEM, TAMANHO_ITEM)
        self.defasagem = (x * 0.017 + y * 0.031) % 6.28   # cada item anima fora de sincronia

    @property
    def pontos(self):
        """Pontos que o item vale (a chave não vale pontos)."""
        if self.tipo == TIPO_MOEDA:
            return PONTOS_MOEDA
        if self.tipo == TIPO_TESOURO:
            return PONTOS_TESOURO
        return 0

    def desenhar(self, tela, tempo):
        tempo += self.defasagem
        if self.tipo == TIPO_MOEDA:
            desenhar_moeda(tela, self.retangulo.center, tempo)
        elif self.tipo == TIPO_CHAVE:
            desenhar_chave(tela, self.retangulo.center, tempo)
        else:
            desenhar_bau(tela, self.retangulo.center, tempo)


# ----------------------------------------------------------------------
# ARMADILHA: espinhos que sobem e descem num ciclo repetido
# ----------------------------------------------------------------------
class Armadilha:
    CICLO = TEMPO_ARMADILHA_RECOLHIDA + TEMPO_ARMADILHA_ATIVA

    def __init__(self, coluna, linha):
        x = coluna * TAMANHO_TILE
        y = ALTURA_HUD + linha * TAMANHO_TILE
        self.retangulo = pygame.Rect(x, y, TAMANHO_TILE, TAMANHO_TILE)
        # Cada armadilha começa num ponto diferente do ciclo (não ficam sincronizadas)
        self.relogio = (coluna * 0.37 + linha * 0.61) % self.CICLO

    @property
    def estado(self):
        """'recolhida', 'alerta' (prestes a subir) ou 'ativa' (causa dano)."""
        if self.relogio < TEMPO_ARMADILHA_RECOLHIDA - TEMPO_ARMADILHA_ALERTA:
            return "recolhida"
        if self.relogio < TEMPO_ARMADILHA_RECOLHIDA:
            return "alerta"
        return "ativa"

    @property
    def altura_espinhos(self):
        """Quanto os espinhos já subiram: 0 (escondidos) a 1 (totalmente para fora)."""
        if self.relogio < TEMPO_ARMADILHA_RECOLHIDA - TEMPO_ARMADILHA_ALERTA:
            return 0.0
        if self.relogio < TEMPO_ARMADILHA_RECOLHIDA:
            # no aviso, eles sobem só um pouquinho
            avanco = (self.relogio - (TEMPO_ARMADILHA_RECOLHIDA - TEMPO_ARMADILHA_ALERTA))
            return 0.2 + 0.2 * avanco / TEMPO_ARMADILHA_ALERTA
        tempo_ativa = self.relogio - TEMPO_ARMADILHA_RECOLHIDA
        if tempo_ativa < 0.1:                  # disparo rápido
            return 0.4 + 0.6 * tempo_ativa / 0.1
        return 1.0

    @property
    def area_dano(self):
        return self.retangulo.inflate(-MARGEM_ARMADILHA, -MARGEM_ARMADILHA)

    def atualizar(self, dt):
        self.relogio = (self.relogio + dt) % self.CICLO

    def desenhar(self, tela):
        desenhar_armadilha(tela, self.retangulo.x, self.retangulo.y, self.estado,
                           self.altura_espinhos, self.relogio)


# ----------------------------------------------------------------------
# LABIRINTO: guarda o mapa, as paredes, a porta e responde perguntas
# sobre o mapa (tile livre? qual o caminho até o jogador?)
# ----------------------------------------------------------------------
class Labirinto:
    def __init__(self, desenho):
        self.desenho = desenho
        self.paredes = []             # lista de pygame.Rect (usada nas colisões)
        self.itens = []               # itens encontrados no mapa
        self.armadilhas = []          # armadilhas de espinhos
        self.inimigos_iniciais = []   # (simbolo, coluna, linha) de cada inimigo
        self.posicao_inicial = (0, 0)
        self.porta = None             # Rect da porta de saída
        self.porta_aberta = False
        self.progresso_porta = 0.0    # 0 = fechada ... 1 = totalmente aberta (animação)
        self.tochas = []              # centros (x, y) das tochas nas paredes
        self._carregar()
        self._posicionar_tochas()
        self.superficie = self._pre_renderizar()

    def _carregar(self):
        """Lê o desenho do mapa e cria paredes, itens, inimigos, início e porta."""
        for linha, texto in enumerate(self.desenho):
            for coluna, simbolo in enumerate(texto):
                x = coluna * TAMANHO_TILE
                y = ALTURA_HUD + linha * TAMANHO_TILE
                if simbolo == PAREDE:
                    self.paredes.append(pygame.Rect(x, y, TAMANHO_TILE, TAMANHO_TILE))
                elif simbolo == INICIO:
                    self.posicao_inicial = (x, y)
                elif simbolo == SAIDA:
                    self.porta = pygame.Rect(x, y, TAMANHO_TILE, TAMANHO_TILE)
                elif simbolo in SIMBOLO_PARA_TIPO:
                    self.itens.append(Item(SIMBOLO_PARA_TIPO[simbolo], x, y))
                elif simbolo == ARMADILHA:
                    self.armadilhas.append(Armadilha(coluna, linha))
                elif simbolo in (ESQUELETO, GOBLIN, CHEFE):
                    self.inimigos_iniciais.append((simbolo, coluna, linha))

    def _eh_parede(self, coluna, linha):
        """True se o tile é parede (ou está fora do mapa)."""
        if linha < 0 or linha >= len(self.desenho):
            return True
        if coluna < 0 or coluna >= len(self.desenho[linha]):
            return True
        return self.desenho[linha][coluna] == PAREDE

    def _posicionar_tochas(self):
        """
        Escolhe, de forma fixa (sempre as mesmas para o mesmo mapa), paredes
        voltadas para um corredor onde pendurar tochas, sem deixá-las muito juntas.
        """
        candidatas = [(coluna, linha)
                      for linha, texto in enumerate(self.desenho)
                      for coluna, simbolo in enumerate(texto)
                      if simbolo == PAREDE and self.tile_livre(coluna, linha + 1)]
        candidatas.sort(key=lambda p: (p[0] * 7919 + p[1] * 104729) % 1009)
        escolhidas = []
        for coluna, linha in candidatas:
            if len(escolhidas) >= MAX_TOCHAS:
                break
            longe = all(math.hypot(coluna - c, linha - l) >= DISTANCIA_MIN_TOCHAS
                        for c, l in escolhidas)
            if longe:
                escolhidas.append((coluna, linha))
        self.tochas = [(c * TAMANHO_TILE + TAMANHO_TILE // 2,
                        ALTURA_HUD + l * TAMANHO_TILE + TAMANHO_TILE // 2 + 4)
                       for c, l in escolhidas]

    def _pre_renderizar(self):
        """Desenha paredes e chão UMA vez numa imagem (mais rápido por quadro)."""
        imagem = pygame.Surface((LARGURA_JANELA, ALTURA_JANELA))
        imagem.fill(COR_FUNDO)
        for linha, texto in enumerate(self.desenho):
            for coluna, simbolo in enumerate(texto):
                x = coluna * TAMANHO_TILE
                y = ALTURA_HUD + linha * TAMANHO_TILE
                if simbolo == PAREDE:
                    # Face de tijolos se houver chão logo abaixo; senão, topo da parede
                    face = not self._eh_parede(coluna, linha + 1)
                    variante = (coluna * 7 + linha * 13) % 8
                    bordas = (not self._eh_parede(coluna - 1, linha),
                              not self._eh_parede(coluna + 1, linha),
                              not self._eh_parede(coluna, linha - 1),
                              not self._eh_parede(coluna, linha + 1))
                    desenhar_parede(imagem, x, y, face, variante, bordas)
                else:
                    desenhar_chao(imagem, x, y, linha, coluna,
                                  self._eh_parede(coluna, linha - 1))
        return imagem

    def abrir_porta(self):
        self.porta_aberta = True

    def atualizar(self, dt):
        """Anima a abertura da porta."""
        if self.porta_aberta and self.progresso_porta < 1.0:
            self.progresso_porta = min(1.0, self.progresso_porta + dt / TEMPO_ABERTURA_PORTA)

    def desenhar(self, tela, tempo):
        tela.blit(self.superficie, (0, 0))
        # Porta e tochas são animadas: desenhadas a cada quadro
        desenhar_porta(tela, self.porta.x, self.porta.y, self.porta_aberta,
                       self.progresso_porta, tempo)
        for x, y in self.tochas:
            desenhar_tocha(tela, x, y, tempo, x + y)

    def colide_com_parede(self, retangulo):
        """True se o retângulo tocar numa parede ou na porta ainda trancada."""
        if retangulo.collidelist(self.paredes) != -1:
            return True
        return (not self.porta_aberta) and retangulo.colliderect(self.porta)

    # ---------- consultas em "coordenadas de tile" (coluna, linha) ----------
    def tile_livre(self, coluna, linha):
        """True se o tile existe e os inimigos podem andar nele."""
        if linha < 0 or linha >= len(self.desenho):
            return False
        if coluna < 0 or coluna >= len(self.desenho[linha]):
            return False
        return self.desenho[linha][coluna] not in (PAREDE, SAIDA)

    @staticmethod
    def tile_do_ponto(ponto):
        """Converte um ponto da tela (pixels) em (coluna, linha) do mapa."""
        x, y = ponto
        return int(x) // TAMANHO_TILE, int(y - ALTURA_HUD) // TAMANHO_TILE

    def caminho_bfs(self, origem, alvo, limite):
        """
        Busca em largura (BFS): menor caminho de 'origem' até 'alvo'.
        Retorna a lista de tiles a percorrer (sem incluir a origem) ou None
        se não houver caminho com no máximo 'limite' passos.
        """
        fila = deque([origem])
        anterior = {origem: None}
        profundidade = {origem: 0}
        while fila:
            atual = fila.popleft()
            if atual == alvo:
                break
            if profundidade[atual] >= limite:
                continue
            for d_coluna, d_linha in DIRECOES:
                vizinho = (atual[0] + d_coluna, atual[1] + d_linha)
                if vizinho not in anterior and self.tile_livre(*vizinho):
                    anterior[vizinho] = atual
                    profundidade[vizinho] = profundidade[atual] + 1
                    fila.append(vizinho)
        if alvo not in anterior:
            return None
        caminho = []
        no = alvo
        while no != origem:
            caminho.append(no)
            no = anterior[no]
        caminho.reverse()
        return caminho


# ----------------------------------------------------------------------
# JOGADOR
# ----------------------------------------------------------------------
class Jogador:
    def __init__(self):
        self.retangulo = pygame.Rect(0, 0, TAMANHO_JOGADOR, TAMANHO_JOGADOR)
        self.x = 0.0
        self.y = 0.0
        self.vidas = VIDAS_INICIAIS
        self.invulneravel_restante = 0.0
        self.direcao = "baixo"
        self.andando = False
        self.tempo_animacao = 0.0
        self.fator_velocidade = 1.0   # multiplicador de velocidade (poção do modo Perseguição)
        self.bloqueado = False        # True: ignora o teclado (loja aberta no modo Perseguição)

    @property
    def invulneravel(self):
        return self.invulneravel_restante > 0

    @property
    def hitbox(self):
        """Área sensível a dano: um pouco menor que o desenho."""
        return self.retangulo.inflate(-MARGEM_HITBOX_JOGADOR, -MARGEM_HITBOX_JOGADOR)

    def posicionar(self, posicao_tile):
        """Coloca o jogador no centro de um tile (início de cada fase)."""
        folga = (TAMANHO_TILE - TAMANHO_JOGADOR) // 2
        self.x = float(posicao_tile[0] + folga)
        self.y = float(posicao_tile[1] + folga)
        self.retangulo.topleft = (round(self.x), round(self.y))
        self.direcao = "baixo"
        self.andando = False

    def perder_vida(self):
        """Tira uma vida e ativa a invulnerabilidade temporária."""
        self.vidas -= 1
        self.invulneravel_restante = TEMPO_INVULNERAVEL

    def ler_teclado(self):
        """Retorna (dx, dy) conforme as teclas pressionadas (setas ou WASD)."""
        teclas = pygame.key.get_pressed()
        dx = dy = 0
        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            dx -= 1
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            dx += 1
        if teclas[pygame.K_UP] or teclas[pygame.K_w]:
            dy -= 1
        if teclas[pygame.K_DOWN] or teclas[pygame.K_s]:
            dy += 1
        return dx, dy

    def atualizar(self, dt, labirinto):
        """Move o jogador. dt = segundos desde o último quadro."""
        if self.invulneravel_restante > 0:
            self.invulneravel_restante = max(0.0, self.invulneravel_restante - dt)
        self.tempo_animacao += dt

        dx, dy = (0, 0) if self.bloqueado else self.ler_teclado()
        self.andando = (dx != 0 or dy != 0)
        if not self.andando:
            return

        # Diagonal não pode ser mais rápida: normaliza o vetor
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071

        if dx < 0:
            self.direcao = "esquerda"
        elif dx > 0:
            self.direcao = "direita"
        elif dy < 0:
            self.direcao = "cima"
        else:
            self.direcao = "baixo"

        passo = VELOCIDADE_JOGADOR * self.fator_velocidade * dt
        # Move e testa colisão em cada eixo separadamente:
        # assim o jogador "desliza" na parede em vez de ficar preso.
        self._mover_eixo(dx * passo, 0, labirinto)
        self._mover_eixo(0, dy * passo, labirinto)

    def _mover_eixo(self, mov_x, mov_y, labirinto):
        self.x += mov_x
        self.y += mov_y
        self.retangulo.x = round(self.x)
        self.retangulo.y = round(self.y)
        if labirinto.colide_com_parede(self.retangulo):
            # Desfaz o movimento deste eixo
            self.x -= mov_x
            self.y -= mov_y
            self.retangulo.x = round(self.x)
            self.retangulo.y = round(self.y)

    def desenhar(self, tela):
        # Piscar enquanto estiver invulnerável (some e aparece 10x por segundo)
        if self.invulneravel and int(self.invulneravel_restante * 10) % 2 == 0:
            return
        desenhar_jogador(tela, self.retangulo, self.direcao,
                         self.tempo_animacao, self.andando)


# ----------------------------------------------------------------------
# INIMIGOS
# Os inimigos andam "de tile em tile": ao chegar ao centro de um tile,
# escolhem o próximo tile de destino. O que muda entre os tipos é apenas
# COMO escolhem (método escolher_destino) -> polimorfismo.
# ----------------------------------------------------------------------
class Inimigo:
    tamanho = TAMANHO_INIMIGO     # cada tipo pode ter seu próprio tamanho
    perseguindo = False           # True quando está indo atrás do jogador (afeta a animação)

    def __init__(self, coluna, linha, velocidade):
        self.coluna = coluna          # tile em que o inimigo está
        self.linha = linha
        self.velocidade = velocidade  # pixels por segundo
        self.destino = (coluna, linha)
        self.direcao = (0, 0)         # (delta_coluna, delta_linha) atual
        self.tempo_animacao = random.uniform(0, 6)  # desincroniza animações
        self.x, self.y = self._posicao_do_tile(coluna, linha)
        self.retangulo = pygame.Rect(round(self.x), round(self.y),
                                     self.tamanho, self.tamanho)

    def _posicao_do_tile(self, coluna, linha):
        """Canto superior esquerdo do inimigo quando centralizado no tile."""
        folga = (TAMANHO_TILE - self.tamanho) // 2
        return (coluna * TAMANHO_TILE + folga,
                ALTURA_HUD + linha * TAMANHO_TILE + folga)

    @property
    def hitbox(self):
        """Área que causa dano: um pouco menor que o desenho."""
        return self.retangulo.inflate(-MARGEM_HITBOX_INIMIGO, -MARGEM_HITBOX_INIMIGO)

    def escolher_destino(self, labirinto, jogador):
        """Retorna o próximo tile (coluna, linha). Cada tipo de inimigo implementa."""
        raise NotImplementedError

    def atualizar(self, dt, labirinto, jogador):
        self.tempo_animacao += dt
        alvo_x, alvo_y = self._posicao_do_tile(*self.destino)
        falta_x = alvo_x - self.x
        falta_y = alvo_y - self.y
        distancia = math.hypot(falta_x, falta_y)
        passo = self.velocidade * dt
        if distancia <= passo:
            # Chegou ao tile de destino: encaixa e decide para onde ir agora
            self.x, self.y = alvo_x, alvo_y
            self.coluna, self.linha = self.destino
            self.destino = self.escolher_destino(labirinto, jogador)
        else:
            self.x += falta_x / distancia * passo
            self.y += falta_y / distancia * passo
        self.retangulo.topleft = (round(self.x), round(self.y))

    def desenhar(self, tela):
        raise NotImplementedError


class Esqueleto(Inimigo):
    """Patrulheiro: segue reto pelo corredor e escolhe outro rumo ao bater na parede."""

    def escolher_destino(self, labirinto, jogador):
        atras = (-self.direcao[0], -self.direcao[1])
        opcoes = [d for d in DIRECOES
                  if d != atras and labirinto.tile_livre(self.coluna + d[0],
                                                         self.linha + d[1])]
        if opcoes:
            continuar = self.direcao in opcoes
            # Segue em frente, mas às vezes vira num cruzamento
            if continuar and random.random() > CHANCE_VIRAR:
                nova = self.direcao
            else:
                nova = random.choice(opcoes)
        elif labirinto.tile_livre(self.coluna + atras[0], self.linha + atras[1]):
            nova = atras             # beco sem saída: dá meia-volta
        else:
            return (self.coluna, self.linha)   # cercado: fica parado
        self.direcao = nova
        return (self.coluna + nova[0], self.linha + nova[1])

    def desenhar(self, tela):
        desenhar_esqueleto(tela, self.retangulo, self.tempo_animacao,
                           self.direcao[0] < 0)


class Goblin(Esqueleto):
    """
    Perseguidor: se o jogador estiver ao alcance, segue o menor caminho até ele
    (BFS). Se não estiver, patrulha como o esqueleto (herança).
    """
    raio_percepcao = RAIO_PERSEGUICAO

    def escolher_destino(self, labirinto, jogador):
        origem = (self.coluna, self.linha)
        alvo = labirinto.tile_do_ponto(jogador.retangulo.center)
        caminho = labirinto.caminho_bfs(origem, alvo, self.raio_percepcao)
        if caminho:
            self.perseguindo = True
            proximo = caminho[0]
            self.direcao = (proximo[0] - origem[0], proximo[1] - origem[1])
            return proximo
        self.perseguindo = False
        return super().escolher_destino(labirinto, jogador)

    def desenhar(self, tela):
        desenhar_goblin(tela, self.retangulo, self.tempo_animacao,
                        self.direcao[0] < 0, self.perseguindo)


class Dragao(Goblin):
    """Chefe da última fase: maior, mais rápido e percebe o jogador de bem mais longe."""
    tamanho = TAMANHO_CHEFE
    raio_percepcao = RAIO_CHEFE

    def desenhar(self, tela):
        desenhar_dragao(tela, self.retangulo, self.tempo_animacao,
                        self.direcao[0] < 0, self.perseguindo)