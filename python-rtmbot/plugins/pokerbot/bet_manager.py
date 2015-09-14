from game import WAIT
from player import IN_STATE, FOLD_STATE, ALL_IN_STATE

CALL_MESSAGE = "It's your turn. Respond with\n*(C)all    (R)aise    (F)old*\nin the next {} seconds."
CHECK_MESSAGE = "It's your turn. Respond with\n*(C)heck    (B)et    (F)old*\nin the next {} seconds."
ALL_IN_MESSAGE = "It's your turn. Respond with\n*(A)ll in    (F)old*\nin the next {} seconds."
TIMEOUT_MESSAGE = "You have run out of time. You have automatically folded."

NEED_AMOUNT = "You need to specify a proper amount."
NOT_ENOUGH_MONEY = "You do not have enough money to do that."


class BetManager:
    def __init__(self, game, pot_manager):
        self.game = game
        self.player_id = None
        self.dealer_id = None
        self.callback_func = None
        self.timer = WAIT
        self.last_message = None
        self.pot_manager = pot_manager
        self.stop_player = None
        self.player = None
        self.bet_type = None
        self.allow_stop_bet = False

    def request_bets(self, player_id, callback_func):
        self.player_id = self.dealer_id = player_id
        self.callback_func = callback_func
        self.timer = WAIT
        self.last_message = None
        self.stop_player = self.get_player(self.dealer_id)
        self.allow_stop_bet = self.stop_player == self.pot_manager.small_blind

    def get_player(self, player_id):
        return self.game.players[player_id % len(self.game.players)]

    def count_down(self, player):
        self.timer -= 1
        if self.timer < 0:
            player.action = "FOLD"
            player.chat.message(TIMEOUT_MESSAGE)
            self.next_player()
            return

    def next_player(self):
        self.player_id += 1
        self.last_message = None
        self.timer = WAIT

    def tick(self):
        self.player = self.get_player(self.player_id)
        if self.player.state != IN_STATE:
            self.next_player()
            return

        if self.player == self.stop_player:
            if not self.allow_stop_bet:
                self.callback_func()
                return
            else:
                self.allow_stop_bet = False

        if self.pot_manager.current_bet == self.player.bet:
            self.bet_type = CHECK_MESSAGE
            self.last_message = self.player.chat.message(CHECK_MESSAGE.format(self.timer), self.last_message)
            return

        if self.pot_manager.current_bet > self.player.bet:
            difference = self.pot_manager.current_bet - self.player.bet
            if difference >= self.player.money:
                self.bet_type = ALL_IN_MESSAGE
                self.last_message = self.player.chat.message(ALL_IN_MESSAGE.format(self.timer), self.last_message)
            else:
                self.bet_type = CALL_MESSAGE
                self.last_message = self.player.chat.message(CALL_MESSAGE.format(self.timer), self.last_message)
            return

    @staticmethod
    def is_num(number_string):
        try:
            int(number_string)
        except ValueError:
            return False

        return True

    def process_all_in(self):
        self.pot_manager.all_in(self.player)
        self.next_player()

    def process(self, data):
        if self.player != self.game.players[self.player_id % len(self.game.players)]:
            return

        if self.player.state != IN_STATE:
            return

        if data['text'].lower() == 'f':
            self.pot_manager.fold(self.player)
            self.next_player()
            return

        if self.bet_type == ALL_IN_MESSAGE:
            if data['text'].lower() == 'a':
                self.process_all_in()
                return

        if self.bet_type == CHECK_MESSAGE:
            if data['text'].lower() == 'c':
                self.pot_manager.check(self.player)
                self.next_player()
                return

            if data['text'].lower().starts_with('b'):
                bet_amount = data['text'].lower().replace('b', '')

                if bet_amount is '' or not BetManager.is_num(bet_amount):
                    return self.player.chat.message(NEED_AMOUNT)

                bet_amount = int(bet_amount)

                if bet_amount > self.player.money:
                    return self.player.chat.message(NOT_ENOUGH_MONEY)

                if bet_amount == self.player.money:
                    self.process_all_in()
                    return

                self.pot_manager.bet(self.player, bet_amount)
                self.next_player()
                return

        if self.bet_type == CALL_MESSAGE:
            if data['text'].lower() == 'c':
                difference = self.pot_manager.current_bet - self.player.bet

                if difference > self.player.money:
                    return self.player.chat.message(NOT_ENOUGH_MONEY)

                if difference == self.player.money:
                    self.process_all_in()
                    return

                self.pot_manager.call(self.player)
                self.next_player()
                return

            if data['text'].lower().starts_with('r'):
                raise_amount = data['text'].lower().replace('r', '')

                if raise_amount is '' or not BetManager.is_num(raise_amount):
                    return self.player.chat.message(NEED_AMOUNT)

                raise_amount = int(raise_amount)

                difference = self.pot_manager.current_bet - self.player.bet

                total_amount = raise_amount + difference

                if total_amount > self.player.money:
                    return self.player.chat.message(NOT_ENOUGH_MONEY)

                if total_amount == self.player.money:
                    self.process_all_in()
                    return

                self.pot_manager.raise_bid(self.player, raise_amount)
                self.next_player()
                return







