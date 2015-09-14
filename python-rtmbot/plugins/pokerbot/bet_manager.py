from game import WAIT
from player import IN_STATE, FOLD_STATE, ALL_IN_STATE

CALL_MESSAGE = "It's your turn. Respond with\n*(C)all    (R)aise    (F)old*\nin the next {} seconds."
CHECK_MESSAGE = "It's your turn. Respond with\n*(C)heck    (B)et    (F)old*\nin the next {} seconds."
ALL_IN_MESSAGE = "It's your turn. Respond with\n*(A)ll in    (F)old*\nin the next {} seconds."
TIMEOUT_MESSAGE = "You have run out of time. You have automatically folded."



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

    def process(self, data):
        if self.player != self.game.players[self.player_id % len(self.game.players)]:
            return

        if self.player.state != IN_STATE:
            return

        if data['text'].lower() == 'f':
            self.pot_manager.fold(self.player)

        if self.bet_type == ALL_IN_MESSAGE:
            if data['text'].lower() == 'a':
                self.pot_manager.all_in(self.player)

        if self.bet_type == CHECK_MESSAGE:
            if data['text'].lower() == 'c':
                self.pot_manager.check(self.player)
                self.next_player()

            if data['text'].lower().starts_with('b'):
                #TODO remove b, test if number, check it player has enough money, place bet



