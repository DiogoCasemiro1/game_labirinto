"""
Loja "Santuário do Aventureiro": estado da loja (aberta, item selecionado, avisos)
e a interface medieval. As regras de compra ficam em ModoPerseguicao.comprar().
"""

import pygame

from constantes import COR_ALERTA, COR_OURO, COR_SUCESSO, COR_TEXTO, LARGURA_JANELA
from constantes_perseguicao import CATALOGO
from desenho import desenhar_icone_moeda
from desenho_perseguicao import desenhar_icone_item
from interface import desenhar_painel, desenhar_texto_contorno

TEMPO_AVISO = 1.8


class Loja:
    def __init__(self):
        self.aberta = False
        self.selecionado = 0
        self.aviso = ""
        self.aviso_erro = False
        self.tempo_aviso = 0.0
        self.painel = pygame.Rect(110, 56, LARGURA_JANELA - 220, 528)
        self.linhas = [pygame.Rect(self.painel.x + 28, self.painel.y + 112 + i * 70,
                                   self.painel.w - 56, 64) for i in range(len(CATALOGO))]
        self.botao_fechar = pygame.Rect(self.painel.right - 168, self.painel.y + 62, 140, 36)

    def abrir(self):
        self.aberta = True
        self.selecionado = 0
        self.aviso = ""

    def fechar(self):
        self.aberta = False

    def mover(self, delta):
        self.selecionado = (self.selecionado + delta) % len(CATALOGO)

    def avisar(self, texto, erro=False):
        self.aviso = texto
        self.aviso_erro = erro
        self.tempo_aviso = TEMPO_AVISO

    def atualizar(self, dt):
        if self.tempo_aviso > 0:
            self.tempo_aviso -= dt

    def indice_em(self, posicao):
        """Índice do item sob o ponto (ou None)."""
        for i, linha in enumerate(self.linhas):
            if linha.collidepoint(posicao):
                return i
        return None

    def desenhar(self, tela, fontes, saldo, inventario, tempo):
        fonte_titulo, fonte, fonte_pequena = fontes
        desenhar_painel(tela, self.painel, 238)
        meio = self.painel.centerx
        desenhar_texto_contorno(tela, fonte_titulo, "SANTUÁRIO DO AVENTUREIRO", COR_OURO,
                                (meio, self.painel.y + 34), (60, 30, 5), 3)

        # saldo
        desenhar_icone_moeda(tela, self.painel.x + 34, self.painel.y + 62, tempo)
        saldo_img = fonte.render(f"Moedas: {saldo}", True, COR_OURO)
        tela.blit(saldo_img, (self.painel.x + 66, self.painel.y + 63))
        # botão fechar
        pygame.draw.rect(tela, (70, 40, 40), self.botao_fechar, border_radius=8)
        pygame.draw.rect(tela, (200, 120, 110), self.botao_fechar, 2, border_radius=8)
        fechar = fonte_pequena.render("Fechar [E]", True, COR_TEXTO)
        tela.blit(fechar, fechar.get_rect(center=self.botao_fechar.center))

        for i, (item, linha) in enumerate(zip(CATALOGO, self.linhas)):
            ativa = i == self.selecionado
            pode = saldo >= item["preco"]
            pygame.draw.rect(tela, (92, 70, 38) if ativa else (44, 38, 56), linha, border_radius=10)
            pygame.draw.rect(tela, COR_OURO if ativa else (110, 98, 130), linha, 2, border_radius=10)
            tecla = fonte_pequena.render(f"[{i + 1}]", True, COR_OURO)
            tela.blit(tecla, (linha.x + 12, linha.centery - 10))
            desenhar_icone_item(tela, item["id"], linha.x + 62, linha.centery, tempo)
            nome = fonte.render(item["nome"], True, COR_TEXTO)
            tela.blit(nome, (linha.x + 96, linha.y + 8))
            descricao = fonte_pequena.render(item["descricao"], True, (200, 190, 170))
            tela.blit(descricao, (linha.x + 96, linha.y + 36))
            preco = fonte.render(f"{item['preco']} moedas", True,
                                 COR_SUCESSO if pode else COR_ALERTA)
            tela.blit(preco, preco.get_rect(topright=(linha.right - 16, linha.y + 8)))
            qtd = fonte_pequena.render(f"No inventário: {inventario.quantidade(item['id'])}",
                                       True, COR_TEXTO)
            tela.blit(qtd, qtd.get_rect(topright=(linha.right - 16, linha.y + 36)))

        if self.tempo_aviso > 0 and self.aviso:
            cor = COR_ALERTA if self.aviso_erro else COR_SUCESSO
            desenhar_texto_contorno(tela, fonte, self.aviso, cor,
                                    (meio, self.painel.bottom - 50), (10, 8, 14), 2)
        dica = "Setas: escolher  |  ENTER ou clique: comprar  |  1 a 5: compra rápida  |  E ou ESC: fechar"
        desenhar_texto_contorno(tela, fonte_pequena, dica, COR_TEXTO,
                                (meio, self.painel.bottom - 22), (10, 8, 14), 1)