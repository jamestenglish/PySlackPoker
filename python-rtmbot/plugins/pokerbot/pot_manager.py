from pot import Pot


class PotManager:
    def __init__(self, game):
        self.game = game
        self.pots = []
        self.current_bet = 0
        self.big_blind = None
        self.small_blind = None

    def post_small_blind(self, player):
        if player.money < 1:
            return False

        pot = Pot(player, 1)
        player.money -= 1
        player.bet = 1
        player.action = "SMALL BLIND"

        self.pots.append(pot)
        self.game.message('<@{}> posts small blind $1'.format(player.slack_id))
        self.current_bet = 1
        self.big_blind = None
        self.small_blind = player

        return True

    def post_big_blind(self, player):
        if player.money < 2:
            return False

        self.game.message('<@{}> posts big blind $2'.format(player.slack_id))
        self.pots[0].players.append(player)
        PotManager.place_bet(2, player, self.pots[0])
        player.bet = 2
        player.action = "BIG BLIND"
        self.current_bet = 2
        self.big_blind = player

        return True

    @staticmethod
    def place_bet(amount, player, pot):
        pot.amount += amount
        player.money -= amount

    def fold(self, player):
        pass

    def all_in(self, player):
        pass

    def call(self, player):
        pass

    def raise_bid(self, player, amount):
        pass

    def check(self, player):
        pass

    def bet(self, player, amount):
        pass


    def display_pot(self):
        main_pot = True
        for pot in self.pots:
            if main_pot:
                self.game.message('Main Pot: ${}'.format(pot.amount))
                main_pot = False
            else:
                self.game.message('Side Pot: ${} | Players {}'.format(pot.amount, pot.players))
