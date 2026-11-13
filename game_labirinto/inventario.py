"""Inventário do modo Perseguição: quantidade de cada item comprado."""

from constantes_perseguicao import CATALOGO, MAX_ITENS_POR_TIPO


class Inventario:
    def __init__(self):
        self.itens = {item["id"]: 0 for item in CATALOGO}

    def quantidade(self, item_id):
        return self.itens.get(item_id, 0)

    def tem(self, item_id):
        return self.quantidade(item_id) > 0

    def cheio(self, item_id):
        """True se já tem o máximo permitido desse item."""
        return self.quantidade(item_id) >= MAX_ITENS_POR_TIPO

    def adicionar(self, item_id):
        """Guarda uma unidade. Retorna False se o inventário desse item está cheio."""
        if item_id not in self.itens or self.cheio(item_id):
            return False
        self.itens[item_id] += 1
        return True

    def consumir(self, item_id):
        """Gasta uma unidade. Retorna False se não havia nenhuma."""
        if not self.tem(item_id):
            return False
        self.itens[item_id] -= 1
        return True