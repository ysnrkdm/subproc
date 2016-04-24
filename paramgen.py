import config
import sys


def conv_num(num):
    if num < 0:
        return 256 + num
    else:
        return num


def write_data(file_full_path, parameters):
    norm_params = map(conv_num, parameters)

    print 'writing to %s' % file_full_path
    with open(file_full_path, "wb") as fout:
        bary = bytearray(norm_params)
        bary.append(0)
        fout.write(bary)


def get_learn(conf):
    mod = __import__(conf['learn_from'], fromlist=[conf['learn_class']])
    class_def = getattr(mod, conf['learn_class'])
    obj = class_def()
    return obj


def fetch_and_paramgen(conf):
    # load parameter
    learn = get_learn(conf)
    print 'type is %s' % type(learn)
    learn.configure(conf)
    params = learn.read_parameters()
    print 'params: %s' % str(params)
    write_data(conf['paramgen_output_path'], params)


def fetch_and_show(conf):
    file_full_path = conf['paramgen_output_path']
    with open(file_full_path, "rb") as fin:
        data = fin.read()
        N = len(data)
        line = ''
        print 'data length: %d' % N
        for i in range(N):
            elem = str(ord(data[i]))
            if i == 0:
                print elem
            elif (i) % ((N-2)/4) == 0 and i != 1:
                line += elem + ', '
                print line
                line = ''
            else:
                line += elem + ', '
        print line


def main(comm, file_full_path):
    conf = config.config_by_filename(file_full_path)
    if comm == 'read':
        fetch_and_show(conf)
    elif comm == 'write':
        fetch_and_paramgen(conf)


if __name__ == '__main__':
    command = sys.argv[1]
    filename = sys.argv[2]
    main(command, filename)
