import yaml
from slackclient import SlackClient

# import sys
# import os
# sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from game import Game

config = yaml.load(file('rtmbot.conf', 'r'))
token = config["SLACK_TOKEN"]
slack_client = SlackClient(token)


outputs = []
crontable = [[1, "tick"]]
current_game = Game(slack_client)


def tick():
    current_game.tick()


def process_message(data):
    print data

    if data['type'] == 'message' and 'text' in data:
        current_game.process(data)















