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
        self.game_state: simple_go_game.GoGame = None

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

        # Send request to other node (implementation of sending message is not shown)


    def receive_start_game_request(self, message):
        # Terminal commands to accept or decline
            # If declined, send decline message back to opponent
            # If accepted, choose starting color and initialize game
                # call start_game method to set up game state
                # If color is stating color, follow up with first move
        pass

    def start_game(self, opponent_node, color, board_size=9):
        self.is_connected = True
        self.connected_to = opponent_node
        self.game_color = color
        self.game_state = simple_go_game.create_game_state(board_size)
        # Connect socket to neighbor?

    def send_move(self, move):
        if self.is_connected and self.connected_to:

            # Pass message as simple dictionary for now, can be structured as a message object if needed in future
            pass

            # message = message(message_type=message_type.MAKE_MOVE, sent_by=(self.ip_address, self.port), content=...)

            # Send the move to the connected node (implementation of sending message is not shown)

    def type_move(self):
        # Terminal command to type move and capture as string
        while True:
            move = input(f"{self.state['current_player']} move (e.g. c3 or pass): ").strip().lower()

            # Build move message
            if move == "pass":
                move_msg = {
                    "type": "pass",
                    "color": self.state["current_player"]
                }
            else:
                move_msg = {
                    "type": "move",
                    "move": move,
                    "color": self.state["current_player"]
                }

            # Validate + apply move locally
            response = simple_go_game.handle_move(self.game_state, move_msg)

            # If invalid → retry
            if not response["ok"]:
                print("❌", response["message"])
                continue

            # If valid move updates local state
            self.game_state = response

            print("✅", response["message"])
            # simple_go_game.print_board(self.state)

            # Send move to opponent
            self.send_move(move_msg)

            break

    def receive_move(self, move):
        # Update game state based on the received move
        self.game_state = simple_go_game.handle_move(self.game_state, move)

        # Check if the game is over after the move
        if self.game_state.game_over:
            self.end_game()

        # If game is not over, make another move
        self.type_move()

    def end_game(self):
        # Game state flag that indicates game is over, and no more moves can be made
        # Determine if this node won or lost and update skill rating accordingly
        # Clear game state and disconnect from opponent
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
            self.receive_start_game_request(message)
        elif message.message_type == message_type.MAKE_MOVE:
            # Handle make move logic
            pass
        elif message.message_type == message_type.END_GAME:
            # Handle end game logic
            pass