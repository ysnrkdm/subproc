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


class NamedParameterStore(ParameterStore):
    def __init__(self, name):
        self.conf = {}
        self.name = name

    def _key_for_param(self, keys_array):
        a_keys = [REDIS_KEY_PREFIX, self.name] + keys_array
        return ':'.join(a_keys)

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
