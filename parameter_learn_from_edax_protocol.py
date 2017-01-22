from parameter_progress_position_moves_learn import ProgressPositionMovesParameter
from parameter import board_from_a_book
import commands
from ast import literal_eval


def counts(a_book, side, path):
    a_board = board_from_a_book(a_book)
    sfen = a_board.serialize_str()
    command = (path + " -h \"%s\"") % sfen
    hash_in_list_str = check = commands.getoutput(command)
    hash_in_list = literal_eval(hash_in_list_str)
    return [(64 - a_board.n_empty())] + [int(x) for x in hash_in_list]


class LearnFromEdaxProtocolProcessParameter(ProgressPositionMovesParameter):
    def __init__(self):
        super(LearnFromEdaxProtocolProcessParameter, self).__init__()
        self.conf = None
        pass

    def configure(self, conf):
        self.conf = conf

    def header(self):
        return 3

    def default_value(self):
        return [
            [100, 99, -1, -1, -1, -1, 3, 8, 20],
            [75, 99, 2,  -5,  7,  6,  4,  5, 5],
            [25, 99, 2,  -5,  -7,  -6,  4,  5, 5],
            [1, 100, 50, 30, 30, 30, 30, 30, 30]
        ]

    def hash_from_book(self, a_book, side):
        path = self.conf['learn_learn_for_path']
        count_list = counts(a_book, side, path)
        return ':'.join(map(lambda x: str(x), count_list))

