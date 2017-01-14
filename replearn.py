import time
from pyres import ResQ
from eljem_task import ElJemTask
import config
import sys


def get_instance_from_config(conf, section):
    mod = __import__(conf[section + '_from'], fromlist=[conf[section + '_class']])
    class_def = getattr(mod, conf[section + '_class'])
    obj = class_def()
    return obj


def get_learn(conf):
    l = get_instance_from_config(conf, 'learn')
    l.configure(conf)
    return l


def get_game_reader(conf):
    r = get_instance_from_config(conf, 'game_reader')
    r.configure('', '', conf)
    return r


def learn_books(conf, book_ids):
    reader = get_game_reader(conf)

    print 'will process %s' % (str(book_ids))

    books = []
    for i in book_ids:
        meta, a_book = reader.load_by_id(i)
        if len(a_book) > 0:
            a_book_sorted = sorted(a_book, key=lambda x: int(x['turn']))
            a_book_reversed = list(reversed(a_book_sorted))
            if a_book_reversed[0]['end']:
                books.append((i, a_book_reversed, meta))

    learn = get_learn(conf)
    learn.store_batch_stats(books)
    learn.learn_and_update_batch(books)

    enqueue_job(conf, len(books))


def get_books_to_process(conf, from_id):
    retry_counter = conf['replearn_latest_book_id_continue_to_find']
    reader = get_game_reader(conf)
    current_id = from_id
    ret = []
    id_exists = len(reader.load_by_id(current_id)[1]) > 0
    print 'id %d %s' % (current_id, ('found' if id_exists else 'not found'))
    if id_exists:
        ret.append(current_id)
    while retry_counter > 0:
        current_id += 1
        id_exists = len(reader.load_by_id(current_id)[1]) > 0
        if id_exists:
            ret.append(current_id)
        else:
            retry_counter -= 1
        print 'id %d %s' % (current_id, ('found' if id_exists else 'not found'))
        if current_id - from_id > conf['learn_max_batch_size_per_epic']:
            print 'more than %d found. start learning the batch' % (current_id - from_id)
            break

    return current_id, ret


def get_num_working_processes(conf):
    reader = get_game_reader(conf)
    return reader.num_working_processes()


def enqueue_job(conf, nth=1):
    print 'Enqueue-ing %d runs' % nth
    for i in range(nth):
        r = ResQ(server=config.redis_hostname_port_from_config(conf), password=conf['redis_password'])
        a = get_learn(conf)
        params = a.read_parameters()
        r.enqueue(ElJemTask, (conf, params))
        print r.info()
        time.sleep(conf['replearn_enqueue_buffer_interval_secs'])


def main(config_filename):
    conf = config.config_by_filename(config_filename)
    print 'Will use %s' % get_learn(conf).name()
    epic_batch_size = conf['learn_epic_batch_size']
    print 'Batch size per epic is %d' % epic_batch_size

    while True:
        learn = get_learn(conf)
        last = learn.last_processed()

        print 'last processed: %d' % last

        from_id = max(last + 1, 1)

        most_book_id, book_ids = get_books_to_process(conf, from_id)

        print 'greatest book id found is %d' % most_book_id

        to_id = max(from_id, most_book_id)

        if epic_batch_size <= len(book_ids):
            learn_books(conf, book_ids)
        else:
            print 'Not enough data to process: from_id[%d] and to_id[%d]' % (from_id, to_id)
            # Re-enqueue
            r = ResQ(server=config.redis_hostname_port_from_config(conf), password=conf['redis_password'])
            n_inqueue = get_num_working_processes(conf)
            n_pending = r.info()['pending']
            n_enqueued = epic_batch_size - len(book_ids) - n_inqueue - n_pending
            print 'buffered %d matches, and %d in queue, %d pending jobs, will add %d jobs' %\
                  (len(book_ids), n_inqueue, n_pending, n_enqueued)
            enqueue_job(conf, n_enqueued)

        time.sleep(conf['replearn_iteration_interval_secs'])


if __name__ == '__main__':
    filename = sys.argv[1]
    main(filename)
