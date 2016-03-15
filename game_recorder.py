from abc import ABCMeta, abstractmethod
from datetime import datetime
import redis


class GameRecorder(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def configure(self, title, meta, config_dict):
        pass

    @abstractmethod
    def add(self, serialize_data):
        pass

    @abstractmethod
    def store(self):
        pass


class FlatFileRecorder(GameRecorder):

    def __init__(self):
        self.lines = []
        self.output_path = ''
        self.title = ''
        self.meta = ''
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def configure(self, title, meta, config_dict):
        self.output_path = config_dict['output_path']

    def add(self, game_board):
        print game_board
        line = game_board.serialize_str()
        self.lines.append(line)

    def store(self):
        path = self.output_path + '/' + self.title + '_' + self.timestamp
        print 'Writing to file: ' + path + '\n'
        f = open(path, 'w+')
        for line in self.lines:
            f.write(line + "\n")
        f.close()
        print 'File closed\n'

GameRecorder.register(FlatFileRecorder)


class RedisRecorder(GameRecorder):

    def __init__(self):
        self.r = None
        self.r_count = None
        self.lines = []
        self.dbkeyprefix = 'DEFAULT'
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def configure(self, title, meta, config_dict):
        self.r = redis.Redis(host=config_dict['host'], port=config_dict['port'], db=config_dict['db'])
        self.r_count = redis.Redis(host=config_dict['hostcount'], port=config_dict['portcount'], db=config_dict['dbcount'])
        self.dbkeyprefix = config_dict['dbkeyprefix']

    def add(self, game_board):
        obj = {
            'book': game_board.serialize_board(),
            'whosturn': game_board.serialize_turn(),
            'turn': game_board.nturn,
            'end': game_board.is_game_over()
        }
        self.lines.append(obj)

    def get_id(self):
        if not self.r_count.exists('count'):
            self.r_count.set('count', 0)
        return self.r_count.incr('count')

    def store(self):
        book_id = self.get_id()
        entry_key = ':'.join([self.dbkeyprefix, str(book_id)])
        n_turn = 0
        for a_book in self.lines:
            for k, v in a_book.items():
                key_turn = ':'.join([entry_key, str(n_turn)])
                self.r.hset(key_turn, k, v)
                self.r.hset(key_turn, 'timestamp', self.timestamp)
            n_turn += 1

GameRecorder.register(RedisRecorder)
