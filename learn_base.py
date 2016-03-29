import redis
import board
import slack
from abc import ABCMeta, abstractmethod

REDIS_KEY_PREFIX = 'othelloparam'


class LearnBase(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def store_batch_stats(self, books):
        pass

    @abstractmethod
    def learn_and_update_batch(self, books):
        pass

    @abstractmethod
    def last_processed(self):
        pass


class LearnBasePlus(LearnBase):
    def key_for_param(self, keys):
        a_keys = [REDIS_KEY_PREFIX, self.name()] + keys
        return ':'.join(a_keys)

    @abstractmethod
    def name(self):
        pass

    def _redis_param(self):
        r_param = redis.Redis(host='localhost', port=6379, db=2)
        return r_param

    def store_batch_stats(self, books):
        black_wins = 0
        white_wins = 0
        disc_diff = []
        book_ids = []

        for book_id, book in books:
            last_book = book[0]
            last_board = board.Board()
            last_board.deserialize(last_book['book'], last_book['whosturn'], last_book['turn'])
            black_discs = last_board.n_black()
            white_discs = last_board.n_white()
            disc_diff.append(black_discs - white_discs)
            if black_discs > white_discs:
                black_wins += 1
            elif white_discs > black_wins:
                white_wins += 1
            else:
                pass
            book_ids.append(book_id)

        black_win_rate = float(black_wins) / float(len(books))
        white_win_rate = float(white_wins) / float(len(books))
        min_disc_diff = min(disc_diff)
        max_disc_diff = max(disc_diff)
        avg_disc_diff = float(sum(disc_diff)) / float(len(books))
        book_id_from = min(book_ids)
        book_id_to = max(book_ids)

        key_for_update_stats = self.key_for_param(['stats', str(book_id_from), str(book_id_to)])
        r_param = self._redis_param()
        payload = {
            'black_win_rate': black_win_rate,
            'white_win_rate': white_win_rate,
            'min_disc_diff': min_disc_diff,
            'max_disc_diff': max_disc_diff,
            'avg_disc_diff': avg_disc_diff
        }
        r_param.hmset(key_for_update_stats, payload)

        slack.post_message(
                ('Done matches, from %d to %d' % (book_id_from, book_id_to)) + '\n' +
                ('win rate: black/white = %.4f/%.4f' % (black_win_rate * 100.0, white_win_rate * 100.0)) + '\n' +
                ('disc diff: min/avg/max = %d/%.2f/%d' % (min_disc_diff, avg_disc_diff, max_disc_diff)) + '\n' +
                'disc diffs: %s' % str(disc_diff))

    @abstractmethod
    def learn_and_update_batch(self, books):
        pass

    @abstractmethod
    def last_processed(self):
        pass
