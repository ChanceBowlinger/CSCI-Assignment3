"""
Central Hub
    list<Node> nodes

    list<Node> return_new_neighbors(list<Node> existing_neighbors):
        // return list of existing + new neighbors
"""

class central_hub:
    def __init__(self):
        self.nodes = []

    def get_active_players(self, current_player):
        new_players = []
        for node in self.nodes:
            if node != current_player and node.active:
                new_players.append(node)
        return new_players