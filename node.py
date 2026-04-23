from message import message, message_type
import simple_go_game

class Node:
    def __init__(self, node_id, central_hub):
        self.node_id = node_id
        self.neighbors = []
        self.central_hub = central_hub
        self.skill_rating = 0
        self.is_connected = False
        self.connected_to = None
        self.game_color = None
        self.game = None

    def connect_to(self, other_node=None):
        if other_node:
            # send ping to specific neighbor
            self.start_game_request(other_node, board_size=5)  # Example board size, can be parameterized
        else:
            # send ping to all neighbors
            for neighbor in self.neighbors:
                self.start_game_request(neighbor, board_size=5)  # Example board size, can be parameterized

    def start_game_request(self, opponent_node, board_size=5):
        message_body = {
            "board_size": board_size
        }

        # Send start game message to opponent
        message = message(message_type=message_type.START_GAME, sent_by=self.node_id, content=message_body)



    def receive_start_game_request(self, message):
        # Terminal commands to accept or decline
            # If declined, send decline message back to opponent
            # If accepted, choose starting color and initialize game
                # call start_game method to set up game state
                # If color is stating color, follow up with first move
        pass

    def start_game(self, opponent_node, color, board_size=5):
        self.is_connected = True
        self.connected_to = opponent_node
        self.game_color = color
        self.game = simple_go_game.create_game_state(board_size)
        # Connect socket to neighbor?

    def send_move(self, move):
        if self.is_connected and self.connected_to:
            message = message(message_type=message_type.MAKE_MOVE, sent_by=self.node_id, content=...)
            # Send the move to the connected node (implementation of sending message is not shown)

    def receive_move(self, move):
        # Update game state based on the received move
        pass

    def end_game(self):
        # Game state flag that indicates game is over, and no more moves can be made
        # Clear game state, update skill rating, and disconnect from opponent
        pass

    def get_new_neighbors(self):
        # May not be exact implementation
        new_neighbors = self.central_hub.return_new_neighbors(self.neighbors)
        self.neighbors.extend(new_neighbors)

    # Stretch Goal
    def compare_rating(self):
        # Ping neighbors for their skill rating and compare
        pass

    # Stretch Goal
    def ping_score_request(self):
        # Ping neighbors for their skill rating
        pass

    def handle_score_request(self):
        return self.skill_rating

    def handle_message(self, message):


        if message.message_type == message_type.SCORE_REQUEST:
            return self.handle_score_request()
        elif message.message_type == message_type.NEW_NEIGHBOR:
            # Handle new neighbor logic
            pass
        elif message.message_type == message_type.START_GAME:
            # Handle start game logic
            pass
        elif message.message_type == message_type.MAKE_MOVE:
            # Handle make move logic
            pass
        elif message.message_type == message_type.END_GAME:
            # Handle end game logic
            pass