from ConfigParser import SafeConfigParser


def config_by_filename(filename):
    parser = SafeConfigParser()
    parser.read(filename)
    ret = {
        'redis_hostname': parser.get('redis', 'hostname'),
        'redis_port': parser.get('redis', 'port'),
        'redis_password': parser.get('redis', 'password'),
        'redis_db_book': parser.getint('redis', 'book_db'),
        'redis_db_param': parser.getint('redis', 'param_db'),
        'proc_a_path': parser.get('proc', 'a_path'),
        'proc_b_path': parser.get('proc', 'b_path')
    }
    return ret


def redis_hostname_port_from_config(config):
    return '%s:%s' % (config['redis_hostname'], config['redis_port'])
