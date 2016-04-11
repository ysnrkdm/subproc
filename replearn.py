import game_reader
import time
from simple_learn import SimpleLearn
from pyres import ResQ
from eljem_task import ElJemTask
import config
import sys


MAX_BATCH_SIZE_PER_EPIC = 100

SECONDS = 15

EPIC_BATCH_SIZE = 50


def learn_books(conf, from_id, to_id):
    reader = get_reader(conf)
    learn = SimpleLearn()
    learn.configure(conf)

    will_process = range(from_id, to_id)
    print 'will process %s' % (str(will_process))

    books = []
    for i in will_process:
        meta, a_book = reader.load_by_id(i)
        if len(a_book) > 0:
            a_book_sorted = sorted(a_book, key=lambda x: int(x['turn']))
            a_book_reversed = list(reversed(a_book_sorted))
            books.append((i, a_book_reversed, meta))

    learn.store_batch_stats(books)
    learn.learn_and_update_batch(books)

    enqueue_job(conf, len(books))


def get_most_book_id(conf, from_id):
    reader = get_reader(conf)
    current_id = from_id
    id_exists = len(reader.load_by_id(current_id)[1]) > 0
    print 'id %d %s' % (current_id, ('found' if id_exists else 'not found'))
    while id_exists:
        current_id += 1
        id_exists = len(reader.load_by_id(current_id)[1]) > 0
        print 'id %d %s' % (current_id, ('found' if id_exists else 'not found'))
        if current_id - from_id > MAX_BATCH_SIZE_PER_EPIC:
            print 'more than %d found. going back to learn' % (current_id - from_id)
            break

    return current_id


def get_reader(conf):
    r = game_reader.RedisReader()
    r.configure('', '', {
        'host': conf['redis_hostname'],
        'port': conf['redis_port'],
        'db': conf['redis_db_book'],
        'password': conf['redis_password'],
        'dbkeyprefix': 'othellobook',
    })
    return r


def enqueue_job(conf, nth=1):
    for i in range(nth):
        r = ResQ(server=config.redis_hostname_port_from_config(conf), password=conf['redis_password'])
        a = SimpleLearn()
        a.configure(conf)
        params = a.read_parameters()
        r.enqueue(ElJemTask, (conf,params))
        print r.info()


def main(config_filename):
    conf = config.config_by_filename(config_filename)

    while True:
        learn = SimpleLearn()
        learn.configure(conf)
        last = learn.last_processed()

        print 'last processed: %d' % last

        from_id = last + 1

        if from_id == 0:
            from_id = 1

        most_book_id = get_most_book_id(conf, from_id)

        print 'most book size is %d' % most_book_id

        to_id = max(from_id, most_book_id)

        if from_id + EPIC_BATCH_SIZE <= to_id:
            learn_books(conf, from_id, to_id)
        else:
            print 'Not enough data to process: from_id[%d] and to_id[%d]' % (from_id, to_id)
            # Re-enqueue
            r = ResQ(server=config.redis_hostname_port_from_config(conf), password=conf['redis_password'])
            n_inqueue = r.info()['queues']
            n_pending = r.info()['pending']
            n_enqueued = EPIC_BATCH_SIZE - (to_id - from_id) - n_inqueue - n_pending
            print 'buffered %d matches, and %d in queue, %d pending jobs, will add %d jobs' % ((to_id - 1 - from_id + 1), n_inqueue, n_pending, n_enqueued)
            enqueue_job(conf, n_enqueued)

        time.sleep(SECONDS)


if __name__ == '__main__':
    filename = sys.argv[1]
    main(filename)
