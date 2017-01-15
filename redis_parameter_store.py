from parameter_store import NamedParameterStore
import redis


class RedisParameterStore(NamedParameterStore):
    def __init__(self, name):
        super(RedisParameterStore).__init__(name)
        self.r_param = None

    def configure(self, conf_dict):
        super(RedisParameterStore).configure(conf_dict)
        self.r_param = redis.Redis(host=self.conf['redis_hostname'], port=self.conf['redis_port'],
                                   db=self.conf['redis_db_param'], password=self.conf['redis_password'])

    def _redis_param(self):
        return self.r_param

    def keys(self, key_pattern):
        r_param = self._redis_param()
        fully_qualified_pattern = self._key_for_param(key_pattern)
        return r_param.keys(fully_qualified_pattern)

    def exists(self, key):
        r_param = self._redis_param()
        fully_qualified_key = self._key_for_param(key)
        return r_param.exists(fully_qualified_key)

    def get(self, key):
        r_param = self._redis_param()
        fully_qualified_key = self._key_for_param(key)
        return r_param.get(fully_qualified_key)

    def set(self, key, value):
        r_param = self._redis_param()
        fully_qualified_key = self._key_for_param(key)
        return r_param.set(fully_qualified_key, value)

    def hget(self, key, field):
        r_param = self._redis_param()
        fully_qualified_key = self._key_for_param(key)
        return r_param.hget(fully_qualified_key, field)

    def hset(self, key, field, value):
        r_param = self._redis_param()
        fully_qualified_key = self._key_for_param(key)
        return r_param.hset(fully_qualified_key, field, value)
