from abc import ABCMeta, abstractmethod
from datetime import datetime


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

    @abstractmethod
    def load(self):
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

    def add(self, serialize_str):
        self.lines.append(serialize_str)

    def store(self):
        path = self.output_path + '/' + self.title + '_' + self.timestamp
        print 'Writing to file: ' + path + '\n'
        f = open(path, 'w+')
        for line in self.lines:
            f.write(line + "\n")
        f.close()
        print 'File closed\n'

    def load(self):
        raise NotImplementedError('load is not implemented yet, sorry!')

GameRecorder.register(FlatFileRecorder)


class RedisRecorder(GameRecorder):

    def load(self):
        raise NotImplementedError('load is not implemented yet, sorry!')

GameRecorder.register(RedisRecorder)
