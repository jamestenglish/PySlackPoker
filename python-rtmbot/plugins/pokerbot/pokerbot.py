import yaml
import json
from slackclient import SlackClient

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from deuces.deuces import Deck, Card

bot_name = '<@U0A1420MD>'

config = yaml.load(file('rtmbot.conf', 'r'))
token = config["SLACK_TOKEN"]

outputs = []
crontable = [[1, "tick"]]
games = {}
slack_client = SlackClient(token)
start_message = "Who wants to play? Respond with 'yes' in this channel in the next {} seconds. "
join_message = "<@{}> has joined the game."


WAIT = 10

def tick():
    for channel in games:
        games[channel].tick()


def process_message(data):
    print data
    if data['type'] == 'message' and 'text' in data:
        channel = data['channel']

        text = data['text']
        deal_text = '{}: deal'.format(bot_name)
        
        if deal_text.lower() in text.lower():
            if channel not in games:
                games[channel] = Game(channel)
                games[channel].start()

        if channel in games:
            games[channel].process(data)



class Game:
    def __init__(self, channel):
        self.channel = channel
        self.state = None
        self.timer = WAIT
        self.last_message = None
        self.players = []
        self.deck = None

    def start(self):
        self.state = 'START'
        self.timer = WAIT
        self.players = []
        self.deck = Deck()

    def process(self, data):
        if 'DEAD' == self.state:
            text = data['text']
            deal_text = '{}: deal'.format(bot_name)

            if deal_text.lower() in text.lower():
                self.start()

        if 'START' == self.state:
            if 'text' in data and data['text'].lower() == 'yes':
                for player in self.players:
                    if player.slack_id == data['user']:
                        return

                self.players.append(Player(data['user']))
                self.message(join_message.format(data['user']))

    def set_state(self, state):
        self.state = state
        self.timer = WAIT
        self.last_message = None

    def message(self, text, last_message=None):

        result = None
        if last_message:
            result = slack_client.api_call('chat.update',
                                           text=text,
                                           channel=self.channel,
                                           ts=self.last_message['ts'])
        else:
            result = slack_client.api_call('chat.postMessage',
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

    def start_state(self):
        self.timer -= 1
        if self.timer < 0:
            self.set_state('DEAL')
            return

        self.last_message = self.message(start_message.format(self.timer),
                                         self.last_message)

    def deal_state(self):
        print 'deal_state====='
        print repr(self.players)
        print 'end'
        #if len(self.players) < 2:
        #    self.message("Not enough players.")
            #self.set_state('DEAD')
            #return

        for player in self.players:
            print '2a'
            print str(self.deck.draw(2))
            print '2b'
            player.deal(self.deck.draw(2))
            
        self.set_state('PREFLOP_BET')

    def tick(self):
        if 'START' == self.state:
            self.start_state()

        if 'DEAL' == self.state:
            self.deal_state()


def get_im_channel(user):
    ims = json.loads(slack_client.api_call('im.list'))['ims']
    for im in ims:
        if im['user'] == user:
            return im['id']




class Player:
    def __init__(self, slack_id):
        self.slack_id = slack_id
        self.money = 200
        self.cards = []

    def deal(self, cards):
        self.cards = cards
        card_str = '[{}, {}]'.format(Card.int_to_pretty_str(cards[0]), Card.int_to_pretty_str(cards[1]))
        result = slack_client.api_call('chat.postMessage',
                              text=card_str,
                              channel=get_im_channel(self.slack_id),
                              username='poker_bot',
                              as_user=True)
        print str(result)
