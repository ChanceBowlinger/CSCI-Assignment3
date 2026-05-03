'''
Board Size
Current Player : Black/White
black score :
white score :
consecutive passes : -- if 2 passes reach game stops
move number : 
message : -- game result/ if illegal move is made
message Types : -- MOVE; PASS; RESET; QUIT
'''


from copy import deepcopy

from random import randrange
from math import ceil, sqrt

BLACK = "black"
WHITE = "white"
EMPTY = None


def other_player(color: str) -> str:
    return WHITE if color == BLACK else BLACK


class GoGame:
    def __init__(self, board_size: int = 9):
        if board_size < 1 or board_size > 26:
            raise ValueError("Board size must be between 1 and 26")
        self.board_size = board_size
        self.board = [[EMPTY for _ in range(board_size)] for _ in range(board_size)]
        self.current_player = BLACK
        self.black_score = 0
        self.white_score = 0
        self.consecutive_passes = 0
        self.move_number = 0
        self.game_over = False
        self.message = "Game started"

    def to_dict(self) -> dict:
        return {
            "board_size": self.board_size,
            "board": deepcopy(self.board),
            "current_player": self.current_player,
            "black_score": self.black_score,
            "white_score": self.white_score,
            "consecutive_passes": self.consecutive_passes,
            "move_number": self.move_number,
            "game_over": self.game_over,
            "message": self.message,
        }

    @staticmethod
    def from_dict(state:dict) -> "GoGame":
        game = GoGame(state["board_size"])
        game.board = deepcopy(state["board"])
        game.current_plater = state["current_player"]
        game.black_score = state["black_score"]
        game.white_score = state["white_score"]
        game.consecutive_passes = state["consecutive_passes"]
        game.move_number = state["move_number"]
        game.game_over = state["game_over"]
        game.message = state["message"]
        return game

def create_game_state(board_size: int = 5) -> dict:
    return GoGame(board_size).to_dict()

def is_on_board(board_size: int, row: int, col: int) -> bool:
    return 0 <= row < board_size and 0 <= col < board_size

def parse_move(move: str, board_size: int) -> tuple[int, int]:
    if not move or len(move)<2:
        raise ValueError("Move must look like this 'c3'")

    col_char = move[0].lower()
    if not ("a" <= col_char <= chr(ord('a') + board_size - 1)):
        raise ValueError(f"Column must be between a and {chr(ord('a') + board_size - 1)}")

    row_text = move[1:]
    if not row_text.isdigit():
        raise ValueError("Row must be a number")

    row_num = int(row_text)
    if not (1 <= row_num <= board_size):
        raise ValueError(f"Row must be between 1 and {board_size}")

    col = ord(col_char) - ord('a')
    row = board_size - row_num
    return row, col


def get_neighbors(board_size: int, row: int, col: int):
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = row + dr, col + dc
        if is_on_board(board_size, nr, nc):
            yield nr, nc


def get_group_and_liberties(board: list[list], row: int, col: int):
    color = board[row][col]
    if color is EMPTY:
        return set(), set()

    stack = [(row, col)]
    group = set()
    liberties = set()

    while stack:
        r, c = stack.pop()
        if (r, c) in group:
            continue
        group.add((r, c))

        for nr, nc in get_neighbors(len(board), r, c):
            if board[nr][nc] == EMPTY:
                liberties.add((nr, nc))
            elif board[nr][nc] == color and (nr, nc) not in group:
                stack.append((nr, nc))

    return group, liberties


def remove_group(board: list[list], group: set[tuple[int, int]]) -> None:
    for r, c in group:
        board[r][c] = EMPTY


def update_scores(state: dict) -> None:
    black = 0
    white = 0
    for row in state["board"]:
        for cell in row:
            if cell == BLACK:
                black += 1
            elif cell == WHITE:
                white += 1
    state["black_score"] = black
    state["white_score"] = white

def make_response(state: dict, ok: bool) -> dict:
    return {
        "ok": ok,
        "board_size": state["board_size"],
        "board": deepcopy(state["board"]),
        "current_player": state["current_player"],
        "black_score": state["black_score"],
        "white_score": state["white_score"],
        "consecutive_passes": state["consecutive_passes"],
        "move_number": state["move_number"],
        "game_over": state["game_over"],
        "message": state["message"],
    }

def is_board_full(board):
    for row in board:
        for cell in row:
            if cell is None:
                return False
    return True


def handle_move(game_state: dict, move_msg: dict) -> dict:

    '''
    move_msg example:
        {"type": "move", "move": "c3", "color": "black"}
        {"type": "pass", "color": "white"}
    '''
    
    state = deepcopy(game_state)

    if state["game_over"]:
        state["message"] = "Game is OVER"
        return make_response(state, False)

    msg_type = move_msg.get("type")
    color = move_msg.get("color")

    if color not in (BLACK, WHITE):
        state["message"] = "Invalid Color"
        return make_response(state, False)

    if color != state["current_player"]:
        state["message"] = f"Not {color}'s turn"
        return make_response(state, False)

    if msg_type == "pass":
        state["consecutive_passes"] += 1
        state["move_number"] += 1
        state["message"] = f"{color} passed"

        if state["consecutive_passes"] >=2:
            state["game_over"] = True
            update_scores(state)
            if state["black_score"] > state["white_score"]:
                state["message"] = "Black wins"
            elif state["white_score"] > state["black_score"]:
                state["message"] = "White wins"
            else:
                state["message"] = "Draw"
        else:
            state["current_player"] = other_player(color)

        return make_response(state, True)

    if msg_type != "move":
        state["message"] = "Invalid message type"
        return make_response(state, False)

    move = move_msg.get("move", "")

    try:
        row, col = parse_move(move, state["board_size"])
    except ValueError as exc:
        state["message"] = str(exc)
        return make_response(state, False)
    
    if state["board"][row][col] is not EMPTY:
        state["message"] = "Square already occupied"
        return make_response(state, False)

    # TRIAL BOARD ... test in simulation befor commit a move in Network
    trial_board = deepcopy(state["board"])
    trial_board[row][col] = color

    opponent = other_player(color)
    captured_count = 0
    checked = set()

    for nr, nc in get_neighbors(state["board_size"], row, col):
        if trial_board[nr][nc] != opponent or (nr, nc) in checked:
            continue
        group, liberties = get_group_and_liberties(trial_board, nr, nc)
        checked |= group
        if len(liberties) == 0:
            captured_count += len(group)
            remove_group(trial_board, group)

    own_group, own_liberties = get_group_and_liberties(trial_board, row, col)
    if len(own_liberties) == 0:
        state["message"] = "Illegal move: suicide is not allowed"
        return make_response(state, False)

    state["board"] = trial_board
    state["consecutive_passes"] = 0
    state["move_number"] += 1
    state["current_player"] = opponent
    update_scores(state)

    if is_board_full(state["board"]):
        state["game_over"] = True

        if state["black_score"] > state["white_score"]:
            state["message"] = "Board full. Game over. Black wins."
        elif state["white_score"] > state["black_score"]:
            state["message"] = "Board full. Game over. White wins."
        else:
            state["message"] = "Board full. Game over. Draw."

        return make_response(state, True)

    if captured_count > 0:
        state["message"] = f"{color} played {move} and captured {captured_count} stone(s)"
    else:
        state["message"] = f"{color} played {move}"

    return make_response(state, True)


def print_board(game_state: dict) -> None:
    size = game_state["board_size"]
    board = game_state["board"]
    files = [chr(ord("a") + i) for i in range(size)]

    print("   " + " ".join(files))
    for r in range(size):
        board_row_num = size - r
        rendered = []
        for c in range(size):
            cell = board[r][c]
            if cell == BLACK:
                rendered.append("B")
            elif cell == WHITE:
                rendered.append("W")
            else:
                rendered.append(".")
        print(f"{board_row_num:>2} " + " ".join(rendered))
    print("   " + " ".join(files))


def demo():
    state = create_game_state(5)
    print_board(state)

    messages = [
        {"type": "move", "move": "a1", "color": "black"},
        {"type": "move", "move": "b1", "color": "white"},
        {"type": "pass", "color": "black"},
        {"type": "pass", "color": "white"},
    ]

    for msg in messages:
        response = handle_move(state, msg)
        state = response
        print(response["message"])
        print_board(state)


# Testing Game State: - When PlayerWhite wins when a move is made.
def demo2():
    state = create_game_state(5)
    print_board(state)

    messages = [
        {"type": "move", "move": "b2", "color": "black"},
        {"type": "move", "move": "c2", "color": "white"},
        {"type": "move", "move": "c1", "color": "black"},
        {"type": "move", "move": "e5", "color": "white"},
        {"type": "move", "move": "c3", "color": "black"},
        {"type": "move", "move": "a5", "color": "white"},
        {"type": "move", "move": "d2", "color": "black"}
    ]

    for msg in messages:
        response = handle_move(state, msg)
        state = response
        print(response["message"])
        print_board(state)


if __name__ == "__main__":
    # demo()
    demo2()

