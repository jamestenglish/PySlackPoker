import json


class Chat:
    def __init__(self, slack_client, channel):
        self.slack_client = slack_client
        self.channel = channel
        self.last_message = None

    def reset(self):
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