class Pot:
    def __init__(self, name, player, small_blind):
        self.name = name
        self.players = [player]
        self.amount = small_blind