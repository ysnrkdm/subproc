from ConfigParser import SafeConfigParser


def config_by_filename(filename):
    parser = SafeConfigParser()
    parser.read(filename)
    ret = {
        # [redis]
        'redis_hostname': parser.get('redis', 'hostname'),
        'redis_port': parser.get('redis', 'port'),
        'redis_password': parser.get('redis', 'password'),
        'redis_db_book': parser.getint('redis', 'book_db'),
        'redis_db_param': parser.getint('redis', 'param_db'),
        'redis_book_dbkeyprefix': parser.get('redis', 'book_dbkeyprefix'),
        # [proc]
        'proc_a_path': parser.get('proc', 'a_path'),
        'proc_b_path': parser.get('proc', 'b_path'),
        #[paramgen]
        'paramgen_output_path': parser.get('paramgen', 'output_path'),
        #[learn]
        'learn_from': parser.get('learn', 'from'),
        'learn_class': parser.get('learn', 'class'),
        'learn_epic_batch_size': parser.getint('learn', 'epic_batch_size'),
        #[game_reader]
        'game_reader_from': parser.get('game_reader', 'from'),
        'game_reader_class': parser.get('game_reader', 'class'),
        #[game_recorder]
        'game_recorder_from': parser.get('game_recorder', 'from'),
        'game_recorder_class': parser.get('game_recorder', 'class'),
    }
    return ret


def redis_hostname_port_from_config(config):
    return '%s:%s' % (config['redis_hostname'], config['redis_port'])
