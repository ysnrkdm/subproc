from abc import ABCMeta, abstractmethod
from datetime import datetime
import redis
import boto3
from boto3.dynamodb.conditions import Key
import decimal


class GameRecorder(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def __enter__(self):
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @abstractmethod
    def graceful_exit(self):
        pass

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
    def add_meta(self, meta_dict):
        pass


class FlatFileRecorder(GameRecorder):

    def __init__(self):
        self.lines = []
        self.output_path = ''
        self.title = ''
        self.meta = {}
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def graceful_exit(self):
        pass

    def configure(self, title, meta, config_dict):
        self.output_path = config_dict['flatfile_output_path']

    def add(self, game_board):
        # print game_board
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

    def add_meta(self, meta_dict):
        self.meta.update(meta_dict)

GameRecorder.register(FlatFileRecorder)


class RedisRecorder(GameRecorder):

    def __init__(self):
        self.r = None
        self.lines = []
        self.meta = {'meta': 'meta'}
        self.dbkeyprefix = 'DEFAULT'
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def graceful_exit(self):
        pass

    def configure(self, title, meta, config_dict):
        self.r = redis.Redis(host=config_dict['redis_hostname'], port=config_dict['redis_port'],
                             db=config_dict['redis_db_book'], password=config_dict['redis_password'])
        self.dbkeyprefix = config_dict['redis_book_dbkeyprefix']

    def add(self, game_board):
        obj = {
            'book': game_board.serialize_board(),
            'whosturn': game_board.serialize_turn(),
            'turn': game_board.nturn,
            'end': game_board.is_game_over()
        }
        self.lines.append(obj)

    def __get_id(self):
        if not self.r.exists('count'):
            self.r.set('count', 0)
        return self.r.incr('count')

    def store(self):
        # TODO: make below as ACID
        book_id = self.__get_id()
        entry_key = ':'.join([self.dbkeyprefix, str(book_id)])
        n_turn = 0
        for a_book in self.lines:
            for k, v in a_book.items():
                key_turn = ':'.join([entry_key, str(n_turn)])
                self.r.hset(key_turn, k, v)
                self.r.hset(key_turn, 'timestamp', self.timestamp)
            n_turn += 1
        key_meta = ':'.join([entry_key, 'meta'])
        self.r.hmset(key_meta, self.meta)

    def add_meta(self, meta_dict):
        self.meta.update(meta_dict)

GameRecorder.register(RedisRecorder)


class DynamoDBRecorder(GameRecorder):

    def __init__(self):
        self.client = None
        self.resource = None
        self.table_name = 'DEFAULT_TABLE_NAME'
        self.lines = []
        self.meta = {'meta': 'meta'}
        self.dbkeyprefix = 'DEFAULT'
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.needs_graceful_exit = False

    def __enter__(self):
        print 'incrementing queue number'
        table = self.__get_table()
        self.__init_meta_data()
        # atomic increment
        table.update_item(Key={'book_id': 0, 'board_id': 0},
                          UpdateExpression="set info.working_processes = info.working_processes + :val",
                          ExpressionAttributeValues={':val': decimal.Decimal(1)},
                          ReturnValues="UPDATED_NEW")
        self.needs_graceful_exit = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.graceful_exit()
        return False

    def graceful_exit(self):
        if self.needs_graceful_exit:
            table = self.__get_table()
            self.__init_meta_data()
            # atomic increment
            table.update_item(Key={'book_id': 0, 'board_id': 0},
                              UpdateExpression="set info.working_processes = info.working_processes - :val",
                              ExpressionAttributeValues={':val': decimal.Decimal(1)},
                              ReturnValues="UPDATED_NEW")
            print 'decrementing queue number'

    def __init_meta_data(self):
        table = self.__get_table()
        res = table.query(KeyConditionExpression=Key('book_id').eq(0))
        if res['Count'] == 0:
            table.put_item(Item={'book_id': 0, 'board_id': 0, 'info': {'working_processes': 0, 'latest_book_id': 0}})

    def configure(self, title, meta, config_dict):
        self.client = boto3.client('dynamodb', endpoint_url=config_dict['dynamodb_endpoint_url'],
                                   region_name=config_dict['dynamodb_region_name'],
                                   aws_access_key_id=config_dict['dynamodb_aws_access_key_id'],
                                   aws_secret_access_key=config_dict['dynamodb_aws_secret_access_key'])
        self.resource = boto3.resource('dynamodb', endpoint_url=config_dict['dynamodb_endpoint_url'],
                                       region_name=config_dict['dynamodb_region_name'],
                                       aws_access_key_id=config_dict['dynamodb_aws_access_key_id'],
                                       aws_secret_access_key=config_dict['dynamodb_aws_secret_access_key'])
        self.table_name = config_dict['dynamodb_book_table_name']

    def add(self, game_board):
        obj = {
            'book': game_board.serialize_board(),
            'whosturn': game_board.serialize_turn(),
            'turn': game_board.nturn,
            'end': game_board.is_game_over(),
            'timestamp': self.timestamp
        }
        self.lines.append(obj)

    def __get_table(self):
        if not unicode(self.table_name) in self.client.list_tables()['TableNames']:
            table = self.resource.create_table(TableName=self.table_name,
                                               KeySchema=[
                                                   {'AttributeName': 'book_id', 'KeyType': 'HASH'},
                                                   {'AttributeName': 'board_id', 'KeyType': 'RANGE'}],
                                               AttributeDefinitions=[
                                                   {'AttributeName': 'book_id', 'AttributeType': 'N'},
                                                   {'AttributeName': 'board_id', 'AttributeType': 'N'}],
                                               ProvisionedThroughput={
                                                   'ReadCapacityUnits': 10,
                                                   'WriteCapacityUnits': 10})
        else:
            table = self.resource.Table(self.table_name)
        return table

    def __get_id(self):
        table = self.__get_table()
        self.__init_meta_data()
        # atomic increment
        res = table.update_item(Key={'book_id': 0, 'board_id': 0},
                                UpdateExpression="set info.latest_book_id = info.latest_book_id + :val",
                                ExpressionAttributeValues={':val': decimal.Decimal(1)},
                                ReturnValues="UPDATED_NEW")
        return int(res['Attributes']['info']['latest_book_id'])

    def store(self):
        table = self.__get_table()
        book_id = self.__get_id()
        print 'Persisting book_id %d' % book_id

        n_turn = 0
        for a_book in self.lines:
            table.put_item(Item={'book_id': book_id, 'board_id': n_turn, 'info': a_book})
            n_turn += 1
        # set meta to board_id -1
        table.put_item(Item={'book_id': book_id, 'board_id': -1, 'info': self.meta})
        print 'Done persisting.'

    def add_meta(self, meta_dict):
        self.meta.update(meta_dict)

GameRecorder.register(DynamoDBRecorder)
