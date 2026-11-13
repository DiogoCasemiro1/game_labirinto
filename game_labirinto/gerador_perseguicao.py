"""
Gerador de mapas do modo Perseguição.

Reaproveita as funções de escavação do gerador.py (sem modificá-lo) e monta
um mapa próprio: com santuários (loja) e a posição inicial do Guardião.
"""

import random

from constantes import (
    ARMADILHA, CHAVE, COLUNAS, INICIO, LINHAS, MOEDA, PAREDE, SAIDA, TESOURO,
)
from constantes_perseguicao import (
    ATALHOS_MINIMOS, ATALHOS_PERSEGUICAO, DISTANCIA_INICIAL_GUARDIAO,
    ESCURIDAO_MAXIMA_PERSEGUICAO, ESCURIDAO_PERSEGUICAO,
    FATOR_VELOCIDADE_MAXIMO_MAPA, FATOR_VELOCIDADE_POR_MAPA,
    MAPA_COM_UM_SANTUARIO, MAX_ARMADILHAS_PERSEGUICAO, MAX_MOEDAS_PERSEGUICAO,
    MAX_TESOUROS_PERSEGUICAO, QUANTIDADE_ARMADILHAS, QUANTIDADE_MOEDAS,
    QUANTIDADE_SANTUARIOS, QUANTIDADE_TESOUROS, RAIO_DETECCAO,
    RAIO_DETECCAO_MAXIMO, REDUCAO_FURIA_POR_MAPA, SIMBOLO_GUARDIAO,
    SIMBOLO_SANTUARIO, SUBTITULO_MODO, TEMPO_FURIA, TEMPO_FURIA_MINIMO,
)
from gerador import (
    _abrir_atalhos, _abrir_salas, _colocar, _distancias, _escavar_dfs,
    _escavar_prim,
)

DISTANCIA_MIN_ENTRE_SANTUARIOS = 8
DISTANCIA_MIN_ARMADILHA = 6


def parametros_do_mapa(numero):
    """
    Quantidades e dificuldade do Guardião para o mapa 'numero' (1, 2, 3...).
    Tudo cresce aos poucos e tem teto, para a partida nunca ficar impossível.
    """
    passo = numero - 1
    return {
        "atalhos": max(ATALHOS_MINIMOS, ATALHOS_PERSEGUICAO - passo),
        "moedas": min(MAX_MOEDAS_PERSEGUICAO, QUANTIDADE_MOEDAS + passo // 2),
        "tesouros": min(MAX_TESOUROS_PERSEGUICAO, QUANTIDADE_TESOUROS + passo // 4),
        "armadilhas": min(MAX_ARMADILHAS_PERSEGUICAO, QUANTIDADE_ARMADILHAS + passo),
        "santuarios": QUANTIDADE_SANTUARIOS if numero < MAPA_COM_UM_SANTUARIO else 1,
        "escuridao": min(ESCURIDAO_MAXIMA_PERSEGUICAO, ESCURIDAO_PERSEGUICAO + 3 * passo),
        # Guardião deste mapa
        "fator_velocidade": min(FATOR_VELOCIDADE_MAXIMO_MAPA,
                                1.0 + FATOR_VELOCIDADE_POR_MAPA * passo),
        "raio_deteccao": min(RAIO_DETECCAO_MAXIMO, RAIO_DETECCAO + passo // 2),
        "tempo_furia": max(TEMPO_FURIA_MINIMO, TEMPO_FURIA - REDUCAO_FURIA_POR_MAPA * passo),
    }


def _montar(rng, parametros):
    """Uma tentativa de mapa. Retorna a grade (lista de listas de caracteres)."""
    grade = [[PAREDE] * COLUNAS for _ in range(LINHAS)]
    celulas = {(l, c) for l in range(1, LINHAS - 2, 2) for c in range(1, COLUNAS - 2, 2)}

    # corredores, salões e muitos atalhos (para dar rotas de fuga)
    inicio = rng.choice(sorted(celulas))
    (_escavar_dfs if rng.random() < 0.5 else _escavar_prim)(rng, grade, celulas, inicio)
    _abrir_salas(rng, grade, celulas, rng.randint(1, 2))
    _abrir_atalhos(rng, grade, parametros["atalhos"])
    dist_inicio = _distancias(grade, inicio)

    # porta numa borda, longe do início
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

    # chave: longe do início e da porta
    maior = max(dist_inicio[c] for c in celulas)
    candidatas = [c for c in celulas if dist_inicio[c] >= 0.4 * maior
                  and dist_porta[c] >= 8 and c != inicio]
    if not candidatas:
        candidatas = [max(celulas, key=lambda c: dist_inicio[c] + dist_porta[c])]
    chave = rng.choice(sorted(candidatas))
    grade[chave[0]][chave[1]] = CHAVE

    livres = [c for c in sorted(celulas) if c not in (inicio, celula_porta, chave)]

    # Guardião: bem longe do jogador
    longe = [c for c in livres if dist_inicio[c] >= DISTANCIA_INICIAL_GUARDIAO]
    if not longe:
        longe = sorted(livres, key=lambda c: -dist_inicio[c])[:5]
    guardiao = rng.choice(sorted(longe))
    grade[guardiao[0]][guardiao[1]] = SIMBOLO_GUARDIAO

    # santuários: afastados do início e entre si
    candidatos_santuario = [c for c in livres if c != guardiao and dist_inicio[c] >= 5]
    rng.shuffle(candidatos_santuario)
    santuarios = []
    for celula in candidatos_santuario:
        if len(santuarios) >= parametros["santuarios"]:
            break
        if all(_distancias(grade, s).get(celula, 0) >= DISTANCIA_MIN_ENTRE_SANTUARIOS
               for s in santuarios):
            santuarios.append(celula)
    for linha, coluna in santuarios:
        grade[linha][coluna] = SIMBOLO_SANTUARIO

    # itens e armadilhas
    celulas_livres = [c for c in livres if c != guardiao]
    _colocar(rng, grade, TESOURO, parametros["tesouros"], celulas_livres)
    _colocar(rng, grade, MOEDA, parametros["moedas"], celulas_livres)
    corredores = [(l, c) for l in range(1, LINHAS - 1) for c in range(1, COLUNAS - 1)
                  if dist_inicio.get((l, c), 0) >= DISTANCIA_MIN_ARMADILHA
                  and (l, c) != celula_porta]
    _colocar(rng, grade, ARMADILHA, parametros["armadilhas"], corredores)

    grade[inicio[0]][inicio[1]] = INICIO
    return grade


def _valida(grade):
    """Tudo o que o jogador precisa alcançar deve estar ao seu alcance."""
    inicio = next((l, c) for l in range(LINHAS) for c in range(COLUNAS) if grade[l][c] == INICIO)
    alcancaveis = _distancias(grade, inicio)
    contagem = {}
    for linha in range(LINHAS):
        for coluna in range(COLUNAS):
            simbolo = grade[linha][coluna]
            contagem[simbolo] = contagem.get(simbolo, 0) + 1
            if simbolo in (CHAVE, MOEDA, TESOURO, ARMADILHA, SAIDA, SIMBOLO_GUARDIAO,
                           SIMBOLO_SANTUARIO) and (linha, coluna) not in alcancaveis:
                return False
    return (contagem.get(CHAVE) == 1 and contagem.get(SAIDA) == 1
            and contagem.get(SIMBOLO_GUARDIAO) == 1
            and contagem.get(SIMBOLO_SANTUARIO, 0) >= 1)


def gerar_nivel_perseguicao(numero=1, semente=None):
    """
    Gera o mapa 'numero' do modo Perseguição, no mesmo formato dos outros modos.
    A chave extra "guardiao" leva a dificuldade do Guardião naquele mapa.
    """
    if semente is None:
        semente = random.SystemRandom().randrange(1 << 30)
    parametros = parametros_do_mapa(numero)
    for tentativa in range(30):
        rng = random.Random(semente + tentativa)
        grade = _montar(rng, parametros)
        if _valida(grade):
            break
    else:
        raise RuntimeError("Não foi possível gerar um mapa válido")
    return {
        "nome": SUBTITULO_MODO,
        "escuridao": parametros["escuridao"],
        "mapa": ["".join(linha) for linha in grade],
        "tempo": 99999,              # não há limite de tempo: o tempo é de sobrevivência
        "fator_inimigos": 1.0,
        "semente": semente,
        "guardiao": {"fator_velocidade": parametros["fator_velocidade"],
                     "raio_deteccao": parametros["raio_deteccao"],
                     "tempo_furia": parametros["tempo_furia"]},
    }