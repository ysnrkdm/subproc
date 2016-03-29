import board
import random
import math
import slack
from learn_base import LearnBasePlus


def mask_count(book, side, mask):
    ret = 0
    for i in range(0, 64):
        if (mask >> i) & 1 > 0:
            if book['book'][63 - i] == side:
                ret += 1
    return ret


class SimpleLearnPhased(LearnBasePlus):
    def __init__(self):
        self.a = 0.03
        self.b = 0.003           # learning rate
        self.l = 0.90            # turn decay in TD-lambda

    def name(self):
        return 'simplelearn'

    def update_state_map(self, a_book, side, turn_left, value):
        r_param = self._redis_param()
        key = self.key_for_param(['param', 'state', self.__hash_from_book(a_book, side)])
        if not r_param.exists(key):
            r_param.set(key, 0)

        current_value = float(r_param.get(key))
        new_value = float(value) * (self.l ** turn_left)
        if current_value == 0:
            r_param.set(key, new_value)
        else:
            r_param.set(key, current_value * (1-self.a) + new_value * self.a)
        return current_value, r_param.get(key)

    def __hash_from_book(self, a_book, side):
        (a, b, c, d, e, f, g, h) = self.__counts(a_book, side)
        return ':'.join([str(a), str(b), str(c), str(d), str(e), str(f), str(g), str(h)])

    def __state_from_hash(self, state):
        a = state.split(':')
        return int(a[4]), int(a[5]), int(a[6]), int(a[7]), int(a[8]), int(a[9]), int(a[10]), int(a[11])

    def __random_sample(self, num):
        r_param = self._redis_param()
        key = self.key_for_param(['param', 'state', '*'])
        print key
        states = r_param.keys(key)
        len(states)
        ret = set()
        for i in range(num):
            key_rand = random.choice(states)
            ret.add((self.__state_from_hash(key_rand), r_param.get(key_rand)))

        return list(ret)

    # def store_batch_stats(self, books):
    #     black_wins = 0
    #     white_wins = 0
    #     disc_diff = []
    #     book_ids = []
    #
    #     for book_id, book in books:
    #         last_book = book[0]
    #         last_board = board.Board()
    #         last_board.deserialize(last_book['book'], last_book['whosturn'], last_book['turn'])
    #         black_discs = last_board.n_black()
    #         white_discs = last_board.n_white()
    #         disc_diff.append(black_discs - white_discs)
    #         if black_discs > white_discs:
    #             black_wins += 1
    #         elif white_discs > black_wins:
    #             white_wins += 1
    #         else:
    #             pass
    #         book_ids.append(book_id)
    #
    #     black_win_rate = float(black_wins) / float(len(books))
    #     white_win_rate = float(white_wins) / float(len(books))
    #     min_disc_diff = min(disc_diff)
    #     max_disc_diff = max(disc_diff)
    #     avg_disc_diff = float(sum(disc_diff)) / float(len(books))
    #     book_id_from = min(book_ids)
    #     book_id_to = max(book_ids)
    #
    #     key_for_update_stats = self.key_for_param(['stats', str(book_id_from), str(book_id_to)])
    #     r_param = self.redis_param()
    #     payload = {
    #         'black_win_rate': black_win_rate,
    #         'white_win_rate': white_win_rate,
    #         'min_disc_diff': min_disc_diff,
    #         'max_disc_diff': max_disc_diff,
    #         'avg_disc_diff': avg_disc_diff
    #     }
    #     r_param.hmset(key_for_update_stats,payload)
    #
    #     slack.post_message(
    #         ('Done matches, from %d to %d' % (book_id_from, book_id_to)) + '\n' +
    #         ('win rate: black/white = %.4f/%.4f' % (black_win_rate * 100.0, white_win_rate * 100.0)) + '\n' +
    #         ('disc diff: min/avg/max = %d/%.2f/%d' % (min_disc_diff, avg_disc_diff, max_disc_diff)) + '\n' +
    #         'disc diffs: %s' % str(disc_diff))

    def learn_and_update_batch(self, books):
        err = 0
        new_param = 0
        for book_id, book in books:
            err, new_param = self.__learn_and_update_one(book_id, book)

        slack.post_message(
            'Learn complete' + '\n' +
            ('err: %s' % str(err)) + '\n' +
            'new param: %s' % str(new_param))

    def __learn_and_update_one(self, book_id, book):
        print book[0]
        last_turn = int(book[0]['turn'])
        last_board = board.Board()
        last_board.deserialize(book[0]['book'], book[0]['whosturn'], book[0]['turn'])
        value_for_black = last_board.n_black() - last_board.n_white()
        value_for_white = last_board.n_white() - last_board.n_black()

        # update values
        for turn in book:
            for (side, value) in [('O', value_for_black), ('X', value_for_white)]:
                # update state map
                current_value, new_value = self.update_state_map(turn, side, last_turn - int(turn['turn']), value)

        # pick up at most 100 states and fit parameters
        parameters = self.__read_parameters()
        samples = self.__random_sample(500)
        err, new_param = self.__fit_parameters(parameters, samples)
        print 'Learn complete:'
        print err
        print new_param

        # store parameter
        self.__update_parameters(book_id, new_param)

        return err, new_param

    def __fit_parameters(self, parameters, samples):
        err = 99999
        for i in range(10000):
            new_parameters = self.__fit_parameters_once(parameters, samples)
            err = self.__norm(parameters, new_parameters)
            print 'param is %s, err: %f' % (str(new_parameters), err)
            if err < 0.005:
                parameters = new_parameters
                break
            parameters = new_parameters
        return err, parameters

    def __norm(self, a, b):
        ret = 0
        for i in range(len(a)):
            ret += (a[i] - b[i]) ** 2
        return math.sqrt(ret)

    def __fit_parameters_once(self, parameters, samples):
        w = list(parameters)
        new_w = list(parameters)
        for j in range(8):
            q = 0
            for i in samples:
                e_i = float(i[1])
                e_i_d = self.__eval_vector(w, i[0])
                f_j_p_i = i[0][j]
                # print '[%s] e_i %f, e_i_d %f, f_j_p_i %f' % (str(i), e_i, e_i_d, f_j_p_i)
                q += (e_i - e_i_d) * f_j_p_i
            a = self.b / len(samples)
            new_w[j] = w[j] + 2 * a * q
            print 'q is %f' % q
            print 'Updated %d %f -> %f' % (j, w[j], new_w[j])
        return tuple(new_w)

    def __eval_vector(self, parameters, features):
        ret = 0
        for i in range(len(parameters)):
            ret += parameters[i] * features[i]
        return ret

    def __counts(self, a_book, side):
        a = mask_count(a_book, side, 0x8100000000000081)
        b = mask_count(a_book, side, 0x4281000000008142)
        c = mask_count(a_book, side, 0x0042000000004200)
        d = mask_count(a_book, side, 0x2400810000810024)
        e = mask_count(a_book, side, 0x1800008181000018)
        f = mask_count(a_book, side, 0x003C424242423C00)
        g = mask_count(a_book, side, 0x0000240000240000)
        h = mask_count(a_book, side, 0x0000183C3C180000)
        return a, b, c, d, e, f, g, h

    def __eval(self, a_book, side, parameters):
        (a, b, c, d, e, f, g, h) = self.__counts(a_book, side)
        (ca, cb, cc, cd, ce, cf, cg, ch) = parameters
        return a * ca + b * cb + c * cc + d * cd + e * ce + f * cf + g * cg + h * ch

    def last_processed(self):
        r_param = self._redis_param()
        key_last_processed = self.key_for_param(['last_processed'])
        if not r_param.exists(key_last_processed):
            r_param.set(key_last_processed, -1)

        return int(r_param.get(key_last_processed))

    def __update_parameters(self, id_processed, parameters):
        (a, b, c, d, e, f, g, h) = parameters
        # update param to db
        r_param = self._redis_param()
        key = self.key_for_param(['param'])
        r_param.hset(key, 'a', int(a))
        r_param.hset(key, 'b', int(b))
        r_param.hset(key, 'c', int(c))
        r_param.hset(key, 'd', int(d))
        r_param.hset(key, 'e', int(e))
        r_param.hset(key, 'f', int(f))
        r_param.hset(key, 'g', int(g))
        r_param.hset(key, 'h', int(h))
        # update last processed id
        key_last_processed = self.key_for_param(['last_processed'])
        r_param.set(key_last_processed, id_processed)

    def __read_parameters(self):
        r_param = self._redis_param()
        key = self.key_for_param(['param'])
        if not r_param.exists(key):
            (a, b, c, d, e, f, g, h) = (99, 2,  -5,  7,  6,  4,  5, 5)
            r_param.hset(key, 'a', a)
            r_param.hset(key, 'b', b)
            r_param.hset(key, 'c', c)
            r_param.hset(key, 'd', d)
            r_param.hset(key, 'e', e)
            r_param.hset(key, 'f', f)
            r_param.hset(key, 'g', g)
            r_param.hset(key, 'h', h)
        (a, b, c, d, e, f, g, h) = r_param.hmget(key, 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h')
        return int(a), int(b), int(c), int(d), int(e), int(f), int(g), int(h)