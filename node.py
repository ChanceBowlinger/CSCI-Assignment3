from message import message, message_type
import simple_go_game

class Node:
    def __init__(self, central_hub):
        self.ip_address = None
        self.port = None
        self.neighbors = [] # Tuples of (ip_address, port)
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
        message = message(message_type=message_type.START_GAME, sent_by=(self.ip_address, self.port), content=message_body)

        # Send request to other node (implementation of sending message is not shown)
        self.send_message(message, opponent_node)


    def receive_start_game_request(self, message):
        while True:
            response = input(f"Received game request from {message.sent_by} with board size {message.content['board_size']}. Accept? (y/n): ").strip().lower()
            if response == 'y':
                color = input("Choose your color (black/white): ").strip().lower()
                if color in ['black', 'white']:
                    self.start_game(message.sent_by, color, board_size=message.content['board_size'])

                    # Send acceptance message back to opponent
                    response_message = message(message_type=message_type.RESPOND_GAME, sent_by=(self.ip_address, self.port), content={"accepted": True, "color": color, "board_size": message.content['board_size']})
                    self.send_message(response_message, message.sent_by)
                    break
                else:
                    print("Invalid color choice. Please choose 'black' or 'white'.")
            elif response == 'n':
                print("Declined game request.")

                # Send decline message back to opponent
                response_message = message(message_type=message_type.RESPOND_GAME, sent_by=(self.ip_address, self.port), content={"accepted": False})
                self.send_message(response_message, message.sent_by)
                break
            else:
                print("Invalid response. Please enter 'y' or 'n'.")

    def receive_start_game_response(self, message):
        if message.content.get("accepted"):
            opponent_color = message.content.get("color")
            # This node has opposite color of the opponent
            if opponent_color == "white":
                color = "black"
            elif opponent_color == "black":
                color = "white"
                
            self.start_game(message.sent_by, color, board_size=message.content.get("board_size", 5))
        else:
            print(f"Game request declined by {message.sent_by}")

    def start_game(self, opponent_node, color, board_size=9):
        self.is_connected = True
        self.connected_to = opponent_node
        self.game_color = color
        self.game_state = simple_go_game.create_game_state(board_size)
        # Connect socket to neighbor?

    def send_move(self, move):
        if self.is_connected and self.connected_to:
            # Wrap move in a message object and send to opponent
            message = message(message_type=message_type.MAKE_MOVE, sent_by=(self.ip_address, self.port), content=move)
            self.send_message(message, self.connected_to)

    def type_move(self):
        # Terminal command to type move and capture as string
        while True:
            move = input(f"{self.game_state['current_player']} move (e.g. c3 or pass): ").strip().lower()

            # Build move message
            if move == "pass":
                move_msg = {
                    "type": "pass",
                    "color": self.game_state["current_player"]
                }
            else:
                move_msg = {
                    "type": "move",
                    "move": move,
                    "color": self.game_state["current_player"]
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

            # If game is over, call end_game() to update skill rating and disconnect
            if self.game_state["game_over"]:
                print("Game Over!")
                self.end_game()

            break

    def receive_move(self, message):
        # Update game state based on the received move
        self.game_state = simple_go_game.handle_move(self.game_state, message.content)

        # Check if the game is over after the move
        if self.game_state["game_over"]:
            self.end_game()

        # If game is not over, make another move
        self.type_move()

    def end_game(self):
        # Clear game state and disconnect from opponent
        if self.game_state["message"].endswith("wins"):
            if self.game_state["message"].startswith(self.game_color.capitalize()):
                print("You won! 🎉")
                self.skill_rating += 10
            else:
                print("You lost. 😢")
                self.skill_rating -= 10
        elif self.game_state["message"] == "Draw":
            print("It's a draw. 🤝")

        self.is_connected = False
        self.connected_to = None
        self.game_color = None
        self.game_state = None

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
    
    def send_message(self, message, recipient):
        # Implementation of sending message to other node (e.g. via socket)
        pass

    def handle_message(self, message):
        if message.message_type == message_type.SCORE_REQUEST:
            return self.handle_score_request()
        elif message.message_type == message_type.NEW_NEIGHBOR:
            # Handle new neighbor logic
            pass
        elif message.message_type == message_type.START_GAME:
            self.receive_start_game_request(message)
        elif message.message_type == message_type.RESPOND_GAME:
            self.receive_start_game_response(message)
        elif message.message_type == message_type.MAKE_MOVE:
            self.receive_move(message)