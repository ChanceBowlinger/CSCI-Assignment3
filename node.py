"""
Node
    int node_id
    list<Node> neighbors
    CentralHub central_hub

    int skill_rating
    bool is_connected
    Node connected_to
    [][] game_state? (might be different)

    void connect_to(Node other_node):
        // send ping to specific neighbor
        if neighbor accepts:
            is_connected = true
            connected_to = other_node

    void connect_to():
        // send ping to all neighbors
        for neighbor in neighbors:
            if neighbor accepts:
                is_connected = true
                connected_to = neighbor
                break
                
    void send_move(... move):
        // Ping neighbor with move
        // updtae game state

    void receive_move(... move):
        // update game state

    void end_game():
        // Determine winner
        // Clear game_state
        // Increment/decrement game_state

    list<Node> get_new_neighbors():
        // ping central hub for new neighbors
        neighbors = central_hub.return_new_neighbors(neighbors)

    void compare_rating():
        // Pint neighbors for their skill rating
        // Sort and compare skill ratings

    void ping_score_request():
        // Ping neighbors for their skill rating

    void handle_score_request():
        return skill_rating

    handle_message(Message message):
        if message.type == score_request:
            handle_score_request()
        elif message.type == connection:
            // handle connection
        elif message.type == new_neighbor:
            // handle new neighbor
        etc.

"""

from message import message, message_type

class Node:
    def __init__(self, node_id, central_hub):
        self.node_id = node_id
        self.neighbors = []
        self.central_hub = central_hub
        self.skill_rating = 0
        self.is_connected = False
        self.connected_to = None
        self.game_state = None

    def connect_to(self, other_node=None):
        if other_node:
            # send ping to specific neighbor
            if other_node.accept_connection(self):
                self.is_connected = True
                self.connected_to = other_node
        else:
            # send ping to all neighbors
            for neighbor in self.neighbors:
                if neighbor.accept_connection(self):
                    self.is_connected = True
                    self.connected_to = neighbor
                    break

    def send_connection_request(self, other_node):
        # Ping neighbor with connection request
        # Wait for response and update connection status accordingly
        pass

    def accept_connection(self, other_node):
        # Logic to accept/reject connection by default (by score) or accept/decline
        return True  # Placeholder for acceptance logic

    def send_move(self, move):
        if self.is_connected and self.connected_to:
            message = message(message_id=..., message_type=message_type.MAKE_MOVE, sent_by=self.node_id, content=...)
            # Send the move to the connected node (implementation of sending message is not shown)

    def receive_move(self, move):
        # Update game state based on the received move
        pass

    def end_game(self):
        # Determine winner, clear game state, and update skill rating
        pass

    def get_new_neighbors(self):
        new_neighbors = self.central_hub.return_new_neighbors(self.neighbors)
        self.neighbors.extend(new_neighbors)

    def compare_rating(self):
        # Ping neighbors for their skill rating and compare
        pass

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