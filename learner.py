# SimpleLearn
import game_reader
from simple_learn import SimpleLearn


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


def get_most_book_id(from_id):
    reader = get_reader()
    current_id = from_id
    id_exists = len(reader.load_by_id(current_id)) > 0
    while id_exists:
        print '.'
        current_id += 1
        id_exists = len(reader.load_by_id(current_id)) > 0
        if current_id - from_id > 50:
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


def main():
    learn = SimpleLearn()
    last = learn.last_processed()

    print 'last processed: %d' % last

    from_id = last + 1

    if from_id == 0:
        from_id = 1

    most_book_id = get_most_book_id(from_id)

    to_id = max(from_id, most_book_id)

    if from_id + 10 <= to_id:
        learn_books(from_id, to_id)
    else:
        print 'Not enough data to process: from_id[%d] and to_id[%d]' % (from_id, to_id)


if __name__ == '__main__':
    main()
