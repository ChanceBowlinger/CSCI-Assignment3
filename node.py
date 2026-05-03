import json
import logging
import socketserver
from message import message, message_type
import simple_go_game
import socket


class request_handler(socketserver.BaseRequestHandler):
    
    def __init__(self, request, client_address, node):
        self.logger = logging.getLogger('request_handler')
        self.logger.debug('__init__')
        self.node : Node = node
        socketserver.BaseRequestHandler.__init__(self, request, client_address, node)
        return

    def handle(self):
        self.logger.debug('handle')

        # Echo the back to the client
        data = self.request.recv(1024).decode('utf-8')
        data = json.loads(data)
        data : message = message(**data)
        self.node.handle_message(data)
        self.request.send("Message received".encode('utf-8'))
        return

    def finish(self):
        self.logger.debug('finish')
        return socketserver.BaseRequestHandler.finish(self)

class Node(socketserver.TCPServer):
    def __init__(self, server_address, RequestHandlerClass=request_handler):
        socketserver.TCPServer.__init__(self, server_address, RequestHandlerClass)
        
        self.node_id = None
        self.ip_address = server_address[0]
        self.port = server_address[1]
        self.neighbors = []
        self.skill_rating = 0
        self.is_connected = False
        self.connected_to = None
        self.game_color = None
        self.game_state: simple_go_game.GoGame = None

        self.central_hub = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print('Connecting to central hub...')
        self.central_hub.connect(('localhost', 3000))
        self.register_to_central_hub()

    def register_to_central_hub(self):
        new_message = message(message_type=message_type.CONNECT_TO_CENTRAL_HUB, sent_by=(self.ip_address, self.port))
        print(new_message.__dict__)
        self.central_hub.send(json.dumps(new_message.__dict__).encode('utf-8'))
        response = self.central_hub.recv(1024)

        print('Response from central hub:', response.decode('utf-8'))

    def send_message(self, message: message, recipient):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(recipient[0], recipient[1])
        s.send(json.dumps(message.__dict__).encode('utf-8'))
        response = s.recv(1024)
        print('Response from recipient:', response.decode('utf-8'))
        s.close()

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
            
if __name__ == '__main__':
    # Example of creating a node and connecting to the central hub
    address = ('localhost', 0)  # let the kernel give us a port
    node = Node(address, request_handler)
    ip, port = node.server_address
    print(f'Node is running on {ip}:{port}')
    node.serve_forever()
