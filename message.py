from enum import Enum

class message_type(int, Enum):
    CONNECT_TO_CENTRAL_HUB = 0
    NEW_NEIGHBOR = 1
    NEW_NEIGHBOR_RESPONSE = 2
    SCORE_REQUEST = 3
    START_GAME = 4
    RESPOND_GAME = 5
    MAKE_MOVE = 6


class message:
    def __init__(self, message_type: message_type, sent_by=(0,0), TTL=1, content=None):
        self.message_type = message_type
        self.sent_by = sent_by
        self.TTL = TTL
        self.content = content

    