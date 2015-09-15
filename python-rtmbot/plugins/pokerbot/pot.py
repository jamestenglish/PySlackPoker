class Pot:
    def __init__(self, name, player, amount, locked=False):
        self.name = name
        self.players = [player]
        self.amount = amount
        self.locked = locked