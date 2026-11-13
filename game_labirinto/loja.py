"""
Santuário do Aventureiro: catálogo, inventário e interface da loja
do modo Perseguição.

A loja NÃO pausa a partida: ela é só uma camada de interface por cima do jogo.
Quem decide o que acontece na partida (gastar ouro, usar itens) é perseguicao.py.
"""

import math

import pygame

from constantes import (
    COR_ALERTA, COR_OURO, COR_SUCESSO, COR_TEXTO, DURACAO_BUSSOLA,
    DURACAO_INVISIBILIDADE, DURACAO_VELOCIDADE, FATOR_POCAO_VELOCIDADE,
    LARGURA_JANELA, MAX_POR_ITEM, PRECO_BUSSOLA, PRECO_ESCUDO,
    PRECO_INVISIBILIDADE, PRECO_POCAO_CURA, PRECO_POCAO_VELOCIDADE,
)
from desenho import desenhar_icone_moeda
from desenho_perseguicao import desenhar_icone_item
from interface import desenhar_painel, desenhar_texto_contorno

NOME_LOJA = "SANTUÁRIO DO AVENTUREIRO"
TEMPO_AVISO_LOJA = 1.6

# Catálogo inicial (preços em constantes.py). 'tecla' = atalho de uso no inventário.
CATALOGO = [
    {"id": "cura", "nome": "Poção de Cura", "preco": PRECO_POCAO_CURA, "tecla": "1",
     "descricao": "Recupera 1 vida perdida (sem passar do máximo)"},
    {"id": "velocidade", "nome": "Poção da Velocidade", "preco": PRECO_POCAO_VELOCIDADE,
     "tecla": "2", "descricao": f"+{int((FATOR_POCAO_VELOCIDADE - 1) * 100)}% de velocidade "
                                f"por {DURACAO_VELOCIDADE:g} s"},
    {"id": "escudo", "nome": "Escudo Mágico", "preco": PRECO_ESCUDO, "tecla": "3",
     "descricao": "Bloqueia 1 captura do Guardião (automático)"},
    {"id": "invisibilidade", "nome": "Poção de Invisibilidade", "preco": PRECO_INVISIBILIDADE,
     "tecla": "4", "descricao": f"O Guardião não te detecta por {DURACAO_INVISIBILIDADE:g} s"},
    {"id": "bussola", "nome": "Bússola Mágica", "preco": PRECO_BUSSOLA, "tecla": "5",
     "descricao": f"Aponta a chave (ou a saída) por {DURACAO_BUSSOLA:g} s"},
]
ITENS_POR_ID = {item["id"]: item for item in CATALOGO}


class Inventario:
    """Quantidade de cada item comprado (exclusivo da partida de perseguição)."""

    def __init__(self):
        self.quantidades = {item["id"]: 0 for item in CATALOGO}

    def quantidade(self, identificador):
        return self.quantidades.get(identificador, 0)

    def cheio(self, identificador):
        return self.quantidade(identificador) >= MAX_POR_ITEM

    def adicionar(self, identificador):
        if identificador not in self.quantidades or self.cheio(identificador):
            return False
        self.quantidades[identificador] += 1
        return True

    def consumir(self, identificador):
        """Gasta uma unidade. Retorna False se não houver nenhuma."""
        if self.quantidade(identificador) <= 0:
            return False
        self.quantidades[identificador] -= 1
        return True


def comprar(identificador, ouro, inventario):
    """
    Regra da compra (sem efeitos visuais). Retorna (novo_ouro, sucesso, mensagem).
    Compras inválidas não mudam nada.
    """
    item = ITENS_POR_ID.get(identificador)
    if item is None:
        return ouro, False, "Item desconhecido."
    if ouro < item["preco"]:
        return ouro, False, f"Ouro insuficiente! Faltam {item['preco'] - ouro}."
    if inventario.cheio(identificador):
        return ouro, False, f"Limite de {MAX_POR_ITEM} unidades atingido."
    inventario.adicionar(identificador)
    return ouro - item["preco"], True, f"{item['nome']} comprada!" \
        if identificador != "escudo" else "Escudo Mágico comprado!"


class Loja:
    """Estado e desenho da janela da loja (aberta/fechada, seleção, avisos)."""

    PAINEL = pygame.Rect(LARGURA_JANELA // 2 - 290, 122, 580, 470)   # abaixo dos avisos
    ALTURA_LINHA = 56

    def __init__(self):
        self.aberta = False
        self.selecionado = 0
        self.aviso = ""
        self.cor_aviso = COR_TEXTO
        self.tempo_aviso = 0.0
        self.tempo = 0.0
        topo = self.PAINEL.y + 86
        self.linhas = [pygame.Rect(self.PAINEL.x + 18, topo + i * self.ALTURA_LINHA,
                                   self.PAINEL.w - 36, self.ALTURA_LINHA - 6)
                       for i in range(len(CATALOGO))]
        self.botao_fechar = pygame.Rect(0, 0, 200, 38)
        self.botao_fechar.center = (self.PAINEL.centerx,
                                    topo + len(CATALOGO) * self.ALTURA_LINHA + 18)

    @property
    def total_opcoes(self):
        return len(CATALOGO) + 1                 # itens + "Fechar"

    def abrir(self):
        self.aberta = True
        self.selecionado = 0
        self.tempo = 0.0
        self.aviso = ""

    def fechar(self):
        self.aberta = False

    def mover(self, delta):
        self.selecionado = (self.selecionado + delta) % self.total_opcoes

    def acao_selecionada(self):
        """Id do item selecionado ou 'fechar'."""
        if self.selecionado >= len(CATALOGO):
            return "fechar"
        return CATALOGO[self.selecionado]["id"]

    def opcao_no_ponto(self, posicao):
        """Índice da opção sob o mouse (ou None)."""
        for i, retangulo in enumerate(self.linhas):
            if retangulo.collidepoint(posicao):
                return i
        if self.botao_fechar.collidepoint(posicao):
            return len(CATALOGO)
        return None

    def avisar(self, texto, sucesso):
        self.aviso = texto
        self.cor_aviso = COR_SUCESSO if sucesso else COR_ALERTA
        self.tempo_aviso = TEMPO_AVISO_LOJA

    def atualizar(self, dt):
        self.tempo += dt
        self.tempo_aviso = max(0.0, self.tempo_aviso - dt)

    # ------------------------------------------------------------------
    def desenhar(self, tela, fontes, ouro, inventario):
        """fontes = (titulo, normal, pequena)."""
        fonte_titulo, fonte, fonte_pequena = fontes
        painel = self.PAINEL
        desenhar_painel(tela, painel, 225)
        meio = painel.centerx
        desenhar_texto_contorno(tela, fonte_titulo, NOME_LOJA, COR_OURO,
                                (meio, painel.y + 30), (60, 30, 5), 3)
        # saldo atual
        texto_ouro = f"Seu ouro: {ouro}"
        imagem = fonte.render(texto_ouro, True, COR_OURO)
        x_ouro = meio - imagem.get_width() // 2 + 14
        desenhar_icone_moeda(tela, x_ouro - 30, painel.y + 52, self.tempo)
        tela.blit(imagem, (x_ouro, painel.y + 52))

        for i, (item, linha) in enumerate(zip(CATALOGO, self.linhas)):
            ativo = i == self.selecionado
            quantidade = inventario.quantidade(item["id"])
            pode_pagar = ouro >= item["preco"]
            fundo = (70, 54, 30) if ativo else (34, 28, 44)
            pygame.draw.rect(tela, fundo, linha, border_radius=8)
            pygame.draw.rect(tela, COR_OURO if ativo else (80, 70, 96), linha, 2, border_radius=8)
            if ativo:
                pulso = int(abs(math.sin(self.tempo * 5)) * 3)
                pygame.draw.rect(tela, (255, 232, 140), linha.inflate(pulso * 2, pulso * 2), 1,
                                 border_radius=10)
            desenhar_icone_item(tela, item["id"], (linha.x + 28, linha.centery), self.tempo, 1.3)
            tela.blit(fonte.render(f"[{item['tecla']}] {item['nome']}", True,
                                   (255, 240, 180) if ativo else COR_TEXTO),
                      (linha.x + 56, linha.y + 4))
            tela.blit(fonte_pequena.render(item["descricao"], True, (200, 190, 170)),
                      (linha.x + 56, linha.y + 29))
            # preço (vermelho se não der para pagar) e quantidade no inventário
            cor_preco = COR_OURO if pode_pagar else COR_ALERTA
            preco = fonte.render(str(item["preco"]), True, cor_preco)
            tela.blit(preco, preco.get_rect(topright=(linha.right - 14, linha.y + 4)))
            desenhar_icone_moeda(tela, linha.right - 44 - preco.get_width(), linha.y + 4,
                                 self.tempo)
            cor_qtd = COR_SUCESSO if quantidade else (150, 140, 160)
            qtd = fonte_pequena.render(f"Possui: {quantidade}/{MAX_POR_ITEM}", True, cor_qtd)
            tela.blit(qtd, qtd.get_rect(topright=(linha.right - 14, linha.y + 30)))

        ativo = self.selecionado == len(CATALOGO)
        r = self.botao_fechar
        pygame.draw.rect(tela, (96, 74, 40) if ativo else (54, 48, 66), r, border_radius=10)
        pygame.draw.rect(tela, COR_OURO if ativo else (124, 108, 146), r, 3, border_radius=10)
        desenhar_texto_contorno(tela, fonte, "Fechar", (255, 240, 180) if ativo else COR_TEXTO,
                                r.center)

        if self.tempo_aviso > 0:
            alfa = int(255 * min(1.0, self.tempo_aviso / 0.4))
            desenhar_texto_contorno(tela, fonte, self.aviso, self.cor_aviso,
                                    (meio, painel.bottom - 50), (10, 8, 14), 2, alfa)
        desenhar_texto_contorno(tela, fonte_pequena,
                                "Setas: escolher   ENTER: comprar   E/ESC: fechar   "
                                "(o Guardião não para!)",
                                COR_TEXTO, (meio, painel.bottom - 20), (10, 8, 14), 1)
