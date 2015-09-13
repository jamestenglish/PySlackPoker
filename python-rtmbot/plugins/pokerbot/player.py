import json
from deuces.deuces import Card


class Player:
    def __init__(self, slack_id, slack_client):
        self.slack_id = slack_id
        self.money = 200
        self.cards = []
        self.state = 'IN'
        self.action = ''
        self.bet = 0
        self.slack_client = slack_client

    def get_im_channel(self):
        ims = json.loads(self.slack_client.api_call('im.list'))['ims']
        for im in ims:
            if im['user'] == self.slack_id:
                return im['id']

    def get_username(self):
        user_api = json.loads(self.slack_client.api_call('users.info', user=self.slack_id))['user']
        return user_api['name']

    def deal(self, cards):
        self.bet = 0
        self.cards = cards
        self.state = 'IN'
        card_str = '[{}, {}]'.format(Card.int_to_pretty_str(cards[0]), Card.int_to_pretty_str(cards[1]))
        result = self.slack_client.api_call('chat.postMessage',
                                            text=card_str,
                                            channel=self.get_im_channel(),
                                            username='poker_bot',
                                            as_user=True)
        print str(result)

    def message(self, message, last_message):
        pass

    def __hash__(self):
        return self.slack_id.__hash__()

    def __eq__(self, other):
        return self.slack_id == other.slack_id

    def __str__(self):
        return self.get_username()