from parameter import ParameterBasePlus
from parameter import board_from_a_book


def counts(a_book, side):
    a_board = board_from_a_book(a_book)
    turn = a_board.turn_from_string(side)
    moves = a_board.n_puttable_for(turn)
    a = a_board.mask_count(turn, 0x8100000000000081)
    b = a_board.mask_count(turn, 0x4281000000008142)
    c = a_board.mask_count(turn, 0x0042000000004200)
    d = a_board.mask_count(turn, 0x2400810000810024)
    e = a_board.mask_count(turn, 0x1800008181000018)
    f = a_board.mask_count(turn, 0x003C424242423C00)
    g = a_board.mask_count(turn, 0x0000240000240000)
    h = a_board.mask_count(turn, 0x0000183C3C180000)
    return (64 - a_board.n_empty()), moves, a, b, c, d, e, f, g, h


class ProgressPositionMovesParameter(ParameterBasePlus):
    def __init__(self):
        pass

    def configure(self, conf):
        pass

    def header(self):
        return 2

    def default_value(self):
        return [
            [100, 99, -1, -1, -1, -1, 3, 8, 20],
            [75, 99, 2,  -5,  7,  6,  4,  5, 5],
            [25, 99, 2,  -5,  -7,  -6,  4,  5, 5],
            [1, 100, 50, 30, 30, 30, 30, 30, 30]
        ]

    def __state_from_hash(self, hash_key):
        return tuple(map(lambda x: int(x), hash_key.split(":")[4:]))

    def features_from_hash(self, hash_key):
        return self.__state_from_hash(hash_key)[1:]

    def phase_from_hash(self, hash_key):
        return self.__state_from_hash(hash_key)[0]

    def hash_from_book(self, a_book, side):
        count_list = counts(a_book, side)
        return ':'.join(map(lambda x: str(x), count_list))

