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
    def configure(self, conf_dict):
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

    @abstractmethod
    def read_parameters(self):
        pass


class LearnBasePlus(LearnBase):
    def __init__(self):
        self.conf = {}

    def key_for_param(self, keys):
        a_keys = [REDIS_KEY_PREFIX, self.name()] + keys
        return ':'.join(a_keys)

    @abstractmethod
    def name(self):
        pass

    def configure(self, conf_dict):
        self.conf = conf_dict

    def _redis_param(self):
        r_param = redis.Redis(host=self.conf['redis_hostname'], port=self.conf['redis_port'],
                              db=self.conf['redis_db_param'], password=self.conf['redis_password'])
        return r_param

    def store_batch_stats(self, books):
        black_wins = 0
        white_wins = 0
        disc_diff = []
        book_ids = []
        black_name = 'black'
        white_name = 'white'
        params = set()

        for book_id, book, meta in books:
            try:
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
                black_name = meta['proc_a']
                white_name = meta['prob_b']
                params.add(meta['hamletparam'])
            except:
                import traceback
                print 'Exception occured while processing %d th book' % book_id
                traceback.print_exc()

        black_win_rate = float(black_wins) / float(len(books))
        white_win_rate = float(white_wins) / float(len(books))
        min_disc_diff = min(disc_diff)
        max_disc_diff = max(disc_diff)
        avg_disc_diff = float(sum(disc_diff)) / float(len(books))
        book_id_from = min(book_ids)
        book_id_to = max(book_ids)

        params_used = ' / '.join(params)

        key_for_update_stats = self.key_for_param(['stats', str(book_id_from), str(book_id_to)])
        r_param = self._redis_param()
        payload = {
            black_name + '_win_rate': black_win_rate,
            white_name + '_win_rate': white_win_rate,
            'min_disc_diff': min_disc_diff,
            'max_disc_diff': max_disc_diff,
            'avg_disc_diff': avg_disc_diff,
            'params_used': params_used,
            'diffs': sorted(disc_diff)
        }
        r_param.hmset(key_for_update_stats, payload)

        slack.post_message(
                ('Done matches [%s], from %d to %d' % (self.name(), book_id_from, book_id_to)) + '\n' +
                ('win rate: %s/%s = %.4f/%.4f' %
                 (black_name, white_name, black_win_rate * 100.0, white_win_rate * 100.0)) + '\n' +
                ('disc diff: min/avg/max = %d/%.2f/%d' % (min_disc_diff, avg_disc_diff, max_disc_diff)) + '\n' +
                ('disc diffs: %s' % str(disc_diff)) + '\n' +
                ('params used: %s' % params_used))

        self.__show_stats()

    def __show_stats(self):
        r_param = self._redis_param()
        key_for_update_stats = self.key_for_param(['stats', '*'])

        ret = []
        for k in r_param.keys(key_for_update_stats):
            if 'params_used' in r_param.hgetall(k):
                ret.append(r_param.hgetall(k))

        sorted_list = sorted(ret, key=lambda x: float(x['Edax_win_rate']))
        ranking_list = list(sorted_list)
        if len(ranking_list) < 4:
            ranking_list.append({'empty': 'empty'})
            ranking_list.append({'empty': 'empty'})
            ranking_list.append({'empty': 'empty'})
            ranking_list.append({'empty': 'empty'})
        slack.post_message(
                ('Ranking of %s: ' % self.name()) + '\n' +
                ('1st: %s' % str(ranking_list[0])) + '\n' +
                ('2nd: %s' % str(ranking_list[1])) + '\n' +
                ('3rd: %s' % str(ranking_list[2])))

    @abstractmethod
    def learn_and_update_batch(self, books):
        pass

    @abstractmethod
    def last_processed(self):
        pass

    @abstractmethod
    def read_parameters(self):
        pass