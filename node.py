import json
import logging
import os
import socketserver
import threading
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

        data = self.request.recv(1024).decode('utf-8')
        if not data:
            return
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
        self.ip_address = self.server_address[0]
        self.port = self.server_address[1]
        self.neighbors = []
        self.skill_rating = 0
        self.is_connected = False
        self.connected_to = None
        self.game_color = None
        self.game_state: simple_go_game.GoGame = None
        self.pending_requests = [] # Store incoming game requests
        self.move_received_event = threading.Event() # Sync turns

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
        s.connect((recipient[0], recipient[1]))
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
        msg = message(message_type=message_type.START_GAME, sent_by=(self.ip_address, self.port), content=message_body)

        # Send request to other node (implementation of sending message is not shown)
        self.send_message(msg, opponent_node)

    def receive_start_game_response(self, message):
        if message.content.get("accepted"):
            opponent_color = message.content.get("color")
            # This node has opposite color of the opponent
            if opponent_color == "white":
                color = "black"
            elif opponent_color == "black":
                color = "white"
                
            self.start_game(message.sent_by, color, board_size=message.content.get("board_size", 9))
        else:
            print(f"Game request declined by {message.sent_by}")

    def start_game(self, opponent_node, color, board_size=9):
        self.is_connected = True
        self.connected_to = opponent_node
        self.game_color = color
        self.game_state = simple_go_game.create_game_state(board_size)

    def send_move(self, move):
        if self.is_connected and self.connected_to:
            # Wrap move in a message object and send to opponent
            msg = message(message_type=message_type.MAKE_MOVE, sent_by=(self.ip_address, self.port), content=move)
            self.send_message(msg, self.connected_to)

    def type_move(self):
        while True:
            move = input(f"{self.game_state['current_player']} move (e.g. c3 or pass): ").strip().lower()

            # Build move message
            move_msg = {
                "type": "move" if move != "pass" else "pass",
                "move": move,
                "color": self.game_color
            }

            # Validate + apply move locally
            response = simple_go_game.handle_move(self.game_state, move_msg)

            if not response["ok"]:
                print("❌", response["message"])
                continue

            self.game_state = response
            self.send_move(move_msg)
            
            break

    def receive_move(self, message):
        # Update game state based on the received move
        self.game_state = simple_go_game.handle_move(self.game_state, message.content)

        # Check if the game is over after the move
        if self.game_state["game_over"]:
            self.end_game()

        self.move_received_event.set()

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

    def request_neighbors(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('localhost', 3000))
        msg = message(message_type=message_type.NEW_NEIGHBOR, sent_by=(self.ip_address, self.port))
        s.send(json.dumps(msg.__dict__).encode('utf-8'))
        response = json.loads(s.recv(4096).decode('utf-8'))
        s.close()
        response_msg = message(**response)
        if response_msg.message_type == message_type.NEW_NEIGHBOR_RESPONSE:
            incoming = [list(p) for p in response_msg.content]
            new_neighbors = [n for n in incoming if n not in self.neighbors]
            self.neighbors = incoming
            for neighbor in new_neighbors:
                self.notify_neighbor(neighbor)

    def notify_neighbor(self, neighbor):
        try:
            msg = message(message_type=message_type.NEW_NEIGHBOR, sent_by=(self.ip_address, self.port))
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2.0)
            s.connect((neighbor[0], neighbor[1]))
            s.send(json.dumps(msg.__dict__).encode('utf-8'))
            s.recv(1024)
            s.close()
        except OSError:
            pass

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

    def _clear(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def _print_main_menu(self):
        self._clear()
        print(f"=== Go Game Node  [{self.ip_address}:{self.port}] ===")
        print("1. Request new neighbors")
        print("2. View neighbors")
        print("3. Start game")
        print("4. View pending game requests")
        print("5. My rating")
        print("6. Exit")
        print()

    def neighbors_menu(self):
        while True:
            self._clear()
            print("=== Neighbors ===")
            if self.neighbors:
                for i, n in enumerate(self.neighbors, 1):
                    print(f"  {i}. {n[0]}:{n[1]}")
            else:
                print("  (no neighbors yet — use option 1 from the main menu)")
            print()
            print("  0. Back to main menu")
            print()
            choice = input("Select: ").strip()
            if choice == '0':
                break

    def start_game_menu(self):
        """Sub-menu for starting a match with neighbors."""
        self._clear()
        print("=== Start a Match ===")
        print("1. Challenge all neighbors")
        print("2. Challenge a specific neighbor")
        print("0. Back to main menu")
        print()
        
        choice = input("Select: ").strip()
        
        if choice == '1':
            print("Sending game requests to all neighbors...")
            self.connect_to()
            input("Requests sent. Press Enter to continue...")
            
        elif choice == '2':
            if not self.neighbors:
                print("Your neighbor list is empty. Try requesting neighbors from the hub first.")
                input("Press Enter to continue...")
                return
            
            print("\nAvailable Opponents:")
            for i, n in enumerate(self.neighbors, 1):
                print(f"  {i}. {n[0]}:{n[1]}")
            
            try:
                idx_input = input("\nEnter the number of the opponent (0 to cancel): ").strip()
                idx = int(idx_input)
                
                if 1 <= idx <= len(self.neighbors):
                    # Convert the list [ip, port] to the required tuple (ip, port)
                    target_tuple = tuple(self.neighbors[idx-1])
                    print(f"Sending request to {target_tuple[0]}:{target_tuple[1]}...")
                    self.connect_to(other_node=target_tuple)
                    input("Request sent. Press Enter to continue...")
                elif idx == 0:
                    return
                else:
                    print("Invalid selection.")
                    input("Press Enter to continue...")
            except ValueError:
                print("Error: Please enter a valid numerical index.")
                input("Press Enter to continue...")

    def main_loop(self):
        while not self.is_connected:
            self._print_main_menu()
            if self.pending_requests:
                print(f"🔔 YOU HAVE {len(self.pending_requests)} PENDING GAME REQUEST(S)!")
            
            choice = input("Select: ").strip()

            if choice == '1':
                print("Requesting neighbors from hub...")
                self.request_neighbors()
                print(f"Done. {len(self.neighbors)} active neighbor(s) found.")
                input("Press Enter to continue...")
            elif choice == '2':
                self.neighbors_menu()
            elif choice == '3':
                self.start_game_menu()
            elif choice == '4':
                self.handle_pending_requests()
            elif choice == '5':
                print(f"Your skill rating: {self.skill_rating}")
                input("Press Enter to continue...")
            elif choice == '6':
                return "EXIT"
            
            # Check if a response we sent or received triggered a game
            if self.is_connected:
                return "GAME_START"

    def game_loop(self):
        while self.is_connected:
            self._clear()
            print(f"=== Game vs {self.connected_to} ===")
            print(f"Your Color: {self.game_color.upper()}")
            simple_go_game.print_board(self.game_state)

            if self.game_state["game_over"]:
                print("\nGAME OVER")
                self.end_game()
                input("\nPress Enter to return to menu...")
                break

            if self.game_state["current_player"] == self.game_color:
                self.type_move()
            else:
                # Opponent's turn: Wait for network event
                print("\nWaiting for opponent to move...")
                self.move_received_event.wait()
                self.move_received_event.clear()


    def handle_message(self, message):
        if message.message_type == message_type.SCORE_REQUEST:
            return self.handle_score_request()
        elif message.message_type == message_type.NEW_NEIGHBOR:
            sender = list(message.sent_by)
            if sender not in self.neighbors:
                self.neighbors.append(sender)
        elif message.message_type == message_type.START_GAME:
            self.pending_requests.append(message)
        elif message.message_type == message_type.RESPOND_GAME:
            self.receive_start_game_response(message)
        elif message.message_type == message_type.MAKE_MOVE:
            self.game_state = simple_go_game.handle_move(self.game_state, message.content)
            self.move_received_event.set()

    def handle_pending_requests(self):
        """Interact with game requests stored in the queue."""
        if not self.pending_requests:
            print("No pending requests.")
            input("Press Enter...")
            return

        req = self.pending_requests.pop(0)
        resp = input(f"Accept request from {req.sent_by}? (y/n): ").strip().lower()
        if resp == 'y':
            color = input("Color (black/white): ").strip().lower()
            msg = message(message_type=message_type.RESPOND_GAME, 
                          sent_by=(self.ip_address, self.port), 
                          content={"accepted": True, "color": color, "board_size": req.content['board_size']})
            self.send_message(msg, req.sent_by)
            self.start_game(req.sent_by, color, req.content['board_size'])
        else:
            msg = message(message_type=message_type.RESPOND_GAME, 
                          sent_by=(self.ip_address, self.port), 
                          content={"accepted": False})
            self.send_message(msg, req.sent_by)
            
if __name__ == '__main__':
    # Example of creating a node and connecting to the central hub
    address = ('localhost', 0)  # let the kernel give us a port
    node = Node(address, request_handler)
    ip, port = node.server_address
    print(f'Node is running on {ip}:{port}')
    server_thread = threading.Thread(target=node.serve_forever, daemon=True)
    server_thread.start()

    while True:
        if node.is_connected:
            node.game_loop()
        else:
            status = node.main_loop()
            if status == "EXIT":
                break