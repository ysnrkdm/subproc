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
        self.nturn = 0

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

    def puttables(self, piece):
        ret = []
        for y in range(len(self.board)):
            for x in range(len(self.board[y])):
                if self.is_puttable_at(piece, x, y):
                    ret.append((x, y))
        return ret

    def n_puttable_for(self, piece):
        return len(self.puttables(piece))

    def is_game_over(self):
        return self.n_puttable_for(Black) == 0 and self.n_puttable_for(White) == 0

    def set(self, piece, x, y):
        self.board[y][x] = piece

    def get(self, x, y):
        return self.board[y][x]

    def str_from_turn(self, color):
        if color == Black:
            return 'Black'
        elif color == White:
            return 'White'
        else:
            return 'None'

    def mask_count(self, color, mask):
        # mask to arrays
        ret = 0
        for i in range(0, 8):
            for j in range(0, 8):
                if (mask >> j+i*8) & 1 > 0 and self.get(j, i) == color:
                        ret += 1
        return ret

    @classmethod
    def show_mask(cls, mask):
        q = Board()
        for i in range(0, 8):
            for j in range(0, 8):
                if (mask >> j+i*8) & 1 > 0:
                    q.set(Black, j,i)
                else:
                    q.set(Empty, j,i)
        print q

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

    def coord_from_handstr(self, handstr):
        b = re.findall(r"[WB]*([a-zA-Z])([0-9])", handstr)
        if len(b) > 0:
            col = b[0][0].lower()
            row = b[0][1]
            x = ord(col) - ord('a')
            y = ord(row) - ord('1')
            return x, y
        else:
            return -1, -1

    def handstr_from_coord(self, coord):
        x, y = coord
        sx = chr(ord('a') + x)
        sy = chr(ord('1') + y)
        return sx + sy

    def put_s(self, stri):
        out = -1
        if stri == 'PS' or stri == 'ps':
            out = 0
        else:
            x, y = self.coord_from_handstr(stri)
            if x >= 0 and y >= 0:
                out = self.put(self.turn, x, y)
                if out == 0:
                    out = -1

        if out >= 0:
            self.nturn += 1
            if self.turn == Black:
                self.turn = White
            else:
                self.turn = Black
        return out

    def serialize_tuple(self):
        return self.board, self.turn

    def serialize_str(self, append_turn=True):
        ret = ''
        ret += self.serialize_board()
        if append_turn:
            ret += ' '
            ret += self.serialize_turn()

        return ret

    def serialize_board(self):
        ret = ''
        i = 1
        for row in self.board:
            for cell in row:
                ret += self.string_from_turn(cell)
                ret += ''
            ret += ''
            i += 1
        return ret

    def serialize_turn(self):
        return self.string_from_turn(self.turn)

    def string_from_turn(self, turn):
        if turn == Black:
            return 'O'
        elif turn == White:
            return 'X'
        else:
            return '-'

    def turn_from_string(self, turn_string):
        if turn_string == 'O':
            return Black
        elif turn_string == 'X':
            return White
        else:
            return Empty

    def deserialize(self, board_str, turn_str, nturn):
        i = 0
        for s in board_str:
            cell = self.turn_from_string(s)
            self.set(cell, i % 8, i / 8)
            i += 1

        self.turn = self.turn_from_string(turn_str)

        self.nturn = nturn


def is_within_board(x, y):
    return 0 <= x < 8 and 0 <= y < 8


def clone_board(board):
    new_board = [[Empty for i in range(8)] for j in range(8)]

    for i in range(8):
        for j in range(8):
            new_board[i][j] = board[i][j]

    return new_board
