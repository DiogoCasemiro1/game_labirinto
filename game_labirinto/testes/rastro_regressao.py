"""
Executa a CAMPANHA e o modo INFINITO com entradas e sementes fixas e imprime
um rastro (JSON) do estado a cada quadro. Rodado sobre o projeto original e
sobre o modificado: os rastros precisam ser idênticos (sem regressões).
Uso: python rastro_regressao.py <pasta_do_projeto> [quadros] > rastro.json
(rode no projeto original e no modificado e compare os dois arquivos)
"""
import json
import os
import random
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, sys.argv[1])

import pygame  # noqa: E402
import main  # noqa: E402
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bot  # noqa: E402
import gerador  # noqa: E402

main.gerar_nivel = lambda numero: gerador.gerar_nivel(numero, 1000 + numero)

roteiro = [(1, 0)] * 40 + [(0, 1)] * 70 + [(1, 0)] * 60 + [(0, -1)] * 50 + [(-1, 1)] * 40 \
    + [(0, 0)] * 30 + [(1, 1)] * 80 + [(-1, 0)] * 60 + [(0, 1)] * 90 + [(1, -1)] * 60
rastro = []
for modo in ("campanha", "infinito"):
    random.seed(12345)
    jogo = main.Jogo()
    jogo.executar_acao("iniciar")
    jogo.executar_acao(modo)
    indice = {"i": 0}

    def piloto():
        # primeiros quadros: roteiro fixo; depois, o bot busca chave e porta
        if indice["i"] < 300:
            return roteiro[indice["i"] % len(roteiro)]
        alvo, pixel = bot.objetivo(jogo.labirinto, jogo.itens)
        return bot.direcao_para(jogo.labirinto, jogo.jogador, alvo, pixel)

    jogo.jogador.ler_teclado = piloto
    fases = set()
    for quadro in range(int(sys.argv[2]) if len(sys.argv) > 2 else 12000):
        indice["i"] = quadro
        if quadro == 500:                      # pausa e volta
            jogo.tratar_tecla(pygame.K_p)
        if quadro == 520:
            jogo.tratar_tecla(pygame.K_p)
        jogo.atualizar(1 / 60, 1 / 60)
        if quadro % 50 == 0:
            jogo.desenhar()
        if jogo.estado in ("game_over", "vitoria") and jogo.tempo_fim > 1:
            fases.add((jogo.estado, jogo.numero_fase))
            jogo.executar_acao("reiniciar")
            jogo.jogador.ler_teclado = piloto
        jogo.jogador.ler_teclado = piloto
        fases.add(("fase", jogo.numero_fase))
        if quadro % 3:
            continue
        rastro.append([modo, quadro, jogo.estado, jogo.numero_fase, jogo.pontos,
                       jogo.jogador.vidas, round(jogo.jogador.x, 3), round(jogo.jogador.y, 3),
                       round(jogo.tempo_restante, 3), len(jogo.itens),
                       [(round(i.x, 2), round(i.y, 2)) for i in jogo.inimigos]])
    rastro.append([modo, "resumo", sorted(fases)])
    # menus e pausa
    jogo.executar_acao("menu")
    rastro.append([modo, "menu", jogo.estado, [b.acao for b in jogo.menu_principal.botoes]])
    pygame.quit()
print(json.dumps(rastro))
