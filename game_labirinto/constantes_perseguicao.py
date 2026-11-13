"""
Constantes exclusivas do modo "Perseguição - O Guardião das Trevas".
Ficam num arquivo próprio para não misturar com as constantes dos outros modos.
"""

NOME_MODO = "Perseguição"
SUBTITULO_MODO = "O Guardião das Trevas"

# ---------------- símbolos extras nos mapas ----------------
SIMBOLO_GUARDIAO = "G"           # posição inicial do Guardião
SIMBOLO_SANTUARIO = "L"          # santuário onde se abre a loja

# ---------------- estágios da inteligência do Guardião ----------------
ESTAGIO_VIGILANCIA = "vigilancia"    # patrulha procurando o jogador
ESTAGIO_CACADA = "cacada"            # viu o jogador e o persegue
ESTAGIO_FURIA = "furia"              # depois de muito tempo: persegue sem descanso
ROTULO_ESTAGIO = {
    ESTAGIO_VIGILANCIA: "Vigilância",
    ESTAGIO_CACADA: "Caçada",
    ESTAGIO_FURIA: "FÚRIA",
}

# ---------------- Guardião das Trevas ----------------
TAMANHO_GUARDIAO = 32            # cabe em corredores de 40 px
VELOCIDADE_BASE_GUARDIAO = 100   # pixels/s (o jogador anda a 180)
# (segundos de partida, multiplicador de velocidade): +20%, +40%, +60%
PROGRESSAO_VELOCIDADE = [(0, 1.0), (30, 1.2), (60, 1.4), (90, 1.6)]
TEMPO_FURIA = 90                 # a partir daqui o estágio é FÚRIA
RAIO_DETECCAO = 9                # tiles de caminho para perceber o jogador (vigilância)
RAIO_PERDA = 18                  # além disso o jogador some do "radar" do Guardião
TEMPO_PERDA_JOGADOR = 5.0        # segundos sem enxergar até voltar à vigilância
INTERVALO_BUSCA = 0.5            # segundos entre cada BFS (não roda a cada quadro)
LIMITE_BFS = 120                 # profundidade máxima da busca de caminho
TEMPO_ATORDOADO = 2.0            # segundos parado depois de bater no escudo

# ---------------- progressão infinita (a cada mapa concluído) ----------------
FATOR_VELOCIDADE_POR_MAPA = 0.05     # +5% de velocidade do Guardião a cada mapa
FATOR_VELOCIDADE_MAXIMO_MAPA = 1.5   # teto do fator por mapa
VELOCIDADE_MAXIMA_GUARDIAO = 165     # teto absoluto (px/s): continua menor que o jogador (180)
RAIO_DETECCAO_MAXIMO = 16            # o raio de detecção cresce 1 tile a cada 2 mapas, até aqui
TEMPO_FURIA_MINIMO = 45              # a fúria chega mais cedo a cada mapa, até este mínimo
REDUCAO_FURIA_POR_MAPA = 5           # segundos a menos até a fúria por mapa
ATALHOS_MINIMOS = 4                  # menos atalhos = labirinto mais complexo
MAX_MOEDAS_PERSEGUICAO = 20
MAX_TESOUROS_PERSEGUICAO = 6
MAX_ARMADILHAS_PERSEGUICAO = 12
ESCURIDAO_MAXIMA_PERSEGUICAO = 190
MAPA_COM_UM_SANTUARIO = 8            # a partir deste mapa há só 1 santuário

# ---------------- posicionamento ----------------
DISTANCIA_INICIAL_GUARDIAO = 16  # tiles de caminho entre o início do jogador e o Guardião
DISTANCIA_SEGURA_JOGADOR = 10    # onde o jogador reaparece (longe do Guardião)
DISTANCIA_REAPARECER_GUARDIAO = 14
AMOSTRAS_REPOSICIONAMENTO = 60   # tiles sorteados ao procurar um ponto seguro

# ---------------- proximidade ----------------
INTERVALO_PROXIMIDADE = 0.25     # segundos entre medições da distância
DISTANCIA_PERIGO = 4             # tiles: abaixo disso é perigo
DISTANCIA_ALERTA = 9             # tiles: abaixo disso é alerta
DISTANCIA_CALMA = 14             # tiles: acima disso o indicador fica tranquilo

# ---------------- pontuação ----------------
PONTOS_ESCAPAR = 100
BONUS_SEM_CAPTURA = 50

# ---------------- itens da loja ----------------
MAX_ITENS_POR_TIPO = 9
DURACAO_VELOCIDADE = 8.0         # segundos
FATOR_VELOCIDADE_POCAO = 1.5
DURACAO_INVISIBILIDADE = 5.0
DURACAO_BUSSOLA = 15.0
INTERVALO_BUSSOLA = 0.3          # segundos entre recálculos da seta

ITEM_CURA = "cura"
ITEM_VELOCIDADE = "velocidade"
ITEM_ESCUDO = "escudo"
ITEM_INVISIBILIDADE = "invisibilidade"
ITEM_BUSSOLA = "bussola"

# Catálogo: a ordem define as teclas 1 a 5
CATALOGO = [
    {"id": ITEM_CURA, "nome": "Poção de Cura", "preco": 50,
     "descricao": "Recupera uma vida perdida"},
    {"id": ITEM_VELOCIDADE, "nome": "Poção da Velocidade", "preco": 40,
     "descricao": "Velocidade maior por 8 segundos"},
    {"id": ITEM_ESCUDO, "nome": "Escudo Mágico", "preco": 80,
     "descricao": "Bloqueia uma captura do Guardião"},
    {"id": ITEM_INVISIBILIDADE, "nome": "Poção da Invisibilidade", "preco": 100,
     "descricao": "O Guardião não te vê por 5 segundos"},
    {"id": ITEM_BUSSOLA, "nome": "Bússola Mágica", "preco": 60,
     "descricao": "Seta para a chave (ou a saída) por 15 s"},
]

# ---------------- santuário ----------------
QUANTIDADE_SANTUARIOS = 2
DISTANCIA_INTERACAO_SANTUARIO = 40   # pixels de folga para o jogador "estar perto"

# ---------------- mapa do modo ----------------
ESCURIDAO_PERSEGUICAO = 150
QUANTIDADE_MOEDAS = 14
QUANTIDADE_TESOUROS = 4
QUANTIDADE_ARMADILHAS = 4
ATALHOS_PERSEGUICAO = 12         # muitos atalhos: corredores para fugir em círculos