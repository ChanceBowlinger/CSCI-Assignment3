'''
Board Size
Current Player : Black/White
black score :
white score :
consecutive passes : -- if 2 passes reach game stops
move number : 
message : -- game result/ if illegal move is made
'''

from random import randrange
from math import ceil, sqrt


class Board:
    def __init__(self, board_size, margin=2):
        self.EMPTY = 0
        self.BLACK = 1
        self.WHITE = 2
        self.MARKER = 4
        self.OFFBOARD = 7
        self.LIBERTY = 8
        self.pieces = '.#o  bw +'

        self.BOARD_SIZE = board_size
        self.MARGIN = margin
        self.BOARD_RANGE = board_size + self.MARGIN
        self.board = self.create()

    def create(self):
        top_bottom_row = [self.OFFBOARD] * self.BOARD_RANGE
        middle_row = [self.OFFBOARD] + [self.EMPTY] * self.BOARD_SIZE + [self.OFFBOARD]
        board = [top_bottom_row] + [middle_row[:] for _ in range(self.BOARD_SIZE)] + [top_bottom_row]
        return [item for sublist in board for item in sublist]

    def render(self):
        files = [chr(ascii_code) for ascii_code in range(97, 97 + self.BOARD_SIZE)]

        print('\n' + '    ' + ' '.join(files), end='')
        for row in range(self.BOARD_RANGE):
            for col in range(self.BOARD_RANGE):
                if 0 < row < self.BOARD_RANGE - 1:
                    if col == 0:
                        cur_row = self.BOARD_RANGE - 1 - row
                        print('' + str(cur_row) if cur_row >= 10 else ' ' + str(cur_row), end='')
                    elif col == self.BOARD_RANGE - 1:
                        cur_row = self.BOARD_RANGE - 1 - row
                        print(' ' + str(cur_row), end='')

                square = row * self.BOARD_RANGE + col
                stone = self.board[square]
                print(self.pieces[stone] + ' ', end='')
            print()
        print('    ' + ' '.join(files) + '\n')

    def reset(self):
        self.board = self.create()

    def place_stone(self, square, color):
        self.board[square] = color

    def remove_stone(self, square):
        self.board[square] = self.EMPTY

    def count(self, square, color):
        group = set()
        liberties = set()
        piece = self.board[square]
        if piece != self.OFFBOARD:
            if (piece & 3) and (piece & color) and (piece & self.MARKER) == 0:
                group.add(square)
                self.board[square] |= self.MARKER
                for delta in [-self.BOARD_RANGE, 1, self.BOARD_RANGE, -1]:
                    next_group, next_liberties = self.count(square + delta, color)
                    group |= next_group
                    liberties |= next_liberties
            elif piece == self.EMPTY:
                self.board[square] |= self.LIBERTY
                liberties.add(square)
        return group, liberties

    def restore(self):
        for square in range(self.BOARD_RANGE * self.BOARD_RANGE):
            if self.board[square] != self.OFFBOARD:
                self.board[square] &= 3

    def clear_group(self, group):
        for captured in group:
            self.board[captured] = self.EMPTY


def check_input(input_string, board_size):
    outstate = 0
    if len(input_string) == 0:
        msg = 'Input not provided.'
    else:
        last_char = chr(97 + board_size - 1)
        column = input_string[0].lower()
        msg = 'Unknown error.'
        if last_char < 'a' or last_char > 'z':
            msg = "Invalid last character. Must be between 'a' and 'z'."
        elif column < 'a' or column > last_char:
            msg = "Invalid column input, it must be between 'a' and '{}'".format(last_char)
        else:
            if input_string[1:].isdigit():
                row = int(input_string[1:])
                if row < 1 or row > board_size:
                    msg = 'Invalid row, it must be between 1 and {}'.format(board_size)
                else:
                    outstate = 1
            else:
                msg = 'Invalid row.'
    if not outstate:
        print(msg)
    return outstate


def move2square(move, board_range):
    return (1 + int(move[1:])) * -board_range + ord(move[0].lower()) % 97 + 1


def square2move(square, board_range):
    col = chr(97 + (square % board_range - 1))
    row = str(board_range - 1 - square // board_range)
    return col + row


def opposite_color(board, color):
    return board.WHITE if color == board.BLACK else board.BLACK


def color_name(board, color):
    return 'Black' if color == board.BLACK else 'White'


def place_handicap_stones(board):
    num_placed_stones = 0
    while num_placed_stones < ceil(sqrt(board.BOARD_SIZE)):
        square = (1 + randrange(1, board.BOARD_SIZE + 1)) * -board.BOARD_RANGE + randrange(1, board.BOARD_SIZE + 1)
        if not board.board[square] & 7:
            board.place_stone(square, board.BLACK)
            num_placed_stones += 1


def get_group_and_liberties(board, square, color):
    group, liberties = board.count(square, color)
    board.restore()
    return group, liberties


def capture_dead_groups(board, color):
    captured_groups = []
    visited = set()

    for square in range(board.BOARD_RANGE * board.BOARD_RANGE):
        if square in visited:
            continue
        if board.board[square] != color:
            continue

        group, liberties = get_group_and_liberties(board, square, color)
        visited |= group
        if len(liberties) == 0:
            captured_groups.append(group)

    total_captured = 0
    for group in captured_groups:
        total_captured += len(group)
        board.clear_group(group)

    return total_captured


def apply_move(board, move, color):
    if not check_input(move, board.BOARD_SIZE):
        return False

    square = move2square(move, board.BOARD_RANGE)
    if board.board[square] & 7:
        print('Square already occupied.')
        return False

    board.place_stone(square, color)

    opponent = opposite_color(board, color)
    captured = capture_dead_groups(board, opponent)

    own_group, own_liberties = get_group_and_liberties(board, square, color)
    if len(own_liberties) == 0:
        board.clear_group(own_group)
        print('Illegal move: suicide is not allowed.')
        return False

    if captured:
        print(f'{color_name(board, color)} captured {captured} stone(s).')

    return True



def calculate_score(board):
    black = 0
    white = 0

    for square in board.board:
        if square == board.BLACK:
            black += 1
        elif square == board.WHITE:
            white += 1

    return black, white


def print_score(board):
    black, white = calculate_score(board)
    print(f'Score -> Black: {black}, White: {white}')
    if black > white:
        print('Black wins!')
    elif white > black:
        print('White wins!')
    else:
        print('Draw!')


def main():
    while True:
        input_board_size = input('Which board would you like to choose: ')
        try:
            board_size = int(input_board_size)
            if board_size <= 0:
                raise ValueError
            if board_size > 26:
                print('Please choose a board size up to 26.')
                continue
            board = Board(board_size)
            break
        except ValueError:
            print('Invalid board size!')

    current_player = board.BLACK
    consecutive_passes = 0

    print("Commands: coordinates like 'c3', or 'pass', 'reset', 'quit'.")

    while True:
        board.render()
        move = input(f'{color_name(board, current_player)} to move: ').strip().lower()

        if move == 'quit':
            print('Quitting game...')
            return

        if move == 'reset':
            board.reset()
            current_player = board.BLACK
            consecutive_passes = 0
            continue

        if move == 'handicap':
            board.reset()
            place_handicap_stones(board)
            current_player = board.WHITE
            consecutive_passes = 0
            continue

        if move == 'pass':
            print(f'{color_name(board, current_player)} passes.')
            consecutive_passes += 1
            if consecutive_passes >= 2:
                board.render()
                print('Both players passed. Game over.')
                print_score(board)
                return
            current_player = opposite_color(board, current_player)
            continue

        if apply_move(board, move, current_player):
            consecutive_passes = 0
            current_player = opposite_color(board, current_player)


if __name__ == '__main__':
    main()
