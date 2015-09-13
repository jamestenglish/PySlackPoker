import json

from deuces.deuces import Deck

from pot_manager import PotManager
from player import Player

WAIT = 10
bot_name = '<@U0A1420MD>'
start_message = "Who wants to play? Respond with 'yes' in this channel in the next {} seconds. "
join_message = "<@{}> has joined the game."


class Game:
    def __init__(self, slack_client):
        self.channel = None
        self.state = 'DEAD'
        self.timer = WAIT
        self.last_message = None
        self.players = []
        self.deck = None
        self.current_player = 0
        self.pot_manager = None
        self.slack_client = slack_client

    def start(self, channel):
        self.state = 'START'
        self.channel = channel
        self.timer = WAIT
        self.players = []
        self.deck = Deck()
        self.current_player = 0
        self.pot_manager = PotManager(self)
        self.last_message = self.message(start_message.format(self.timer),
                                         self.last_message)

    def process(self, data):
        if 'DEAD' == self.state:
            self.process_dead(data)

        if 'START' == self.state:
            self.process_start(data)

    def process_dead(self, data):
        text = data['text']
        deal_text = '{}: deal'.format(bot_name)

        if deal_text.lower() in text.lower():
            self.start(data['channel'])

    def process_start(self, data):
        if 'text' in data and data['text'].lower() == 'yes':
            player = Player(data['user'], self.slack_client)
            if player not in self.players:
                self.players.append(player)
                self.message(join_message.format(data['user']))

    def set_state(self, state):
        self.state = state
        self.timer = WAIT
        self.last_message = None

    def message(self, text, last_message=None):

        result = None
        if last_message:
            result = self.slack_client.api_call('chat.update',
                                                text=text,
                                                channel=self.channel,
                                                ts=self.last_message['ts'])
        else:
            result = self.slack_client.api_call('chat.postMessage',
                                                text=text,
                                                channel=self.channel,
                                                username='poker_bot',
                                                as_user=True)

        if not result:
            return result

        result = json.loads(result)
        print '------Result:'
        print str(result)
        print str(result.keys())
        print '----end'

        return result

    def enough_players(self):
        if len(self.players) < 2:
            self.message("Not enough players.")
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
                self.players.remove(0)
                if not self.enough_players():
                    return False
            self.current_player += 1
            return True

    def blind_state(self):
        if not self.post_blind(self.pot_manager.post_small_blind):
            return

        if not self.post_blind(self.pot_manager.post_big_blind):
            return

        self.display_board()

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

        self.message(board_str)

    def count_down(self, new_state):
        self.timer -= 1
        if self.timer < 0:
            self.set_state(new_state)
            return

    def tick(self):
        if 'START' == self.state:
            self.count_down('DEAL')

        if 'DEAL' == self.state:
            self.deal_state()

        if 'BLIND' == self.state:
            self.blind_state()