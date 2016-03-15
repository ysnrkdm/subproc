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
    def list_unprocessed(self):
        pass

    @abstractmethod
    def load_by_id(self, book_id):
        pass

    @abstractmethod
    def load_all(self):
        pass

    @abstractmethod
    def load_all_unprocessed(self):
        pass


class RedisReader(GameReader):

    def __init__(self):
        self.r = None
        self.r_param = None
        self.lines = []
        self.book_db_key_prefix = 'DEFAULT'
        self.param_db_key_prefix = 'DEFAULTPARAM'
        self.param_learn_name = 'DEFAULTLEARNER'
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def configure(self, title, meta, config_dict):
        self.r = redis.Redis(host=config_dict['host'], port=config_dict['port'], db=config_dict['db'])
        self.r_param = redis.Redis(host=config_dict['hostparam'], port=config_dict['portparam'], db=config_dict['dbparam'])
        self.book_db_key_prefix = config_dict['dbkeyprefix']
        self.param_db_key_prefix = config_dict['paramdbkeyprefix']
        self.param_learn_name = config_dict['param_learn_name']

    def list_by_id(self, book_id):
        wildcard_key = ':'.join([self.book_db_key_prefix, str(book_id), '*'])
        ret = self.r.keys(wildcard_key)
        return ret

    def list_all(self):
        entry_key = ':'.join([self.book_db_key_prefix, '*'])
        list_from_redis = self.r.keys(entry_key)
        return list_from_redis

    def list_unprocessed(self):
        last_processed = self.r_param.get(':'.join([self.param_db_key_prefix, self.param_learn_name, 'LastProcessed']))
        list_all = self.list_all()
        ret = []
        for name in list_all:
            book_id = name.split(':')[1]
            if book_id > last_processed:
                ret.append(name)
        return ret

    def load_by_id(self, book_id):
        entry_keys_to_process = self.list_by_id(book_id)
        ret = []
        for entry_key in entry_keys_to_process:
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

        return ret

    def load_all(self):
        ids = self.list_all()
        ret = {}
        for book_id in ids:
            list_book = self.load_by_id(book_id)
            ret[str(book_id)] = list_book
        return ret

    def load_all_unprocessed(self):
        ids = self.list_unprocessed()
        ret = {}
        for book_id in ids:
            list_book = self.load_by_id(book_id)
            ret[str(book_id)] = list_book
        return ret

GameReader.register(RedisReader)
