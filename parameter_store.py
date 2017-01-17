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

    @abstractmethod
    def delete(self, key):
        pass


class NamedParameterStore(ParameterStore):
    def __init__(self, name):
        self.conf = {}
        self.name = name

    def __normalize_key_for_param(self, a_key):
        prefixes = []
        if REDIS_KEY_PREFIX not in a_key:
            prefixes.append(REDIS_KEY_PREFIX)
        if self.name not in a_key:
            prefixes.append(self.name)

        if len(prefixes) > 0:
            prefixes.append(a_key)
            ret = ':'.join(prefixes)
        else:
            ret = a_key

        return ret

    def _key_for_param(self, key_or_keys):
        prefixes = []
        if isinstance(key_or_keys, list):
            suffix = ':'.join(key_or_keys)
        elif isinstance(key_or_keys, str):
            suffix = key_or_keys
        else:
            raise ValueError("Only str or list key is acceptable")

        if REDIS_KEY_PREFIX not in suffix:
            prefixes.append(REDIS_KEY_PREFIX)
        if self.name not in suffix:
            prefixes.append(self.name)
        return ':'.join(prefixes + [suffix])

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

    @abstractmethod
    def delete(self, key):
        pass
