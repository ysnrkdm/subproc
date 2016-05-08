from abc import ABCMeta, abstractmethod
from datetime import datetime
import redis
import boto3
from boto3.dynamodb.conditions import Key


class GameReader(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def configure(self, title, meta, config_dict):
        pass

    @abstractmethod
    def load_by_id(self, book_id):
        pass


class RedisReader(GameReader):

    def __init__(self):
        self.r = None
        self.lines = []
        self.book_db_key_prefix = 'DEFAULT'
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def configure(self, title, meta, config_dict):
        self.r = redis.Redis(host=config_dict['redis_hostname'], port=config_dict['redis_port'],
                             db=config_dict['redis_db_book'], password=config_dict['redis_password'])
        self.book_db_key_prefix = config_dict['redis_book_dbkeyprefix']

    def __list_by_id(self, book_id):
        # print book_id
        wildcard_key = ':'.join([self.book_db_key_prefix, str(book_id), '*'])
        # print '\n' + wildcard_key + '\n'
        ret = self.r.keys(wildcard_key)
        return ret

    def __list_all(self):
        entry_key = ':'.join([self.book_db_key_prefix, '*'])
        list_from_db = self.r.keys(entry_key)
        return list_from_db

    def load_by_id(self, book_id):
        entry_keys_to_process = self.__list_by_id(book_id)
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

    def __load_all(self):
        ids = self.__list_all()
        ret = {}
        for book_id in ids:
            list_book = self.load_by_id(book_id)
            ret[str(book_id)] = list_book
        return ret

GameReader.register(RedisReader)


class DynamoDBReader(GameReader):

    def __init__(self):
        self.client = None
        self.resource = None
        self.table_name = 'DEFAULT_TABLE_NAME'
        pass

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

    def __get_table(self):
        if not unicode(self.table_name) in self.client.list_tables()['TableNames']:
            print 'Book table doesn\'t exist. creating...'
            self.resource.create_table(TableName=self.table_name,
                                       KeySchema=[
                                           {'AttributeName': 'book_id', 'KeyType': 'HASH'},
                                           {'AttributeName': 'board_id', 'KeyType': 'RANGE'}],
                                       AttributeDefinitions=[
                                           {'AttributeName': 'book_id', 'AttributeType': 'N'},
                                           {'AttributeName': 'board_id', 'AttributeType': 'N'}],
                                       ProvisionedThroughput={
                                           'ReadCapacityUnits': 10,
                                           'WriteCapacityUnits': 10})

        table = self.resource.Table(self.table_name)
        return table

    def load_by_id(self, book_id):
        table = self.__get_table()
        res = table.query(KeyConditionExpression=Key('book_id').eq(book_id))
        ret = []
        meta = {}
        for item in res['Items']:
            info = item['info']
            if 'meta' in info.keys():
                meta = info
            else:
                obj = {
                    'book': info['book'],
                    'whosturn': info['whosturn'],
                    'turn': int(info['turn']),
                    'end': info['end'],
                    'timestamp': info['timestamp']
                }
                ret.append(obj)
        return meta, ret

