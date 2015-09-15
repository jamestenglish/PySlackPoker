from functools import partial

try:
    from deuces.deuces import Deck, Evaluator
except ImportError:
    from python_rtmbot.deuces.deuces import Deck, Evaluator


from pot_manager import PotManager
from join_manager import JoinManager
from chat import Chat
from bet_manager import BetManager
from player import Player

WAIT = 30
NEW_GAME_WAIT = 10
bot_name = '<@U0A1420MD>'

DEAD_STATE = 'DEAD'
START_STATE = 'START'
BET_STATE = 'BET'
DEAL_STATE = 'DEAL'
BLIND_STATE = 'BLIND'
FLOP_STATE = 'FLOP'
FOLD_WIN_STATE = 'FOLD WIN'
TURN_STATE = 'TURN'
RIVER_STATE = 'RIVER'
SHOW_HANDS_STATE = 'SHOW_HANDS_STATE'
DETERMINE_WINNER_STATE = 'DETERMINE_WINNER_STATE'
PREPARE_NEW_GAME_STATE = 'PREPARE_NEW_GAME_STATE'
PAUSE_BETWEEN_GAME_STATE = 'PAUSE_BETWEEN_GAME_STATE'

SINGLE_WINNER_MESSAGE = '{} wins ${} from the {}'
SPLIT_WINNER_MESSAGE = '{} splits ${} from the {}'
PAUSE_MESSAGE = "New game in {} seconds. "


class Game:
    def __init__(self, slack_client):
        self.state = DEAD_STATE
        self.timer = WAIT

        self.players = []
        self.deck = None
        self.current_player = 0
        self.pot_manager = None
        self.slack_client = slack_client
        self.join_manager = None
        self.chat = None
        self.dealer_id = 0
        self.bet_manager = None
        self.board = []
        self.evaluator = Evaluator()
        self.last_message = None

    def start(self, channel):
        self.state = START_STATE
        self.timer = WAIT
        self.players = []
        self.deck = Deck()
        self.current_player = 0
        self.pot_manager = PotManager(self)
        self.join_manager = JoinManager(self)
        self.chat = Chat(self.slack_client, channel)
        self.bet_manager = BetManager(self, self.pot_manager)
        self.board = []
        self.last_message = None

    def process(self, data):
        if 'text' in data:
            text = data['text']
            quit_text = '{}: quit'.format(bot_name)

            if quit_text.lower() in text.lower():
                if PAUSE_BETWEEN_GAME_STATE == self.state:
                    player_to_remove = None
                    for player in self.players:
                        if player.slack_id == data['user']:
                            player_to_remove = player

                    self.players.remove(player_to_remove)
                    self.chat.message("{} has quit.".format(player_to_remove))
                else:
                    self.chat.message("You can't quit now, wait between games.")

        if DEAD_STATE == self.state:
            self.process_dead(data)

        if START_STATE == self.state:
            self.process_start(data)

        if BET_STATE == self.state:
            self.bet_manager.process(data)

    def process_dead(self, data):
        text = data['text']
        deal_text = '{}: deal'.format(bot_name)

        if deal_text.lower() in text.lower():
            self.start(data['channel'])

    def process_start(self, data):
        self.join_manager.process_message(data)

    def set_state(self, state):
        self.state = state
        self.timer = WAIT
        self.last_message = None
        self.chat.reset()

    def enough_players(self):
        if len(self.players) < 2:
            self.chat.message("Not enough players.")
            self.set_state(DEAD_STATE)
            return False
        return True

    def deal_state(self):
        self.current_player = 0

        if not self.enough_players():
            return

        # burn card
        self.deck.draw(1)

        for player in self.players:
            player.deal(self.deck.draw(2))

        self.set_state(BLIND_STATE)

    def post_blind(self, blind_func):
        while True:
            player = self.players[0]
            can_post = blind_func(player)
            if not can_post:
                self.players.pop(0)
                if not self.enough_players():
                    return False
            self.current_player += 1
            return True

    def blind_state(self):
        if not self.post_blind(self.pot_manager.post_small_blind):
            return

        if not self.post_blind(self.pot_manager.post_big_blind):
            return

        self.dealer_id = self.current_player

        self.display_board()
        flop_callback = partial(self.set_state, FLOP_STATE)
        fold_win_callback = partial(self.set_state, FOLD_WIN_STATE)
        self.bet_manager.request_bets(self.dealer_id, flop_callback, fold_win_callback)
        self.set_state(BET_STATE)

    def display_board(self):
        board_str = '```'
        for i, player in enumerate(self.players):
            if i == self.current_player % len(self.players):
                board_str += '->'
            else:
                board_str += '  '

            board_str += '<@{}>\t${}\t{}\t{} {}\n'.format(player.slack_id,
                                                          player.money,
                                                          player.state,
                                                          player.action,
                                                          player.bet)
        board_str += '```\n'
        board_str += self.pot_manager.display_pot()

        self.chat.message(board_str)

    def flop_state(self):
        # burn card
        self.deck.draw(1)

        self.board.extend(self.deck.draw(3))
        self.chat.message("*Dealing the flop:*\n{}".format(self.board))
        turn_callback = partial(self.set_state, TURN_STATE)
        fold_win_callback = partial(self.set_state, FOLD_WIN_STATE)
        self.bet_manager.request_bets(0, turn_callback, fold_win_callback)
        self.set_state(BET_STATE)

    def turn_state(self):
        # burn card
        self.deck.draw(1)

        self.board.extend(self.deck.draw(1))
        self.chat.message("*Dealing the turn:*\n{}".format(self.board))
        turn_callback = partial(self.set_state, RIVER_STATE)
        fold_win_callback = partial(self.set_state, FOLD_WIN_STATE)
        self.bet_manager.request_bets(0, turn_callback, fold_win_callback)
        self.set_state(BET_STATE)

    def river_state(self):
        # burn card
        self.deck.draw(1)

        self.board.extend(self.deck.draw(1))
        self.chat.message("*Dealing the river:*\n{}".format(self.board))
        self.set_state(SHOW_HANDS_STATE)

    def count_down(self, new_state):
        self.timer -= 1
        if self.timer < 0:
            self.set_state(new_state)
            return

    def show_hands_state(self):
        for player in self.players:
            if player.state == Player.FOLD_STATE:
                continue

            card_score = self.evaluator.evaluate(self.board, player.cards)
            card_class = self.evaluator.get_rank_class(card_score)
            self.chat.message('{} had: {} {}'.format(player, player.card_str(), card_class))

        self.set_state(DETERMINE_WINNER_STATE)

    def determine_winner_state(self):

        for pot in reversed(self.pot_manager.pots):
            pot_score = 9999
            pot_winners = []
            if len(pot.players) == 1:
                self.chat.message(SINGLE_WINNER_MESSAGE.format(pot.players[0], pot.amount, pot.name))
                pot.players[0].money += pot.amount
            else:
                for player in pot.players:
                    card_score = self.evaluator.evaluate(self.board, player.cards)
                    if card_score == pot_score:
                        pot_winners.append(player)

                    if card_score < pot_score:
                        pot_winners = [player]
                        pot_score = card_score

                if len(pot_winners) == 1:
                    self.chat.message(SINGLE_WINNER_MESSAGE.format(pot_winners[0], pot.amount, pot.name))
                    pot_winners[0].money += pot.amount
                else:
                    self.chat.message(SPLIT_WINNER_MESSAGE.format(pot_winners, pot.amount, pot.name))
                    for pot_winner in pot_winners:
                        pot_winner.money += (pot.amount / len(pot_winners))

        self.set_state(PREPARE_NEW_GAME_STATE)

    def prepare_new_game_state(self):
        # rotate players
        self.players.append(self.players.pop(0))
        self.set_state(PAUSE_BETWEEN_GAME_STATE)

    def pause_between_game_state(self):
        self.last_message = self.chat.message(PAUSE_MESSAGE.format(self.timer), self.last_message)
        self.count_down(DEAL_STATE)

    def tick(self):
        if START_STATE == self.state:
            self.join_manager.tick(self.timer)
            self.count_down(DEAL_STATE)

        if DEAL_STATE == self.state:
            self.deal_state()

        if BLIND_STATE == self.state:
            self.blind_state()

        if BET_STATE == self.state:
            self.bet_manager.tick()

        if FLOP_STATE == self.state:
            self.flop_state()

        if TURN_STATE == self.state:
            self.turn_state()

        if RIVER_STATE == self.state:
            self.river_state()

        if FOLD_WIN_STATE == self.state:
            self.set_state(DETERMINE_WINNER_STATE)

        if SHOW_HANDS_STATE == self.state:
            self.show_hands_state()

        if DETERMINE_WINNER_STATE == self.state:
            self.determine_winner_state()

        if PREPARE_NEW_GAME_STATE == self.state:
            self.prepare_new_game_state()

        if PAUSE_BETWEEN_GAME_STATE == self.state:
            self.pause_between_game_state()