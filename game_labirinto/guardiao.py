"""
Guardião das Trevas: o perseguidor do modo Perseguição.

Reaproveita a classe Inimigo/Esqueleto de entidades.py (movimento de tile em
tile, hitbox, patrulha) e o Labirinto.caminho_bfs() para achar o caminho.
"""

from constantes_perseguicao import (
    ESTAGIO_CACADA, ESTAGIO_FURIA, ESTAGIO_VIGILANCIA, INTERVALO_BUSCA,
    LIMITE_BFS, PROGRESSAO_VELOCIDADE, RAIO_DETECCAO, RAIO_PERDA,
    TAMANHO_GUARDIAO, TEMPO_FURIA, TEMPO_PERDA_JOGADOR,
    VELOCIDADE_BASE_GUARDIAO, VELOCIDADE_MAXIMA_GUARDIAO,
)
from desenho_perseguicao import desenhar_guardiao
from entidades import Esqueleto


def multiplicador_de_velocidade(tempo):
    """Fator de velocidade do Guardião conforme o tempo de partida (tabela configurável)."""
    fator = PROGRESSAO_VELOCIDADE[0][1]
    for segundos, valor in PROGRESSAO_VELOCIDADE:
        if tempo >= segundos:
            fator = valor
    return fator


class GuardiaoDasTrevas(Esqueleto):
    """
    Três estágios:
      VIGILÂNCIA - patrulha o labirinto procurando o jogador;
      CAÇADA     - percebeu o jogador e o persegue pelo menor caminho (BFS);
      FÚRIA      - passados TEMPO_FURIA segundos, persegue sem nunca desistir.
    A velocidade cresce com o tempo (ver PROGRESSAO_VELOCIDADE).
    """

    tamanho = TAMANHO_GUARDIAO

    def __init__(self, coluna, linha):
        super().__init__(coluna, linha, VELOCIDADE_BASE_GUARDIAO)
        self.estagio = ESTAGIO_VIGILANCIA
        self.tempo = 0.0                 # segundos desde o início DESTE mapa (definido pelo modo)
        # Dificuldade do mapa atual (o modo ajusta a cada novo mapa)
        self.fator_mapa = 1.0            # multiplicador de velocidade do mapa
        self.raio_deteccao = RAIO_DETECCAO
        self.tempo_furia = TEMPO_FURIA
        self.atordoado = 0.0             # segundos parado após bater num escudo
        self.jogador_visivel = True      # False com a poção de invisibilidade
        self.sem_ver = 0.0               # segundos sem enxergar o jogador (na caçada)
        self.espera_busca = 0.0          # contagem até a próxima BFS
        self.caminho = []                # caminho em cache: [origem, passo1, passo2, ...]
        self.distancia = None            # distância de caminho até o jogador (tiles)

    # ---------------- inteligência ----------------
    def _buscar(self, labirinto, jogador):
        """Roda a BFS (a cada INTERVALO_BUSCA segundos) e guarda o resultado."""
        origem = (self.coluna, self.linha)
        alvo = labirinto.tile_do_ponto(jogador.retangulo.center)
        caminho = labirinto.caminho_bfs(origem, alvo, LIMITE_BFS)
        if caminho is None:
            self.caminho, self.distancia = [], None
        else:
            self.caminho, self.distancia = [origem] + caminho, len(caminho)

    def _atualizar_estagio(self, dt):
        """Decide o estágio a partir do tempo, da distância e da visibilidade do jogador."""
        enxerga = self.jogador_visivel and self.distancia is not None
        if self.tempo >= self.tempo_furia:
            self.estagio = ESTAGIO_FURIA if self.jogador_visivel else ESTAGIO_VIGILANCIA
            return
        if self.estagio == ESTAGIO_VIGILANCIA:
            if enxerga and self.distancia <= self.raio_deteccao:
                self.estagio = ESTAGIO_CACADA
                self.sem_ver = 0.0
        else:   # caçada (ou saindo da fúria)
            if enxerga and self.distancia <= RAIO_PERDA:
                self.sem_ver = 0.0
            else:
                self.sem_ver += dt
                if self.sem_ver >= TEMPO_PERDA_JOGADOR:
                    self.estagio = ESTAGIO_VIGILANCIA

    @property
    def cacando(self):
        return self.estagio in (ESTAGIO_CACADA, ESTAGIO_FURIA) and self.jogador_visivel

    def escolher_destino(self, labirinto, jogador):
        """Chamado ao chegar num tile: segue o caminho em cache ou patrulha."""
        self.perseguindo = self.cacando
        if self.cacando:
            origem = (self.coluna, self.linha)
            if origem in self.caminho:
                indice = self.caminho.index(origem)
                if indice + 1 < len(self.caminho):
                    proximo = self.caminho[indice + 1]
                    self.direcao = (proximo[0] - origem[0], proximo[1] - origem[1])
                    return proximo
            # caminho velho ou ausente: busca de novo agora
            self._buscar(labirinto, jogador)
            if len(self.caminho) > 1:
                proximo = self.caminho[1]
                self.direcao = (proximo[0] - origem[0], proximo[1] - origem[1])
                return proximo
        return super().escolher_destino(labirinto, jogador)    # patrulha (Esqueleto)

    def atualizar(self, dt, labirinto, jogador):
        # velocidade = base x fator do mapa x fator do tempo, sempre abaixo do teto
        self.velocidade = min(VELOCIDADE_MAXIMA_GUARDIAO,
                              VELOCIDADE_BASE_GUARDIAO * self.fator_mapa
                              * multiplicador_de_velocidade(self.tempo))
        if self.atordoado > 0:
            self.atordoado = max(0.0, self.atordoado - dt)
            self.tempo_animacao += dt
            return
        self.espera_busca -= dt
        if self.espera_busca <= 0:
            self._buscar(labirinto, jogador)
            self._atualizar_estagio(INTERVALO_BUSCA)
            self.espera_busca = INTERVALO_BUSCA
        super().atualizar(dt, labirinto, jogador)

    # ---------------- posição ----------------
    def posicionar(self, coluna, linha):
        """Teletransporta o Guardião para o centro de um tile (reposicionamento)."""
        self.coluna, self.linha = coluna, linha
        self.destino = (coluna, linha)
        self.direcao = (0, 0)
        self.x, self.y = self._posicao_do_tile(coluna, linha)
        self.retangulo.topleft = (round(self.x), round(self.y))
        self.caminho = []
        self.distancia = None
        self.estagio = ESTAGIO_VIGILANCIA if self.tempo < self.tempo_furia else self.estagio
        self.espera_busca = 0.0

    def pixel_central(self):
        return self.retangulo.center

    def desenhar(self, tela):
        desenhar_guardiao(tela, self.retangulo, self.tempo_animacao, self.estagio,
                          self.direcao[0] < 0, self.atordoado > 0)