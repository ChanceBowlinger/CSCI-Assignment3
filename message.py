from enum import Enum

class message_type(Enum):
    NEW_NEIGHBOR = 1
    NEW_NEIGHBOR_RESPONSE = 2
    SCORE_REQUEST = 3
    START_GAME = 4
    RESPOND_GAME = 5
    MAKE_MOVE = 6
    END_GAME = 7


class message:
    MESSAGE_ID_COUNTER = 0

    def __init__(self, message_type: message_type, sent_by=None, TTL=1, content=None):
        self.message_id = message.MESSAGE_ID_COUNTER 
        self.message_type = message_type
        self.TTL = TTL
        self.content = content
        message.MESSAGE_ID_COUNTER += 1

    