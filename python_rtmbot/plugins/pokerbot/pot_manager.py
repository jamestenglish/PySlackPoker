from pot import Pot
from player import Player

FOLD_NOTIFY_MESSAGE = "{} folds."
ALL_IN_NOTIFY_MESSAGE = "{} is all in."
CHECK_NOTIFY_MESSAGE = "{} checks."
BET_NOTIFY_MESSAGE = "{} bets ${}."
CALL_NOTIFY_MESSAGE = "{} calls."


class PotManager:
    def __init__(self, chat):
        self.chat = chat
        self.pots = []
        self.current_bet = 0
        self.big_blind = None
        self.small_blind = None

    def post_small_blind(self, player):
        if player.money < 1:
            return False

        pot = Pot('Main Pot', player, 1)
        player.money -= 1
        player.bet = 1
        player.action = "SMALL BLIND"

        self.pots.append(pot)
        self.chat.message('<@{}> posts small blind $1'.format(player.slack_id))
        self.current_bet = 1
        self.big_blind = None
        self.small_blind = player

        return True

    def post_big_blind(self, player):
        if player.money < 2:
            return False

        self.chat.message('<@{}> posts big blind $2'.format(player.slack_id))
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
        player.state = Player.FOLD_STATE
        player.action = Player.FOLD_STATE
        for pot in self.pots:
            pot.players.remove(player)

        self.chat.message(FOLD_NOTIFY_MESSAGE.format(player))

    def all_in(self, player):
        player.state = Player.ALL_IN_STATE
        player.action = Player.ALL_IN_STATE
        self.chat.message(ALL_IN_NOTIFY_MESSAGE.format(player))
        players_pot = self.get_player_pot(player)
        PotManager.place_bet(player.money, player, players_pot)

    def call(self, player):
        player.action = Player.CALL_ACTION
        difference = self.current_bet - player.bet
        players_pot = self.get_player_pot(player)
        self.chat.message(CALL_NOTIFY_MESSAGE.format(player))
        PotManager.place_bet(difference, player, players_pot)

    def raise_bid(self, player, amount):
        player.action = "{} ${}".format(Player.RAISE_ACTION, amount)
        difference = self.current_bet - player.bet
        total_amount = amount + difference
        self.current_bet += total_amount

        players_pot = self.get_player_pot(player)

        PotManager.place_bet(total_amount, player, players_pot)

    def check(self, player):
        player.action = Player.CHECK_ACTION
        self.chat.message(CHECK_NOTIFY_MESSAGE.format(player))

    def bet(self, player, amount):
        player.action = "{} ${}".format(Player.BET_ACTION, amount)
        self.current_bet += amount
        PotManager.place_bet(amount, player, self.get_player_pot(player))
        self.chat.message(BET_NOTIFY_MESSAGE.format(player, amount))

    def create_side_pots(self):
        reprocess_pots = True

        # gotta be a better way to do this but
        # I am getting tired of writing this bot
        while reprocess_pots:
            lowest_all_in_player = None
            for pot in self.pots:
                if pot.locked:
                    continue

                lowest_all_in_player = PotManager.get_lowest_all_in_player(pot)
                break

            if lowest_all_in_player:
                amount = lowest_all_in_player.bet * len(pot.players)
                total = pot.amount
                difference = total - amount
                new_players = list(pot.players)
                new_players.remove(lowest_all_in_player)

                pot.locked = True
                pot.amount = amount

                side_pot = Pot('Side Pot {}'.format(len(self.pots)), difference, new_players)
                self.pots.append(side_pot)
            else:
                reprocess_pots = False

    @staticmethod
    def get_lowest_all_in_player(pot):
        lowest = None
        for player in pot.players:
            if player.state == Player.ALL_IN_STATE:
                if not lowest:
                    lowest = player
                    continue

                if lowest.bet > player.bet:
                    lowest = player

        return lowest

    def is_all_folded(self):
        for pot in self.pots:
            if len(pot.players) > 1:
                return False

        return True

    def get_pot_string(self):
        result = ""
        for pot in self.pots:
            result += '{}: ${}\n'.format(pot.name, pot.amount)

        return result
