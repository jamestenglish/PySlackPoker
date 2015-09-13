from pot import Pot


class PotManager:
    def __init__(self, game):
        self.game = game
        self.pots = []

    def post_small_blind(self, player):
        if player.money < 1:
            return False

        pot = Pot(player, 1)
        player.money -= 1
        player.bet = 1
        player.action = "small blind"

        self.pots.append(pot)
        self.game.message('<@{}> posts small blind $1'.format(player.slack_id))

        return True

    def post_big_blind(self, player):
        if player.money < 2:
            return False

        self.game.message('<@{}> posts big blind $2'.format(player.slack_id))
        self.pots[0].players.append(player)
        self.pots[0].amount += 2
        player.money -= 2
        player.bet = 2
        player.action = "big blind"

        return True

    def display_pot(self):
        main_pot = True
        for pot in self.pots:
            if main_pot:
                self.game.message('Main Pot: ${}'.format(pot.amount))
                main_pot = False
            else:
                self.game.message('Side Pot: ${} | Players {}'.format(pot.amount, pot.players))
