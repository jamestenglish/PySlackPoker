import json
try:
    from deuces.deuces import Card
except ImportError:
    from python_rtmbot.deuces.deuces import Card

from chat import Chat


class Player:
    IN_STATE = "IN"
    FOLD_STATE = "FOLD"
    ALL_IN_STATE = "ALL IN"

    CALL_ACTION = "CALL"
    RAISE_ACTION = "RAISE"
    CHECK_ACTION = "CHECK"
    BET_ACTION = "BET"

    def __init__(self, slack_id, slack_client):
        self.slack_id = slack_id
        self.money = 200
        self.cards = []
        self.state = Player.IN_STATE
        self.action = ''
        self.bet = 0
        self.slack_client = slack_client
        self.chat = Chat(slack_client, Player.get_im_channel(self.slack_client, self.slack_id))

    @staticmethod
    def get_im_channel(slack_client, slack_id):
        ims = json.loads(slack_client.api_call('im.list'))['ims']
        for im in ims:
            if im['user'] == slack_id:
                return im['id']

    def get_username(self):
        user_api = json.loads(self.slack_client.api_call('users.info', user=self.slack_id))['user']
        return user_api['name']

    def card_str(self):
        return '[{}, {}]'.format(Card.int_to_pretty_str(self.cards[0]), Card.int_to_pretty_str(self.cards[1]))

    def deal(self, cards):
        self.bet = 0
        self.cards = cards
        self.state = Player.IN_STATE
        self.chat.message(self.card_str())

    def __hash__(self):
        return self.slack_id.__hash__()

    def __eq__(self, other):
        return self.slack_id == other.slack_id

    def __str__(self):
        return self.get_username()