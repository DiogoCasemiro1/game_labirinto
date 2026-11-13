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
ESTADO_MODOS = "modos"             # escolha entre campanha e infinito
ESTADO_INSTRUCOES = "instrucoes"
ESTADO_JOGANDO = "jogando"
ESTADO_PAUSADO = "pausado"
ESTADO_GAME_OVER = "game_over"
ESTADO_VITORIA = "vitoria"

# Direções possíveis num labirinto de grade: (delta_coluna, delta_linha)
DIRECOES = [(1, 0), (-1, 0), (0, 1), (0, -1)]


# ======================================================================
# MODO PERSEGUIÇÃO - O GUARDIÃO DAS TREVAS
# (valores usados SOMENTE pelo terceiro modo; os modos originais não os leem)
# ======================================================================
ACAO_PERSEGUICAO = "perseguicao"     # ação do botão no menu de modos
NOME_MODO_PERSEGUICAO = "Perseguição - O Guardião das Trevas"

# ---------------- símbolos extras dos mapas do modo ----------------
GUARDIAO = "G"               # posição inicial do Guardião
SANTUARIO = "$"              # santuário onde se abre a loja
ESCONDERIJO = "H"            # nicho onde o jogador se esconde por alguns segundos
PASSAGEM_SECRETA = "%"       # parede falsa: o jogador atravessa, o Guardião não

# ---------------- geração do mapa ----------------
NIVEL_BASE_PERSEGUICAO = 4   # dificuldade passada ao gerador original (gerar_nivel)
ATALHOS_EXTRAS_PERSEGUICAO = 10   # mais ciclos = mais rotas de fuga
MOEDAS_EXTRAS_PERSEGUICAO = 8
TESOUROS_EXTRAS_PERSEGUICAO = 1
QTD_SANTUARIOS = 2
QTD_ESCONDERIJOS = 3
QTD_PASSAGENS_SECRETAS = 3
DIST_MIN_GUARDIAO_INICIO = 16     # em tiles de caminho
DIST_MIN_ENTRE_SANTUARIOS = 8
ATALHO_MIN_PASSAGEM = 10          # a passagem secreta deve "economizar" pelo menos isto
ESCURIDAO_PERSEGUICAO = 205        # mais escuro: explorar (e a bússola) importam

# ---------------- jogador ----------------
VIDAS_PERSEGUICAO = 3
MAX_VIDAS_PERSEGUICAO = 3

# ---------------- Guardião ----------------
TAMANHO_GUARDIAO = 34
MARGEM_HITBOX_GUARDIAO = 10
VELOCIDADE_GUARDIAO = 110         # pixels/s (o jogador anda a 180)
# Progressão da velocidade: (a partir de X segundos, multiplicador)
PROGRESSAO_VELOCIDADE_GUARDIAO = [(0, 1.0), (30, 1.2), (60, 1.4), (90, 1.6)]
TEMPO_FURIA = 90                  # segundos de partida para entrar em FÚRIA
TEMPO_DESPERTAR = 3.0             # o Guardião demora a acordar no início
TEMPO_DESPERTAR_APOS_CAPTURA = 2.0
RAIO_DETECCAO_GUARDIAO = 8        # tiles de caminho para sair da vigilância
RAIO_PERDA_GUARDIAO = 14          # na caçada, além disto ele começa a perder o rastro
TEMPO_PERDER_RASTRO = 3.0         # segundos longe para voltar à vigilância
INTERVALO_PERCEPCAO = 0.3         # de quanto em quanto tempo o BFS é refeito
INTERVALO_PISTA = 5.0             # na vigilância, ele "ouve" a região do jogador
RAIO_PISTA = 4                    # imprecisão (em tiles) da pista
LIMITE_BFS_TOTAL = COLUNAS * LINHAS   # limite que cobre o mapa inteiro
TEMPO_ATORDOADO_ESCUDO = 1.5      # o escudo repele o Guardião
TEMPO_ATORDOADO_ARMADILHA = 1.5   # espinhos atrasam o Guardião
IMUNIDADE_ARMADILHA = 3.0         # depois de atordoado por espinhos

ESTAGIO_VIGILANCIA = "VIGILÂNCIA"
ESTAGIO_CACADA = "CAÇADA"
ESTAGIO_FURIA = "FÚRIA"

# ---------------- captura e reposicionamento ----------------
TEMPO_ANIMACAO_CAPTURA = 1.0
DIST_MIN_RESPAWN = 10             # jogador renasce a pelo menos isto do Guardião
DIST_MIN_GUARDIAO_RESPAWN = 12    # Guardião volta a pelo menos isto do jogador

# ---------------- proximidade (em tiles de caminho) ----------------
PROXIMIDADE_ALERTA = 14           # abaixo disto o indicador sai do "tranquilo"
PROXIMIDADE_PERIGO = 6            # abaixo disto: perigo
INTERVALO_PROXIMIDADE = 0.25
INTERVALO_BATIMENTO_ALERTA = 1.1  # som de coração (segundos entre batidas)
INTERVALO_BATIMENTO_PERIGO = 0.55

# ---------------- pontuação e ouro (saldo da loja) ----------------
PONTOS_FUGA = 100
BONUS_SEM_CAPTURA = 50
OURO_MOEDA = 10                   # ouro (saldo) ganho por moeda
OURO_TESOURO = 50                 # ouro ganho por tesouro

# ---------------- loja: preços ----------------
PRECO_POCAO_CURA = 50
PRECO_POCAO_VELOCIDADE = 40
PRECO_ESCUDO = 80
PRECO_INVISIBILIDADE = 100
PRECO_BUSSOLA = 60
MAX_POR_ITEM = 5                  # limite de cada item no inventário
DISTANCIA_SANTUARIO = 34          # pixels: alcance para abrir a loja

# ---------------- efeitos dos itens ----------------
DURACAO_VELOCIDADE = 8.0
FATOR_POCAO_VELOCIDADE = 1.5
DURACAO_INVISIBILIDADE = 5.0
DURACAO_BUSSOLA = 8.0
INTERVALO_BUSSOLA = 0.5           # recálculo da direção indicada

# ---------------- elementos especiais ----------------
DURACAO_ESCONDERIJO = 4.0
RECARGA_ESCONDERIJO = 15.0
DURACAO_LENTIDAO = 2.0            # espinhos deixam o jogador lento
FATOR_LENTIDAO = 0.55

COR_GUARDIAO = (120, 60, 200)
COR_TRANQUILO = (110, 200, 120)