from abc import ABCMeta, abstractmethod

REDIS_KEY_PREFIX = 'othelloparam'


class ParameterStore(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def keys(self, pattern):
        pass

    @abstractmethod
    def exists(self, key):
        pass

    @abstractmethod
    def get(self, key):
        pass

    @abstractmethod
    def set(self, key, value):
        pass

    @abstractmethod
    def hget(self, key, field):
        pass

    @abstractmethod
    def hset(self, key, field, value):
        pass

    @abstractmethod
    def hmget(self, key, fields):
        pass

    @abstractmethod
    def hmset(self, key, mapping):
        pass

    @abstractmethod
    def hgetall(self, key):
        pass

class NamedParameterStore(ParameterStore):
    def __init__(self, name):
        self.conf = {}
        self.name = name

    def _key_for_param(self, key_or_keys):
        if isinstance(key_or_keys, list):
            a_keys = [REDIS_KEY_PREFIX, self.name] + key_or_keys
            return ':'.join(a_keys)
        elif isinstance(key_or_keys, str):
            a_keys = [REDIS_KEY_PREFIX, self.name]
            return ':'.join(a_keys) + key_or_keys
        else:
            raise ValueError("Only str or list key is acceptable")

    def configure(self, conf_dict):
        self.conf = conf_dict

    @abstractmethod
    def keys(self, pattern):
        pass

    @abstractmethod
    def exists(self, key):
        pass

    @abstractmethod
    def get(self, key):
        pass

    @abstractmethod
    def set(self, key, value):
        pass

    @abstractmethod
    def hget(self, key, field):
        pass

    @abstractmethod
    def hset(self, key, field, value):
        pass

    @abstractmethod
    def hmget(self, key, fields):
        pass

    @abstractmethod
    def hmset(self, key, mapping):
        pass

    @abstractmethod
    def hgetall(self, key):
        pass
