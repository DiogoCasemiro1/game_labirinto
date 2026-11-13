"""
Gerador aleatório de fases (modo infinito).

Cada fase é um labirinto novo, criado na hora a partir de uma "semente"
aleatória. Quanto maior o número da fase, mais difícil ela fica: menos
atalhos, mais inimigos, mais armadilhas e inimigos mais rápidos. A cada
INTERVALO_CHEFE fases aparece um dragão.

Técnicas usadas: matriz (lista de listas), busca em largura (BFS),
aleatoriedade controlada por semente (mesma semente = mesmo mapa).
"""

import random
from collections import deque

from constantes import (
    ARMADILHA, CHAO, CHAVE, CHEFE, COLUNAS, ESQUELETO, GOBLIN, INICIO,
    INTERVALO_CHEFE, LINHAS, MOEDA, PAREDE, SAIDA, TAMANHO_TILE, TESOURO,
    VELOCIDADE_JOGADOR,
)

# ---------------- ajustes de dificuldade ----------------
MAX_MOEDAS = 24
MAX_TESOUROS = 6
MAX_ESQUELETOS = 7
MAX_GOBLINS = 5
MAX_ARMADILHAS = 14
MAX_CHEFES = 3
FATOR_VELOCIDADE_MAXIMO = 1.4
ESCURIDAO_MINIMA = 95
ESCURIDAO_MAXIMA = 190
TEMPO_MINIMO = 60
TEMPO_MAXIMO = 240
DISTANCIA_MIN_ESQUELETO = 10     # em tiles de caminho a partir do início
DISTANCIA_MIN_GOBLIN = 12
DISTANCIA_MIN_ARMADILHA = 6
DISTANCIA_MAX_CHEFE_DA_PORTA = 6

PASSOS_CELULA = [(2, 0), (-2, 0), (0, 2), (0, -2)]   # de uma célula à vizinha
VIZINHOS = [(1, 0), (-1, 0), (0, 1), (0, -1)]

# Nomes: (substantivo, gênero) e adjetivos (masculino, feminino)
LUGARES = [("A Cripta", "f"), ("O Calabouço", "m"), ("A Catacumba", "f"),
           ("O Salão", "m"), ("A Torre", "f"), ("O Porão", "m"),
           ("A Masmorra", "f"), ("O Túnel", "m"), ("A Prisão", "f"), ("O Abismo", "m")]
ADJETIVOS = [("Esquecido", "Esquecida"), ("Sombrio", "Sombria"), ("Maldito", "Maldita"),
             ("Perdido", "Perdida"), ("Silencioso", "Silenciosa"), ("Gelado", "Gelada"),
             ("Antigo", "Antiga"), ("Profundo", "Profunda"), ("Assombrado", "Assombrada"),
             ("Abandonado", "Abandonada")]


def parametros_do_nivel(numero):
    """Quantidades de cada elemento para a fase 'numero' (1, 2, 3...)."""
    eh_chefe = numero % INTERVALO_CHEFE == 0
    return {
        "atalhos": max(3, 20 - 2 * numero),        # menos atalhos = caminhos mais longos
        "moedas": min(MAX_MOEDAS, 10 + numero),
        "tesouros": min(MAX_TESOUROS, 3 + numero // 4),
        "esqueletos": 0 if numero == 1 else min(MAX_ESQUELETOS, 1 + (numero - 2) // 2),
        "goblins": 0 if numero < 4 else min(MAX_GOBLINS, 1 + (numero - 4) // 3),
        "armadilhas": 0 if numero < 3 else min(MAX_ARMADILHAS, 2 + (numero - 3)),
        "chefes": min(MAX_CHEFES, numero // INTERVALO_CHEFE) if eh_chefe else 0,
        "fator_inimigos": min(FATOR_VELOCIDADE_MAXIMO, 1.0 + 0.03 * (numero - 1)),
        "escuridao": min(ESCURIDAO_MAXIMA, ESCURIDAO_MINIMA + 8 * numero),
    }


# ----------------------------------------------------------------------
# Construção do labirinto
# ----------------------------------------------------------------------
def _escavar_dfs(rng, grade, celulas, inicio):
    """Labirinto 'sinuoso': anda o mais longe possível e volta quando empaca."""
    visitadas = {inicio}
    pilha = [inicio]
    grade[inicio[0]][inicio[1]] = CHAO
    while pilha:
        linha, coluna = pilha[-1]
        vizinhas = [(linha + dl, coluna + dc, dl, dc) for dl, dc in PASSOS_CELULA
                    if (linha + dl, coluna + dc) in celulas
                    and (linha + dl, coluna + dc) not in visitadas]
        if not vizinhas:
            pilha.pop()
            continue
        nova_linha, nova_coluna, dl, dc = rng.choice(vizinhas)
        grade[linha + dl // 2][coluna + dc // 2] = CHAO     # derruba a parede entre as células
        grade[nova_linha][nova_coluna] = CHAO
        visitadas.add((nova_linha, nova_coluna))
        pilha.append((nova_linha, nova_coluna))


def _escavar_prim(rng, grade, celulas, inicio):
    """Labirinto 'ramificado' (algoritmo de Prim): muitos becos curtos."""
    visitadas = {inicio}
    grade[inicio[0]][inicio[1]] = CHAO
    fronteira = [(inicio, (inicio[0] + dl, inicio[1] + dc), dl, dc)
                 for dl, dc in PASSOS_CELULA if (inicio[0] + dl, inicio[1] + dc) in celulas]
    while fronteira:
        (linha, coluna), destino, dl, dc = fronteira.pop(rng.randrange(len(fronteira)))
        if destino in visitadas:
            continue
        grade[linha + dl // 2][coluna + dc // 2] = CHAO
        grade[destino[0]][destino[1]] = CHAO
        visitadas.add(destino)
        for pl, pc in PASSOS_CELULA:
            vizinha = (destino[0] + pl, destino[1] + pc)
            if vizinha in celulas and vizinha not in visitadas:
                fronteira.append((destino, vizinha, pl, pc))


def _abrir_salas(rng, grade, celulas, quantidade):
    """Abre salões 3x3 tiles (2x2 células) para quebrar a monotonia dos corredores."""
    candidatas = [(l, c) for (l, c) in celulas if (l + 2, c + 2) in celulas]
    rng.shuffle(candidatas)
    for linha, coluna in candidatas[:quantidade]:
        for dl in range(3):
            for dc in range(3):
                grade[linha + dl][coluna + dc] = CHAO


def _abrir_atalhos(rng, grade, quantidade):
    """Derruba algumas paredes entre corredores vizinhos, criando caminhos alternativos."""
    candidatas = []
    for linha in range(1, LINHAS - 2):
        for coluna in range(1, COLUNAS - 2):
            if grade[linha][coluna] != PAREDE:
                continue
            if linha % 2 == 1 and coluna % 2 == 0:       # entre duas células lado a lado
                candidatas.append((linha, coluna))
            elif linha % 2 == 0 and coluna % 2 == 1:     # entre duas células empilhadas
                candidatas.append((linha, coluna))
    rng.shuffle(candidatas)
    for linha, coluna in candidatas[:quantidade]:
        grade[linha][coluna] = CHAO


def _distancias(grade, origem):
    """Busca em largura: distância (em tiles) de 'origem' a todo tile alcançável."""
    distancia = {origem: 0}
    fila = deque([origem])
    while fila:
        linha, coluna = fila.popleft()
        for dl, dc in VIZINHOS:
            vizinho = (linha + dl, coluna + dc)
            if vizinho in distancia:
                continue
            if 0 <= vizinho[0] < LINHAS and 0 <= vizinho[1] < COLUNAS \
                    and grade[vizinho[0]][vizinho[1]] != PAREDE:
                distancia[vizinho] = distancia[(linha, coluna)] + 1
                fila.append(vizinho)
    return distancia


def _nome_da_fase(rng, eh_chefe):
    if eh_chefe:
        return "A Câmara do Dragão"
    substantivo, genero = rng.choice(LUGARES)
    adjetivo = rng.choice(ADJETIVOS)[0 if genero == "m" else 1]
    return f"{substantivo} {adjetivo}"


def _colocar(rng, grade, simbolo, quantidade, candidatas):
    """Sorteia 'quantidade' posições livres entre as candidatas e escreve o símbolo."""
    livres = [p for p in candidatas if grade[p[0]][p[1]] == CHAO]
    rng.shuffle(livres)
    for linha, coluna in livres[:quantidade]:
        grade[linha][coluna] = simbolo


def _montar_fase(rng, numero):
    """Constrói UMA tentativa de fase. Retorna a grade e a distância do trajeto."""
    parametros = parametros_do_nivel(numero)
    grade = [[PAREDE] * COLUNAS for _ in range(LINHAS)]
    celulas = {(l, c) for l in range(1, LINHAS - 2, 2) for c in range(1, COLUNAS - 2, 2)}

    # 1) corredores (dois estilos), salões e atalhos
    inicio = rng.choice(sorted(celulas))
    if rng.random() < 0.5:
        _escavar_dfs(rng, grade, celulas, inicio)
    else:
        _escavar_prim(rng, grade, celulas, inicio)
    if numero >= 2:
        _abrir_salas(rng, grade, celulas, rng.randint(0, min(2, 1 + numero // 4)))
    _abrir_atalhos(rng, grade, parametros["atalhos"])
    dist_inicio = _distancias(grade, inicio)

    # 2) porta numa das bordas, longe do início
    opcoes = []
    for (linha, coluna) in celulas:
        if linha == 1:
            opcoes.append(((linha, coluna), (0, coluna)))
        if linha == LINHAS - 3:
            opcoes.append(((linha, coluna), (LINHAS - 2, coluna)))
        if coluna == 1:
            opcoes.append(((linha, coluna), (linha, 0)))
        if coluna == COLUNAS - 3:
            opcoes.append(((linha, coluna), (linha, COLUNAS - 2)))
    opcoes.sort(key=lambda o: -dist_inicio[o[0]])
    celula_porta, posicao_porta = rng.choice(opcoes[:8])
    grade[posicao_porta[0]][posicao_porta[1]] = SAIDA
    dist_porta = _distancias(grade, celula_porta)

    # 3) chave: bem longe do início e razoavelmente longe da porta
    maior = max(dist_inicio[c] for c in celulas)
    candidatas_chave = [c for c in celulas if dist_inicio[c] >= 0.4 * maior
                        and dist_porta[c] >= 8 and c != inicio]
    if not candidatas_chave:
        candidatas_chave = [max(celulas, key=lambda c: dist_inicio[c] + dist_porta[c])]
    chave = rng.choice(sorted(candidatas_chave))
    grade[chave[0]][chave[1]] = CHAVE

    # 4) tempo limite proporcional ao trajeto início -> chave -> porta
    dist_chave = _distancias(grade, chave)
    trajeto_tiles = dist_inicio[chave] + dist_chave[celula_porta]
    trajeto_segundos = trajeto_tiles * TAMANHO_TILE / VELOCIDADE_JOGADOR
    folga = max(2.2, 3.6 - 0.08 * numero)
    tempo = int(max(TEMPO_MINIMO, min(TEMPO_MAXIMO, 35 + trajeto_segundos * folga)))

    # 5) itens, inimigos e armadilhas
    ordem_celulas = sorted(celulas)
    sem_ponta_morta = [c for c in ordem_celulas if c != inicio and c != celula_porta]
    becos = [c for c in sem_ponta_morta
             if sum(grade[c[0] + dl][c[1] + dc] != PAREDE for dl, dc in VIZINHOS) == 1]
    longe = [c for c in sem_ponta_morta if dist_inicio[c] >= 6]
    _colocar(rng, grade, TESOURO, parametros["tesouros"], becos)
    _colocar(rng, grade, TESOURO, parametros["tesouros"] - sum(
        linha.count(TESOURO) for linha in grade), longe)
    _colocar(rng, grade, CHEFE, parametros["chefes"],
             [c for c in sem_ponta_morta if dist_porta[c] <= DISTANCIA_MAX_CHEFE_DA_PORTA
              and dist_inicio[c] >= 10])
    _colocar(rng, grade, ESQUELETO, parametros["esqueletos"],
             [c for c in sem_ponta_morta if dist_inicio[c] >= DISTANCIA_MIN_ESQUELETO])
    _colocar(rng, grade, GOBLIN, parametros["goblins"],
             [c for c in sem_ponta_morta if dist_inicio[c] >= DISTANCIA_MIN_GOBLIN])
    _colocar(rng, grade, MOEDA, parametros["moedas"], sem_ponta_morta)
    corredores = [(l, c) for l in range(1, LINHAS - 1) for c in range(1, COLUNAS - 1)
                  if dist_inicio.get((l, c), 0) >= DISTANCIA_MIN_ARMADILHA
                  and (l, c) != celula_porta]
    _colocar(rng, grade, ARMADILHA, parametros["armadilhas"], corredores)

    grade[inicio[0]][inicio[1]] = INICIO
    return grade, tempo


def _fase_valida(grade):
    """Confere se tudo o que importa pode ser alcançado a partir do início."""
    inicio = next((l, c) for l in range(LINHAS) for c in range(COLUNAS)
                  if grade[l][c] == INICIO)
    alcancaveis = _distancias(grade, inicio)
    for linha in range(LINHAS):
        for coluna in range(COLUNAS):
            if grade[linha][coluna] in (CHAVE, MOEDA, TESOURO, ESQUELETO, GOBLIN,
                                        CHEFE, ARMADILHA) \
                    and (linha, coluna) not in alcancaveis:
                return False
    porta = next((l, c) for l in range(LINHAS) for c in range(COLUNAS)
                 if grade[l][c] == SAIDA)
    chaves = sum(linha.count(CHAVE) for linha in grade)
    # a porta (não atravessável pelo BFS por ser SAIDA != PAREDE, ela é alcançável)
    return chaves == 1 and porta in alcancaveis


def gerar_nivel(numero, semente=None):
    """
    Gera a fase 'numero'. Devolve um dicionário no mesmo formato de niveis.NIVEIS
    (com a chave extra 'semente'). Sem semente, escolhe uma aleatória.
    """
    if semente is None:
        semente = random.SystemRandom().randrange(1 << 30)
    for tentativa in range(30):
        rng = random.Random(semente + tentativa)
        grade, tempo = _montar_fase(rng, numero)
        if _fase_valida(grade):
            break
    else:
        raise RuntimeError("Não foi possível gerar uma fase válida")
    parametros = parametros_do_nivel(numero)
    return {
        "nome": _nome_da_fase(rng, parametros["chefes"] > 0),
        "escuridao": parametros["escuridao"],
        "mapa": ["".join(linha) for linha in grade],
        "tempo": tempo,
        "fator_inimigos": parametros["fator_inimigos"],
        "semente": semente,
    }