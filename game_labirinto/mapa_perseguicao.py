"""
Mapas do modo Perseguição - O Guardião das Trevas.

O mapa base vem do gerador ORIGINAL (gerador.gerar_nivel), sem nenhuma alteração
nele: porta, chave, moedas, tesouros e armadilhas já saem prontos e validados.
Depois, SEPARADAMENTE, este módulo:
  - remove os inimigos comuns (no modo perseguição a ameaça é só o Guardião);
  - abre atalhos extras (mais ciclos = mais rotas de fuga);
  - acrescenta moedas/tesouros extras, o Guardião (G), os santuários ($),
    os esconderijos (H) e as passagens secretas (%).

Também define LabirintoPerseguicao: o Labirinto original com uma única regra
a mais -> as passagens secretas não são "tiles livres" para o Guardião.
"""

import random

from constantes import (
    ATALHO_MIN_PASSAGEM, ATALHOS_EXTRAS_PERSEGUICAO, CHAO, CHAVE, CHEFE,
    COLUNAS, DIST_MIN_ENTRE_SANTUARIOS, DIST_MIN_GUARDIAO_INICIO, ESCONDERIJO,
    ESCURIDAO_PERSEGUICAO, ESQUELETO, GOBLIN, GUARDIAO, INICIO, LINHAS, MOEDA,
    MOEDAS_EXTRAS_PERSEGUICAO, NIVEL_BASE_PERSEGUICAO, PAREDE, PASSAGEM_SECRETA,
    QTD_ESCONDERIJOS, QTD_PASSAGENS_SECRETAS, QTD_SANTUARIOS, SAIDA, SANTUARIO,
    TESOURO, TESOUROS_EXTRAS_PERSEGUICAO, ALTURA_HUD, ARMADILHA, TAMANHO_TILE,
)
from desenho import desenhar_parede
from desenho_perseguicao import desenhar_rachaduras_passagem
from entidades import Labirinto
# Funções auxiliares do gerador original, reaproveitadas sem modificação
from gerador import VIZINHOS, _abrir_atalhos, _colocar, _distancias, gerar_nivel

NOME_MAPA_PERSEGUICAO = "A Masmorra do Guardião"


# ----------------------------------------------------------------------
# Geração
# ----------------------------------------------------------------------
def _achar(grade, simbolo):
    """Primeira posição (linha, coluna) com o símbolo, ou None."""
    for linha, texto in enumerate(grade):
        for coluna, s in enumerate(texto):
            if s == simbolo:
                return (linha, coluna)
    return None


def _vizinhos_livres(grade, posicao):
    linha, coluna = posicao
    return [(linha + dl, coluna + dc) for dl, dc in VIZINHOS
            if 0 <= linha + dl < LINHAS and 0 <= coluna + dc < COLUNAS
            and grade[linha + dl][coluna + dc] != PAREDE]


def _escolher_guardiao(rng, grade, livres, dist_inicio):
    """Posição inicial do Guardião: entre as mais distantes do jogador."""
    candidatas = [p for p in livres if dist_inicio[p] >= DIST_MIN_GUARDIAO_INICIO]
    # de preferência, sem "acampar" ao lado da chave ou da porta
    objetivos = [p for p in (_achar(grade, CHAVE), _achar(grade, SAIDA)) if p is not None]
    longe_objetivos = [p for p in candidatas
                       if all(abs(p[0] - o[0]) + abs(p[1] - o[1]) >= 5 for o in objetivos)]
    if longe_objetivos:
        candidatas = longe_objetivos
    if not candidatas:
        candidatas = [max(livres, key=lambda p: dist_inicio[p])]
    candidatas.sort(key=lambda p: -dist_inicio[p])
    escolhida = rng.choice(candidatas[:max(1, len(candidatas) * 2 // 5)])
    grade[escolhida[0]][escolhida[1]] = GUARDIAO
    return escolhida


def _escolher_santuarios(rng, grade, livres, dist_inicio, dist_guardiao):
    """Santuários em corredores (nunca em becos), longe um do outro e do Guardião."""
    candidatas = [p for p in livres if grade[p[0]][p[1]] == CHAO
                  and len(_vizinhos_livres(grade, p)) >= 2
                  and dist_inicio[p] >= 4 and dist_guardiao.get(p, 0) >= 6]
    rng.shuffle(candidatas)
    escolhidos = []
    for posicao in candidatas:
        if len(escolhidos) >= QTD_SANTUARIOS:
            break
        if all(_distancias(grade, e).get(posicao, 0) >= DIST_MIN_ENTRE_SANTUARIOS
               for e in escolhidos):
            escolhidos.append(posicao)
    for linha, coluna in escolhidos:
        grade[linha][coluna] = SANTUARIO
    return escolhidos


def _escolher_esconderijos(rng, grade, livres, dist_inicio, dist_guardiao):
    """Esconderijos preferem becos (nichos naturais da masmorra)."""
    def boa(p):
        return grade[p[0]][p[1]] == CHAO and dist_inicio[p] >= 4 \
            and dist_guardiao.get(p, 0) >= 5
    becos = [p for p in livres if boa(p) and len(_vizinhos_livres(grade, p)) == 1]
    outros = [p for p in livres if boa(p) and p not in becos]
    rng.shuffle(becos)
    rng.shuffle(outros)
    escolhidos = (becos + outros)[:QTD_ESCONDERIJOS]
    for linha, coluna in escolhidos:
        grade[linha][coluna] = ESCONDERIJO
    return escolhidos


def _escolher_passagens(rng, grade):
    """
    Paredes internas entre dois corredores cujo caminho "por fora" é longo:
    viram passagens secretas (atalho exclusivo do jogador).
    """
    candidatas = []
    for linha in range(1, LINHAS - 1):
        for coluna in range(1, COLUNAS - 1):
            if grade[linha][coluna] != PAREDE:
                continue
            for (a, b, c, d) in (((linha, coluna - 1), (linha, coluna + 1),
                                  (linha - 1, coluna), (linha + 1, coluna)),
                                 ((linha - 1, coluna), (linha + 1, coluna),
                                  (linha, coluna - 1), (linha, coluna + 1))):
                lados_livres = all(grade[p[0]][p[1]] not in (PAREDE, SAIDA,
                                                             PASSAGEM_SECRETA)
                                   for p in (a, b))
                laterais_parede = all(grade[p[0]][p[1]] == PAREDE for p in (c, d))
                if lados_livres and laterais_parede:
                    economia = _distancias(grade, a).get(b, 999)
                    if economia >= ATALHO_MIN_PASSAGEM:
                        candidatas.append((economia + rng.random() * 6, (linha, coluna)))
    candidatas.sort(reverse=True)
    escolhidas = []
    for _, posicao in candidatas:
        if len(escolhidas) >= QTD_PASSAGENS_SECRETAS:
            break
        if all(abs(posicao[0] - e[0]) + abs(posicao[1] - e[1]) >= 4 for e in escolhidas):
            escolhidas.append(posicao)
    for linha, coluna in escolhidas:
        grade[linha][coluna] = PASSAGEM_SECRETA
    return escolhidas


def mapa_perseguicao_valido(mapa):
    """
    Confere se a partida pode ser concluída SEM usar passagens secretas:
    início -> chave, santuários, esconderijos, Guardião, itens e porta.
    """
    grade = [linha.replace(PASSAGEM_SECRETA, PAREDE) for linha in mapa]
    inicio = _achar(grade, INICIO)
    if inicio is None or _achar(grade, GUARDIAO) is None or _achar(grade, CHAVE) is None:
        return False
    alcancaveis = _distancias(grade, inicio)
    for linha, texto in enumerate(grade):
        for coluna, simbolo in enumerate(texto):
            if simbolo in (CHAVE, SAIDA, SANTUARIO, ESCONDERIJO, GUARDIAO, MOEDA, TESOURO) \
                    and (linha, coluna) not in alcancaveis:
                return False
    return sum(t.count(SANTUARIO) for t in grade) >= 1


def _montar(semente):
    nivel = gerar_nivel(NIVEL_BASE_PERSEGUICAO, semente)
    rng = random.Random(semente * 31 + 7)
    grade = [list(linha) for linha in nivel["mapa"]]

    # 1) só o Guardião persegue: inimigos comuns viram chão
    for linha in grade:
        for coluna, simbolo in enumerate(linha):
            if simbolo in (ESQUELETO, GOBLIN, CHEFE):
                linha[coluna] = CHAO

    # 2) mais ciclos no labirinto e mais riquezas
    _abrir_atalhos(rng, grade, ATALHOS_EXTRAS_PERSEGUICAO)
    inicio = _achar(grade, INICIO)
    dist_inicio = _distancias(grade, inicio)
    livres = sorted(p for p in dist_inicio if grade[p[0]][p[1]] == CHAO)
    _colocar(rng, grade, MOEDA, MOEDAS_EXTRAS_PERSEGUICAO,
             [p for p in livres if dist_inicio[p] >= 3])
    _colocar(rng, grade, TESOURO, TESOUROS_EXTRAS_PERSEGUICAO,
             [p for p in livres if dist_inicio[p] >= 8])
    livres = [p for p in livres if grade[p[0]][p[1]] == CHAO]

    # 3) elementos do modo
    guardiao = _escolher_guardiao(rng, grade, livres, dist_inicio)
    livres = [p for p in livres if p != guardiao]
    dist_guardiao = _distancias(grade, guardiao)
    _escolher_santuarios(rng, grade, livres, dist_inicio, dist_guardiao)
    _escolher_esconderijos(rng, grade, livres, dist_inicio, dist_guardiao)
    _escolher_passagens(rng, grade)

    mapa = ["".join(linha) for linha in grade]
    if not mapa_perseguicao_valido(mapa):
        return None
    return {
        "nome": NOME_MAPA_PERSEGUICAO,
        "escuridao": ESCURIDAO_PERSEGUICAO,
        "mapa": mapa,
        "semente": semente,
    }


def gerar_mapa_perseguicao(semente=None):
    """Gera um mapa do modo Perseguição (mesma semente = mesmo mapa)."""
    if semente is None:
        semente = random.SystemRandom().randrange(1 << 30)
    for tentativa in range(30):
        resultado = _montar(semente + tentativa * 7919)
        if resultado is not None:
            return resultado
    raise RuntimeError("Não foi possível gerar um mapa de perseguição válido")


# ----------------------------------------------------------------------
# Labirinto do modo (herda tudo do Labirinto original)
# ----------------------------------------------------------------------
class LabirintoPerseguicao(Labirinto):
    """
    Igual ao Labirinto original, com uma regra a mais: a passagem secreta não é
    'tile livre' (o Guardião e o BFS não passam), mas também não é parede para
    o jogador (não entra em self.paredes, então a colisão original o deixa passar).
    """

    def __init__(self, desenho):
        super().__init__(desenho)
        self.guardiao_inicial = (0, 0)       # (coluna, linha)
        self.santuarios = []                  # (coluna, linha)
        self.esconderijos = []
        self.passagens = []
        for linha, texto in enumerate(desenho):
            for coluna, simbolo in enumerate(texto):
                if simbolo == GUARDIAO:
                    self.guardiao_inicial = (coluna, linha)
                elif simbolo == SANTUARIO:
                    self.santuarios.append((coluna, linha))
                elif simbolo == ESCONDERIJO:
                    self.esconderijos.append((coluna, linha))
                elif simbolo == PASSAGEM_SECRETA:
                    self.passagens.append((coluna, linha))
        self._pintar_passagens()

    def tile_livre(self, coluna, linha):
        if not super().tile_livre(coluna, linha):
            return False
        return self.desenho[linha][coluna] != PASSAGEM_SECRETA

    def eh_perigoso(self, coluna, linha):
        """Tiles onde ninguém deve reaparecer (armadilhas)."""
        return self.desenho[linha][coluna] == ARMADILHA

    def _pintar_passagens(self):
        """A passagem secreta parece parede rachada (com contorno, que denuncia o segredo)."""
        for coluna, linha in self.passagens:
            x = coluna * TAMANHO_TILE
            y = ALTURA_HUD + linha * TAMANHO_TILE
            face = not self._eh_parede(coluna, linha + 1)
            desenhar_parede(self.superficie, x, y, face, 6)
            desenhar_rachaduras_passagem(self.superficie, x, y)
