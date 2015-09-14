from pot import Pot
from player import FOLD_STATE, ALL_IN_STATE, CALL_ACTION, CHECK_ACTION, RAISE_ACTION, BET_ACTION

FOLD_NOTIFY_MESSAGE = "{} folds."
ALL_IN_NOTIFY_MESSAGE = "{} is all in."
CHECK_NOTIFY_MESSAGE = "{} checks."
BET_NOTIFY_MESSAGE = "{} bets ${}."

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

    def get_player_pot(self, player):
        for pot in reversed(self.pots):
            if player in pot.players:
                return pot

    def fold(self, player):
        player.state = FOLD_STATE
        player.action = FOLD_STATE
        for pot in self.pots:
            pot.players.remove(player)

        self.game.chat.message(FOLD_NOTIFY_MESSAGE.format(player))

    def all_in(self, player):
        player.state = ALL_IN_STATE
        player.action = ALL_IN_STATE
        self.game.chat.message(ALL_IN_NOTIFY_MESSAGE.format(player))

        #TODO make side pot

    def call(self, player):
        player.action = CALL_ACTION

    def raise_bid(self, player, amount):
        player.action = "{} ${}".format(RAISE_ACTION, amount)
        difference = self.current_bet - player.bet
        total_amount = amount + difference
        self.current_bet += total_amount
        PotManager.place_bet(total_amount, player, self.get_player_pot(player))

    def check(self, player):
        player.action = CHECK_ACTION
        self.game.chat.message(CHECK_NOTIFY_MESSAGE.format(player))

    def bet(self, player, amount):
        player.action = "{} ${}".format(BET_ACTION, amount)
        self.current_bet += amount
        PotManager.place_bet(amount, player, self.get_player_pot(player))
        self.game.chat.message(BET_NOTIFY_MESSAGE.format(player, amount))

    def display_pot(self):
        main_pot = True
        for pot in self.pots:
            if main_pot:
                self.game.message('Main Pot: ${}'.format(pot.amount))
                main_pot = False
            else:
                self.game.message('Side Pot: ${} | Players {}'.format(pot.amount, pot.players))
