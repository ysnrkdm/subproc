# SimpleLearn
import game_reader
import simple_learn


def main():
    reader = game_reader.RedisReader()
    reader.configure('', '', {
        'host': 'localhost',
        'port': 6379,
        'db': 0,
        'dbkeyprefix': 'othellobook',
    })

    learn = simple_learn.SimpleLearn()

    last = learn.last_processed()

    print 'last processed: %d'%(last)

    will_process = range(last+1, last + 10)
    print 'will process %s'%(str(will_process))

    for i in will_process:
        a_book = reader.load_by_id(i)
        if len(a_book) > 0:
            a_book_sorted = sorted(a_book, key=lambda x: int(x['turn']))
            a_book_reversed = list(reversed(a_book_sorted))
            learn.learn_and_update(i, a_book_reversed)


if __name__ == '__main__':
    main()
