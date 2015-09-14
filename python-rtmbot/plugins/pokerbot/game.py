from functools import partial
from deuces.deuces import Deck

from pot_manager import PotManager
from join_manager import JoinManager
from chat import Chat
from bet_manager import BetManager

WAIT = 10
bot_name = '<@U0A1420MD>'


class Game:
    def __init__(self, slack_client):
        self.state = 'DEAD'
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

    def start(self, channel):
        self.state = 'START'
        self.timer = WAIT
        self.players = []
        self.deck = Deck()
        self.current_player = 0
        self.pot_manager = PotManager(self)
        self.join_manager = JoinManager(self)
        self.chat = Chat(self.slack_client, channel)
        self.bet_manager = BetManager(self, self.pot_manager)

    def process(self, data):
        if 'DEAD' == self.state:
            self.process_dead(data)

        if 'START' == self.state:
            self.process_start(data)

        if 'BET1' == self.state:
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
        self.chat.reset()

    def enough_players(self):
        if len(self.players) < 2:
            self.chat.message("Not enough players.")
            self.set_state('DEAD')
            return False
        return True

    def deal_state(self):
        self.current_player = 0

        if not self.enough_players():
            return

        for player in self.players:
            player.deal(self.deck.draw(2))

        self.set_state('BLIND')

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
        self.bet_manager.request_bets(self.dealer_id, partial(self.set_state, "FLOP"))
        self.set_state("BET1")

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

    def count_down(self, new_state):
        self.timer -= 1
        if self.timer < 0:
            self.set_state(new_state)
            return

    def tick(self):
        if 'START' == self.state:
            self.join_manager.tick(self.timer)
            self.count_down('DEAL')

        if 'DEAL' == self.state:
            self.deal_state()

        if 'BLIND' == self.state:
            self.blind_state()

        if 'BET1' == self.state:
            self.bet_manager.tick()
            #TODO what if everyone else folds?

        if "FLOP" == self.state:
            pass
            #TODO PROCESS FLOP