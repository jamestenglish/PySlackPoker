from player import Player
from chat import Chat

start_message = "Who wants to play? Respond with 'yes' in this channel in the next {} seconds. "
join_message = "<@{}> has joined the game."


class JoinManager:
    def __init__(self, game):
        self.last_message = None
        self.chat = None
        self.game = game
        self.chat = Chat(self.game.slack_client, self.game.channel)

    def process_message(self, data):
        if 'text' in data and data['text'].lower() == 'yes':
            player = Player(data['user'], self.game.slack_client)
            if player not in self.game.players:
                self.game.players.append(player)
                self.chat.message(join_message.format(data['user']))

    def tick(self, timer):
        self.last_message = self.chat.message(start_message.format(timer),
                                              self.last_message)