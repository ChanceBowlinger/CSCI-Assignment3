'''
    python -m pytest test_simple_p2p_game.py -v
'''

from __future__ import annotations

import importlib.util
import pathlib
import sys
import threading
from unittest.mock import Mock

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def load_module(module_name: str, *candidate_filenames: str):
    """Load modules even when uploaded filenames contain parentheses."""
    for filename in candidate_filenames:
        path = ROOT / filename
        if path.exists():
            spec = importlib.util.spec_from_file_location(module_name, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            assert spec.loader is not None
            spec.loader.exec_module(module)
            return module
    raise FileNotFoundError(f"Could not find one of: {candidate_filenames}")


message_mod = load_module("message", "message.py")
game = load_module("simple_go_game", "simple_go_game.py")
node_mod = load_module("node", "node.py")

message = message_mod.message
message_type = message_mod.message_type

# Testing node 
def make_test_node(port: int):
    node = node_mod.Node.__new__(node_mod.Node)
    node.ip_address = "127.0.0.1"
    node.port = port
    node.neighbors = []
    node.skill_rating = 0
    node.is_connected = False
    node.connected_to = None
    node.game_color = None
    node.game_state = None
    node.pending_requests = []
    node.move_received_event = threading.Event()
    node.send_message = Mock()
    return node


'''Simulate what type_move does, but without using input()'''
def apply_local_move_and_send(node, move_text: str):
    move_msg = {
        "type": "move" if move_text != "pass" else "pass",
        "move": move_text,
        "color": node.game_color,
    }

    response = game.handle_move(node.game_state, move_msg)
    assert response["ok"] is True, response["message"]

    node.game_state = response
    node.send_move(move_msg)

# Challenges neighbors in the network
def test_player_challenges_all_neighbors_in_p2p_network():
    challenger = make_test_node(5000)
    challenger.neighbors = [
        ["127.0.0.1", 5001],
        ["127.0.0.1", 5002],
        ["127.0.0.1", 5003],
    ]

    challenger.connect_to()

    assert challenger.send_message.call_count == 3

    recipients = [call.args[1] for call in challenger.send_message.call_args_list]
    assert recipients == challenger.neighbors

    for call in challenger.send_message.call_args_list:
        sent_msg = call.args[0]
        assert sent_msg.message_type == message_type.START_GAME
        assert sent_msg.sent_by == ("127.0.0.1", 5000)
        assert sent_msg.content == {"board_size": 5}


def test_two_players_have_same_board_after_three_p2p_moves():
    black_player = make_test_node(5000)
    white_player = make_test_node(5001)

    # Simulate the result of a successfully accepted challenge.
    black_player.start_game(("127.0.0.1", 5001), "black", board_size=5)
    white_player.start_game(("127.0.0.1", 5000), "white", board_size=5)

    # Route sent MAKE_MOVE messages directly to the other player's handle_message.
    def send_from_black(sent_msg, recipient):
        assert recipient == ("127.0.0.1", 5001)
        white_player.handle_message(sent_msg)

    def send_from_white(sent_msg, recipient):
        assert recipient == ("127.0.0.1", 5000)
        black_player.handle_message(sent_msg)

    black_player.send_message = Mock(side_effect=send_from_black)
    white_player.send_message = Mock(side_effect=send_from_white)

    apply_local_move_and_send(black_player, "a1")
    apply_local_move_and_send(white_player, "b1")
    apply_local_move_and_send(black_player, "a2")

    assert black_player.game_state["board"] == white_player.game_state["board"]
    assert black_player.game_state["current_player"] == white_player.game_state["current_player"]
    assert black_player.game_state["move_number"] == white_player.game_state["move_number"] == 3

    # Exact board checks: a1 black, b1 white, a2 black.
    assert black_player.game_state["board"][4][0] == game.BLACK
    assert black_player.game_state["board"][4][1] == game.WHITE
    assert black_player.game_state["board"][3][0] == game.BLACK
