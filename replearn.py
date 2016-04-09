import game_reader
import time
from simple_learn import SimpleLearn
from pyres import ResQ
from eljem_task import ElJemTask


MAX_BATCH_SIZE_PER_EPIC = 50

SECONDS = 15

EPIC_BATCH_SIZE = 10


def learn_books(from_id, to_id):
    reader = get_reader()
    learn = SimpleLearn()

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

    enqueue_job(len(books))


def get_most_book_id(from_id):
    reader = get_reader()
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


def get_reader():
    r = game_reader.RedisReader()
    r.configure('', '', {
        'host': 'localhost',
        'port': 6379,
        'db': 0,
        'dbkeyprefix': 'othellobook',
    })
    return r


def enqueue_job(nth=1):
    for i in range(nth):
        r = ResQ(server="localhost:6379")
        a = SimpleLearn()
        params = a.read_parameters()
        r.enqueue(ElJemTask, params)
        print r.info()


def main():

    while True:
        learn = SimpleLearn()
        last = learn.last_processed()

        print 'last processed: %d' % last

        from_id = last + 1

        if from_id == 0:
            from_id = 1

        most_book_id = get_most_book_id(from_id)

        print 'most book size is %d' % most_book_id

        to_id = max(from_id, most_book_id)

        if from_id + EPIC_BATCH_SIZE <= to_id:
            learn_books(from_id, to_id)
        else:
            print 'Not enough data to process: from_id[%d] and to_id[%d]' % (from_id, to_id)
            # Re-enqueue
            r = ResQ(server="localhost:6379")
            n_inqueue = r.info()['queues']
            n_pending = r.info()['pending']
            n_enqueued = EPIC_BATCH_SIZE - (to_id - from_id) - n_inqueue - n_pending
            print 'buffered %d matches, and %d in queue, %d pending jobs, will add %d jobs' % ((to_id - 1 - from_id + 1), n_inqueue, n_pending, n_enqueued)
            enqueue_job(n_enqueued)


        time.sleep(SECONDS)


if __name__ == '__main__':
    main()
