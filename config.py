from ConfigParser import SafeConfigParser


def config_by_filename(filename):
    parser = SafeConfigParser()
    parser.read(filename)
    ret = dict()
    for section in parser.sections():
        for key, value in parser.items(section):
            rvalue = value
            try:
                rvalue = int(value)
            except:
                pass
            ret[section + '_' + key] = rvalue
    return ret


def redis_hostname_port_from_config(config):
    return '%s:%s' % (config['redis_hostname'], config['redis_port'])
