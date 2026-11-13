"""
Guardião das Trevas: o perseguidor do modo Perseguição.

Reaproveita a hierarquia de inimigos de entidades.py:
  Inimigo   -> anda de tile em tile (nunca atravessa paredes)
  Esqueleto -> patrulha (usada quando o Guardião não tem rastro)
  Guardiao  -> IA em três estágios usando o BFS existente (Labirinto.caminho_bfs)

O BFS NÃO roda a cada quadro: a percepção é refeita a cada INTERVALO_PERCEPCAO
segundos e o caminho encontrado é seguido passo a passo.
"""

import random

from constantes import (
    ESTAGIO_CACADA, ESTAGIO_FURIA, ESTAGIO_VIGILANCIA, IMUNIDADE_ARMADILHA,
    INTERVALO_PERCEPCAO, INTERVALO_PISTA, LIMITE_BFS_TOTAL,
    MARGEM_HITBOX_GUARDIAO, PROGRESSAO_VELOCIDADE_GUARDIAO, RAIO_DETECCAO_GUARDIAO,
    RAIO_PERDA_GUARDIAO, RAIO_PISTA, TAMANHO_GUARDIAO, TEMPO_DESPERTAR,
    TEMPO_FURIA, TEMPO_PERDER_RASTRO, VELOCIDADE_GUARDIAO,
)
from desenho_perseguicao import desenhar_guardiao
from entidades import Esqueleto


def fator_velocidade_guardiao(tempo_partida):
    """Multiplicador de velocidade conforme o tempo (tabela em constantes.py)."""
    fator = 1.0
    for inicio, multiplicador in PROGRESSAO_VELOCIDADE_GUARDIAO:
        if tempo_partida >= inicio:
            fator = multiplicador
    return fator


class Guardiao(Esqueleto):
    tamanho = TAMANHO_GUARDIAO

    def __init__(self, coluna, linha, velocidade=VELOCIDADE_GUARDIAO):
        super().__init__(coluna, linha, velocidade)
        self.velocidade_base = velocidade
        self.estagio = ESTAGIO_VIGILANCIA
        self.caminho = []               # próximos tiles a percorrer
        self.ciente = False             # sabe onde o jogador está neste momento
        self.ultimo_local = None        # último tile em que viu o jogador
        self.ponto_busca = None         # tile que está investigando (vigilância)
        self.tempo_percepcao = 0.0
        self.tempo_pista = INTERVALO_PISTA
        self.tempo_sem_ver = 0.0
        self.dormindo = TEMPO_DESPERTAR
        self.atordoado = 0.0
        self.imune_armadilha = 0.0
        self.eventos = []               # 'despertou', 'detectou', 'perdeu', 'furia'
        self.rng = random.Random()

    # ------------------------------------------------------------------
    @property
    def hitbox(self):
        return self.retangulo.inflate(-MARGEM_HITBOX_GUARDIAO, -MARGEM_HITBOX_GUARDIAO)

    @property
    def ativo(self):
        """False enquanto dorme ou está atordoado (não se move nem captura)."""
        return self.dormindo <= 0 and self.atordoado <= 0

    @property
    def tile(self):
        return (self.coluna, self.linha)

    def teleportar(self, coluna, linha, tempo_dormir=0.0):
        """Reposiciona o Guardião (início da partida ou após uma captura)."""
        self.coluna, self.linha = coluna, linha
        self.destino = (coluna, linha)
        self.direcao = (0, 0)
        self.x, self.y = self._posicao_do_tile(coluna, linha)
        self.retangulo.topleft = (round(self.x), round(self.y))
        self.caminho = []
        self.ciente = False
        self.ponto_busca = None
        self.tempo_sem_ver = 0.0
        self.tempo_pista = INTERVALO_PISTA
        self.dormindo = tempo_dormir
        self.atordoado = 0.0
        if self.estagio != ESTAGIO_FURIA:
            self.estagio = ESTAGIO_VIGILANCIA

    def atordoar(self, segundos):
        self.atordoado = max(self.atordoado, segundos)
        self.caminho = []

    def pisou_em_armadilha(self, segundos):
        """Espinhos atrasam o Guardião (com imunidade para não travá-lo sempre)."""
        if self.imune_armadilha > 0 or not self.ativo:
            return False
        self.atordoar(segundos)
        self.imune_armadilha = segundos + IMUNIDADE_ARMADILHA
        return True

    # ------------------------------------------------------------------
    def atualizar_perseguicao(self, dt, labirinto, jogador, tempo_partida,
                              alvo_jogador, detectavel):
        """
        alvo_jogador: tile livre (coluna, linha) em que o jogador está.
        detectavel:   False se o jogador estiver invisível ou escondido.
        """
        self.eventos = []
        self.velocidade = self.velocidade_base * fator_velocidade_guardiao(tempo_partida)
        if tempo_partida >= TEMPO_FURIA and self.estagio != ESTAGIO_FURIA:
            self.estagio = ESTAGIO_FURIA
            self.eventos.append("furia")
        self.imune_armadilha = max(0.0, self.imune_armadilha - dt)
        if self.dormindo > 0:
            self.tempo_animacao += dt
            self.dormindo -= dt
            if self.dormindo <= 0:
                self.dormindo = 0.0
                self.tempo_percepcao = 0.0
                self.eventos.append("despertou")
            return
        if self.atordoado > 0:
            self.tempo_animacao += dt
            self.atordoado = max(0.0, self.atordoado - dt)
            return

        self.tempo_percepcao -= dt
        if self.tempo_percepcao <= 0:
            self.tempo_percepcao = INTERVALO_PERCEPCAO
            self._perceber(labirinto, alvo_jogador, detectavel)
        if not self.ciente:
            self.tempo_pista -= dt
            if self.tempo_pista <= 0:
                self.tempo_pista = INTERVALO_PISTA
                if detectavel:
                    self._ouvir_pista(labirinto, alvo_jogador)
        # Movimento de tile em tile herdado de Inimigo (chama escolher_destino)
        super().atualizar(dt, labirinto, jogador)

    def _perder_rastro(self):
        self.ciente = False
        self.ponto_busca = self.ultimo_local      # vai investigar onde o viu por último
        self.caminho = []
        if self.estagio == ESTAGIO_CACADA:
            self.estagio = ESTAGIO_VIGILANCIA
            self.eventos.append("perdeu")

    def _perceber(self, labirinto, alvo, detectavel):
        """Procura o jogador com o BFS existente; o raio depende do estágio."""
        if not detectavel or alvo is None:
            if self.ciente or self.estagio == ESTAGIO_CACADA:
                self._perder_rastro()
            return
        origem = self.destino            # tile para onde já está indo
        if self.estagio == ESTAGIO_VIGILANCIA:
            raio = RAIO_DETECCAO_GUARDIAO
        elif self.estagio == ESTAGIO_CACADA:
            raio = RAIO_PERDA_GUARDIAO
        else:
            raio = LIMITE_BFS_TOTAL       # na fúria, ele sempre sabe onde você está
        caminho = labirinto.caminho_bfs(origem, alvo, raio)
        if caminho is not None:
            self.caminho = caminho
            self.ciente = True
            self.ultimo_local = alvo
            self.ponto_busca = None
            self.tempo_sem_ver = 0.0
            if self.estagio == ESTAGIO_VIGILANCIA:
                self.estagio = ESTAGIO_CACADA
                self.eventos.append("detectou")
            return
        if self.estagio == ESTAGIO_CACADA:
            # Ainda segue o rastro por um tempo antes de desistir
            self.tempo_sem_ver += INTERVALO_PERCEPCAO
            if self.tempo_sem_ver >= TEMPO_PERDER_RASTRO:
                self._perder_rastro()
            else:
                self.caminho = labirinto.caminho_bfs(origem, alvo, LIMITE_BFS_TOTAL) or []
                self.ultimo_local = alvo
        else:
            self.ciente = False

    def _ouvir_pista(self, labirinto, alvo):
        """Vigilância: 'ouve' um ruído perto do jogador e vai investigar (sem precisão)."""
        if alvo is None:
            return
        opcoes = []
        for dc in range(-RAIO_PISTA, RAIO_PISTA + 1):
            for dl in range(-RAIO_PISTA, RAIO_PISTA + 1):
                if abs(dc) + abs(dl) <= RAIO_PISTA and \
                        labirinto.tile_livre(alvo[0] + dc, alvo[1] + dl):
                    opcoes.append((alvo[0] + dc, alvo[1] + dl))
        if opcoes:
            self.ponto_busca = self.rng.choice(opcoes)
            self.caminho = []

    # ------------------------------------------------------------------
    def _seguir(self, origem, labirinto):
        """Dá o próximo passo do caminho, se ele for válido (vizinho e livre)."""
        while self.caminho and self.caminho[0] == origem:
            self.caminho.pop(0)
        if not self.caminho:
            return None
        proximo = self.caminho[0]
        vizinho = abs(proximo[0] - origem[0]) + abs(proximo[1] - origem[1]) == 1
        if not (vizinho and labirinto.tile_livre(*proximo)):
            return None
        self.caminho.pop(0)
        self.direcao = (proximo[0] - origem[0], proximo[1] - origem[1])
        return proximo

    def escolher_destino(self, labirinto, jogador):
        origem = (self.coluna, self.linha)
        proximo = self._seguir(origem, labirinto)
        if proximo is None and self.caminho:
            # caminho desatualizado: recalcula até o mesmo alvo a partir daqui
            self.caminho = labirinto.caminho_bfs(origem, self.caminho[-1], LIMITE_BFS_TOTAL) or []
            proximo = self._seguir(origem, labirinto)
        if proximo is None and self.ponto_busca is not None:
            if self.ponto_busca == origem:
                self.ponto_busca = None
            else:
                self.caminho = labirinto.caminho_bfs(origem, self.ponto_busca,
                                                     LIMITE_BFS_TOTAL) or []
                proximo = self._seguir(origem, labirinto)
                if proximo is None:
                    self.ponto_busca = None
        if proximo is not None:
            return proximo
        # Sem rastro: patrulha como o esqueleto (nunca fica parado num corredor)
        return super().escolher_destino(labirinto, jogador)

    def desenhar(self, tela):
        desenhar_guardiao(tela, self.retangulo, self.tempo_animacao, self.direcao[0] < 0,
                          self.estagio, self.atordoado > 0, self.dormindo > 0)
