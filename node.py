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