import json
from deuces.deuces import Card


class Player:
    def __init__(self, slack_id, slack_client):
        self.slack_id = slack_id
        self.money = 200
        self.cards = []
        self.state = 'IN'
        self.action = ''
        self.bet = ''
        self.slack_client = slack_client

    def get_im_channel(self, user):
        ims = json.loads(self.slack_client.api_call('im.list'))['ims']
        for im in ims:
            if im['user'] == user:
                return im['id']

    def deal(self, cards):
        self.cards = cards
        self.state = 'IN'
        card_str = '[{}, {}]'.format(Card.int_to_pretty_str(cards[0]), Card.int_to_pretty_str(cards[1]))
        result = self.slack_client.api_call('chat.postMessage',
                                            text=card_str,
                                            channel=self.get_im_channel(self.slack_id),
                                            username='poker_bot',
                                            as_user=True)
        print str(result)

    def __hash__(self):
        return self.slack_id.__hash__()

    def __eq__(self, other):
        return self.slack_id == other.slack_id