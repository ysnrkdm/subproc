from abc import ABCMeta, abstractmethod
import board


def board_from_a_book(a_book):
    a_board = board.Board()
    a_board.deserialize(a_book['book'], a_book['whosturn'], a_book['turn'])
    return a_board


class ParameterBase(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def configure(self, conf):
        pass

    @abstractmethod
    def header(self):
        pass

    @abstractmethod
    def default_value(self):
        pass

    @abstractmethod
    def features_from_hash(self, hash_key):
        pass

    @abstractmethod
    def phase_from_hash(self, hash_key):
        pass

    @abstractmethod
    def hash_from_book(self, a_book, side):
        pass


class ParameterBasePlus(ParameterBase):

    @abstractmethod
    def configure(self, conf):
        pass

    @abstractmethod
    def header(self):
        pass

    @abstractmethod
    def default_value(self):
        pass

    @abstractmethod
    def features_from_hash(self, hash_key):
        pass

    @abstractmethod
    def phase_from_hash(self, hash_key):
        pass

    @abstractmethod
    def hash_from_book(self, a_book, side):
        pass
