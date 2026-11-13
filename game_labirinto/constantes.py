"""
Constantes do jogo Labirinto: A Fuga.
Todos os valores configuráveis ficam aqui, para evitar "números mágicos"
espalhados pelo código e facilitar ajustes de dificuldade.
"""

# ---------------- janela e mapa ----------------
LARGURA_JANELA = 960
ALTURA_JANELA = 640
FPS = 60

TAMANHO_TILE = 40            # cada quadradinho do mapa tem 40x40 pixels
ALTURA_HUD = 80              # faixa superior reservada para a interface
COLUNAS = LARGURA_JANELA // TAMANHO_TILE                 # 24
LINHAS = (ALTURA_JANELA - ALTURA_HUD) // TAMANHO_TILE    # 14

# ---------------- jogador ----------------
VELOCIDADE_JOGADOR = 180     # pixels por SEGUNDO (independe do FPS)
TAMANHO_JOGADOR = 26         # menor que o tile para passar nos corredores
MARGEM_HITBOX_JOGADOR = 8    # a área de dano é menor que o desenho (mais justo)
VIDAS_INICIAIS = 3
TEMPO_INVULNERAVEL = 1.5     # segundos de proteção após perder uma vida

# ---------------- itens e pontuação ----------------
TAMANHO_ITEM = 22            # área de coleta de moedas, chaves e baús
PONTOS_MOEDA = 10
PONTOS_TESOURO = 50

# ---------------- inimigos ----------------
TAMANHO_INIMIGO = 28
MARGEM_HITBOX_INIMIGO = 8
VELOCIDADE_ESQUELETO = 70    # patrulha lenta (pixels por segundo)
VELOCIDADE_GOBLIN = 100      # perseguidor mais rápido, mas ainda mais lento que o jogador
RAIO_PERSEGUICAO = 7         # distância máxima (em tiles de caminho) para o goblin perceber o jogador
CHANCE_VIRAR = 0.25          # chance de o patrulheiro mudar de rumo num cruzamento

# ---------------- chefe (dragão) ----------------
TAMANHO_CHEFE = 36           # ainda cabe num corredor de 40 px
VELOCIDADE_CHEFE = 115
RAIO_CHEFE = 20              # o dragão percebe o jogador de bem mais longe

# ---------------- armadilhas de espinhos ----------------
TEMPO_ARMADILHA_RECOLHIDA = 2.0   # espinhos escondidos (os últimos instantes são o aviso)
TEMPO_ARMADILHA_ALERTA = 0.6      # aviso visual antes de os espinhos subirem
TEMPO_ARMADILHA_ATIVA = 1.0       # espinhos para fora (causam dano)
MARGEM_ARMADILHA = 12             # a área de dano é menor que o tile

# ---------------- tamanho dos sprites (imagens PNG) na tela ----------------
TAMANHO_SPRITE_PERSONAGEM = 36   # jogador, esqueleto e goblin
TAMANHO_SPRITE_CHEFE = 40
TAMANHO_SPRITE_ITEM = 28         # moeda, chave e baú
FPS_ANIMACAO = 8                 # quadros por segundo das animações em PNG

# ---------------- iluminação e efeitos visuais ----------------
LUZ_ATIVADA = True               # tecla L liga/desliga a iluminação durante o jogo
RAIO_LUZ_JOGADOR = 150           # pixels
RAIO_LUZ_TOCHA = 100
MAX_TOCHAS = 9                   # tochas por fase
DISTANCIA_MIN_TOCHAS = 5         # distância mínima entre tochas (em tiles)
TEMPO_TREMOR = 0.35              # segundos de tremor de tela ao levar dano
INTENSIDADE_TREMOR = 5           # pixels
TEMPO_FLASH_DANO = 0.4           # clarão vermelho ao levar dano
TEMPO_FADE = 0.4                 # fade entre fases
TEMPO_TITULO_FASE = 2.2          # faixa com o nome da fase
TEMPO_ABERTURA_PORTA = 0.7       # animação da porta abrindo
INTERVALO_POEIRA = 0.16          # segundos entre nuvens de poeira ao andar
MAX_PARTICULAS = 500

# ---------------- dificuldade do modo infinito ----------------
# A dificuldade define apenas as vidas iniciais (campanha e perseguição não usam isto)
DIFICULDADES_INFINITO = {
    "facil": {"nome": "Fácil", "vidas": 5},
    "medio": {"nome": "Médio", "vidas": 3},
    "dificil": {"nome": "Difícil", "vidas": 1},
}
DIFICULDADE_PADRAO = "medio"

# ---------------- modo infinito ----------------
MODO_INFINITO = True             # True: fases geradas sem fim. False: as 5 fases da campanha
INTERVALO_CHEFE = 5              # a cada 5 fases aparece um dragão
MAX_VIDAS = 5                    # limite de vidas (ganha-se 1 ao vencer cada chefe)

# ---------------- interface ----------------
TEMPO_MENSAGEM = 2.0         # segundos que um aviso fica na tela
TEMPO_ALERTA = 10            # abaixo disso o cronômetro fica vermelho

# ---------------- cores (R, G, B) ----------------
COR_FUNDO = (20, 16, 24)
# Paredes em tons azulados e claros; chão em tons marrons e escuros (bom contraste)
COR_PAREDE = (122, 114, 132)
COR_PAREDE_CLARA = (160, 152, 172)
COR_PAREDE_ESCURA = (72, 66, 84)
COR_TOPO_PAREDE = (96, 100, 126)     # parte de cima das paredes (vista de cima)
COR_TOPO_LAJE = (114, 118, 146)      # lajes em relevo no topo das paredes
COR_CONTORNO_PAREDE = (18, 16, 26)   # contorno escuro onde a parede encontra o chão
COR_CHAO = (46, 38, 40)
COR_CHAO_DETALHE = (52, 43, 45)
COR_CHAO_JUNTA = (32, 26, 29)
COR_TOCHA = (255, 170, 60)
COR_HUD = (30, 24, 36)
COR_TEXTO = (240, 230, 200)
COR_OURO = (240, 200, 60)
COR_OURO_ESCURO = (170, 125, 20)
COR_PORTA = (120, 78, 40)
COR_PORTA_ESCURA = (70, 44, 20)
COR_VIDA = (200, 40, 50)
COR_ALERTA = (240, 70, 60)
COR_SUCESSO = (120, 220, 120)

# ---------------- símbolos usados nos mapas ----------------
PAREDE = "#"
CHAO = "."
INICIO = "P"
SAIDA = "S"
CHAVE = "K"
MOEDA = "o"
TESOURO = "T"
ESQUELETO = "E"              # inimigo que patrulha
GOBLIN = "X"                 # inimigo que persegue
ARMADILHA = "^"              # espinhos que sobem e descem
CHEFE = "B"                  # dragão guardião

# Tipos de item
TIPO_CHAVE = "chave"
TIPO_MOEDA = "moeda"
TIPO_TESOURO = "tesouro"
SIMBOLO_PARA_TIPO = {CHAVE: TIPO_CHAVE, MOEDA: TIPO_MOEDA, TESOURO: TIPO_TESOURO}

# Estados do jogo
ESTADO_MENU = "menu"
ESTADO_MODOS = "modos"             # escolha entre campanha, infinito e perseguição
ESTADO_DIFICULDADE = "dificuldade" # escolha da dificuldade do modo infinito
ESTADO_INSTRUCOES = "instrucoes"
ESTADO_JOGANDO = "jogando"
ESTADO_PAUSADO = "pausado"
ESTADO_GAME_OVER = "game_over"
ESTADO_VITORIA = "vitoria"

# Direções possíveis num labirinto de grade: (delta_coluna, delta_linha)
DIRECOES = [(1, 0), (-1, 0), (0, 1), (0, -1)]