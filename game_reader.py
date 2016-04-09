from abc import ABCMeta, abstractmethod
from datetime import datetime
import redis


class GameReader(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def configure(self, title, meta, config_dict):
        pass

    @abstractmethod
    def list_by_id(self, book_id):
        pass

    @abstractmethod
    def list_all(self):
        pass

    @abstractmethod
    def load_by_id(self, book_id):
        pass

    @abstractmethod
    def load_all(self):
        pass


class RedisReader(GameReader):

    def __init__(self):
        self.r = None
        self.lines = []
        self.book_db_key_prefix = 'DEFAULT'
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def configure(self, title, meta, config_dict):
        self.r = redis.Redis(host=config_dict['host'], port=config_dict['port'], db=config_dict['db'])
        self.book_db_key_prefix = config_dict['dbkeyprefix']

    def list_by_id(self, book_id):
        # print book_id
        wildcard_key = ':'.join([self.book_db_key_prefix, str(book_id), '*'])
        # print '\n' + wildcard_key + '\n'
        ret = self.r.keys(wildcard_key)
        return ret

    def list_all(self):
        entry_key = ':'.join([self.book_db_key_prefix, '*'])
        list_from_redis = self.r.keys(entry_key)
        return list_from_redis

    def load_by_id(self, book_id):
        entry_keys_to_process = self.list_by_id(book_id)
        # print entry_keys_to_process
        ret = []
        meta_key = ''
        for entry_key in entry_keys_to_process:
            if 'meta' in entry_key:
                meta_key = entry_key
                continue
            (turn, timestamp, whosturn, book, end) =\
                self.r.hmget(entry_key, 'turn', 'timestamp', 'whosturn', 'book', 'end')
            obj = {
                'book': book,
                'whosturn': whosturn,
                'turn': turn,
                'end': end,
                'timestamp': timestamp
            }
            ret.append(obj)

        if len(meta_key) > 0:
            meta = self.r.hgetall(meta_key)
        else:
            meta = {}

        return meta, ret

    def load_all(self):
        ids = self.list_all()
        ret = {}
        for book_id in ids:
            list_book = self.load_by_id(book_id)
            ret[str(book_id)] = list_book
        return ret

GameReader.register(RedisReader)
