import yaml
import json
from slackclient import SlackClient

bot_name = '<@U0A1420MD>'

config = yaml.load(file('rtmbot.conf', 'r'))
token = config["SLACK_TOKEN"]

outputs = []
crontable = [[1, "tick"]]
games = {}
slack_client = SlackClient(token)
start_message = "Who wants to play? Respond with 'yes' in this channel in the next {} seconds. "
join_message = "<@{}> has joined the game."


def tick():
    for channel in games:
        games[channel].tick()


def process_message(data):
    print data
    if data['type'] == 'message':
        channel = data['channel']

        text = data['text']
        deal_text = '{}: deal'.format(bot_name)
        
        if deal_text.lower() in text.lower():
            print 'a'
            if channel not in games:
                games[channel] = Game(channel)
                games[channel].start()

        if channel in games:
            games[channel].process(data)



class Game:
    def __init__(self, channel):
        self.channel = channel
        self.state = None
        self.timer = 30
        self.last_message = None
        self.players = []

    def start(self):
        self.state = 'START'
        self.timer = 30
        self.players = []

    def process(self, data):
        if 'START' == self.state:
            if data['text'].lower() == 'yes':
                self.players.append(Player(data['user']))
                self.message(join_message.format(data['user']))

    def set_state(self, state):
        self.state = state
        self.timer = 30
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
                                           channel=self.channel)

        result = json.loads(result)

        print str(result)

        return result

    def tick(self):
        if 'START' == self.state:
            if self.timer == 0:
                self.set_state('DEAL')
                return

            self.last_message = self.message(start_message.format(self.timer),
                                             self.last_message)






class Player:
    def __init__(self, slack_id):
        self.slack_id = slack_id
        self.money = 200
        self.cards = []
