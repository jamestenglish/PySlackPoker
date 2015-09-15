from player import Player
from chat import Chat

start_message = "Who wants to play? Respond with 'yes' in this channel in the next {} seconds. "
join_message = "<@{}> has joined the game."


class JoinManager:
    def __init__(self, slack_client, channel, players):
        self.last_message = None
        self.slack_client = slack_client
        self.channel = channel
        self.players = players
        self.chat = Chat(slack_client, channel)
        print str(channel)

    def process_message(self, data):
        if 'text' in data and data['text'].lower() == 'yes':
            player = Player(data['user'], self.slack_client)
            if player not in self.players:
                self.players.append(player)
                self.chat.message(join_message.format(data['user']))

    def tick(self, timer):
        self.last_message = self.chat.message(start_message.format(timer),
                                              self.last_message)