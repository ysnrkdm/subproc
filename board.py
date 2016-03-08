import re

COLORS = (
    Empty,
    Black,
    White,
) = range(0, 3)

DIRECS =(
    LU, U, RU,
    L,      R,
    LD, D, RD
) = [
    (-1, -1), (0, -1), (1, -1),
    (-1,  0),          (1,  0),
    (-1,  1), (0,  1), (1,  1)
]


class Board:

    def __init__(self):
        self.board = [[Empty for i in range(8)] for j in range(8)]
        self.board[3][3] = self.board[4][4] = White
        self.board[3][4] = self.board[4][3] = Black
        self.turn = Black

    def count_over_board(self, fun):
        ret = 0
        for row in self.board:
            for cell in row:
                if fun(cell):
                    ret += 1
        return ret

    def n_black(self):
        return self.count_over_board(lambda cell: cell == Black)

    def n_white(self):
        return self.count_over_board(lambda cell: cell == White)

    def n_empty(self):
        return self.count_over_board(lambda cell: cell == Empty)

    def n_puttable_for(self, piece):
        ret = 0
        for y in range(len(self.board)):
            for x in range(len(self.board[y])):
                if self.is_puttable_at(piece, x, y):
                    ret += 1
        return ret

    def is_game_over(self):
        return self.n_puttable_for(Black) == 0 and self.n_puttable_for(White) == 0

    def set(self, piece, x, y):
        self.board[y][x] = piece

    def str_from_turn(self, color):
        if color == Black:
            return 'Black'
        elif color == White:
            return 'White'
        else:
            return 'None'

    def __str__(self):
        current_turn = self.str_from_turn(self.turn)
        pudding = "      "

        ret = '  A B C D E F G H\n'
        i = 1
        for row in self.board:
            ret += str(i) + ''
            for cell in row:
                ret += ' '
                if cell == 1:
                    ret += '*'
                elif cell == 2:
                    ret += 'O'
                else:
                    ret += '.'
                ret += ''
            if i == 4:
                ret += pudding + current_turn + '\'s turn'
            elif i == 5:
                ret += pudding + 'Black: ' + str(self.n_black())
            elif i == 6:
                ret += pudding + 'White: ' + str(self.n_white())
            ret += '\n'
            i += 1

        # ret += '\n'

        return ret

    def hands_for_direc(self, direc, piece, x, y):
        ret = []
        hostile = self.hostile(piece)
        dx = direc[0]
        dy = direc[1]
        for i in range(1, 9):
            nx = x + i * dx
            ny = y + i * dy
            if is_within_board(nx, ny) and self.board[ny][nx] == hostile:
                ret.append((piece, nx, ny))
            elif is_within_board(nx, ny) and self.board[ny][nx] == piece:
                break
            else:
                ret = []
                break
        return ret

    def is_puttable_at(self, piece, x, y):
        if self.board[y][x] != Empty:
            return False

        n_puttable = 0
        for direc in DIRECS:
            possible_hands = self.hands_for_direc(direc, piece, x, y)
            n_puttable += len(possible_hands)
        return n_puttable > 0

    def set_hands(self, hands):
        for (piece, x, y) in hands:
            self.set(piece, x, y)

    def hostile(self, piece):
        if piece == Black:
            return White
        else:
            return Black

    def put(self, piece, x, y):
        if self.board[y][x] != Empty:
            return 0

        count = 0

        for direc in DIRECS:
            possible_hands = self.hands_for_direc(direc, piece, x, y)
            if len(possible_hands):
                self.set_hands(possible_hands)
                count += len(possible_hands)
                self.set(piece, x, y)

        return count

    def put_s(self, stri):
        out = -1
        if stri == 'PS':
            out = 0
        else:
            b = re.findall(r"[WB]*([a-zA-Z])([0-9])", stri)
            if len(b) > 0:
                col = b[0][0].lower()
                row = b[0][1]
                x = ord(col) - ord('a')
                y = ord(row) - ord('1')
                out = self.put(self.turn, x, y)
                if out == 0:
                    out = -1

        if out >= 0:
            if self.turn == Black:
                self.turn = White
            else:
                self.turn = Black
        return out

    def serialize_tuple(self):
        return self.board, self.turn

    def serialize_str(self):
        ret = ''
        i = 1
        for row in self.board:
            for cell in row:
                ret += ''
                if cell == White:
                    ret += 'X'
                elif cell == Black:
                    ret += 'O'
                else:
                    ret += '-'
                ret += ''
            ret += ''
            i += 1
        ret += ' '
        if self.turn == Black:
            ret += 'O'
        elif self.turn == White:
            ret += 'X'
        else:
            ret += ''

        return ret


def is_within_board(x, y):
    return 0 <= x < 8 and 0 <= y < 8


def clone_board(board):
    new_board = [[Empty for i in range(8)] for j in range(8)]

    for i in range(8):
        for j in range(8):
            new_board[i][j] = board[i][j]

    return new_board
