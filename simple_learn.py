import board
import random
import math
import slack
from learn_base import LearnBasePlus
import numpy as np
from sklearn.utils import resample
from sklearn import linear_model
from math import sqrt


def mask_count(book, side, mask):
    ret = 0
    for i in range(0, 64):
        if (mask >> i) & 1 > 0:
            if book['book'][63 - i] == side:
                ret += 1
    return ret


class SimpleLearn(LearnBasePlus):
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

    def random_sample(self, num):
        r_param = self._redis_param()
        key = self.key_for_param(['param', 'state', '*'])
        print key
        states = r_param.keys(key)
        len(states)
        ret = set()
        for i in range(num):
            key_rand = random.choice(states)
            ret.add((self.__state_from_hash(key_rand), float(r_param.get(key_rand))))

        y = []
        x = []
        for state, value in list(ret):
            y.append(value)
            x.append(list(state))

        return x,y

    def learn_and_update_batch(self, books):
        last_book_id = -1
        for book_id, book, _ in books:
            last_book_id = self.__update_state_by_book(book_id, book)

        # learn batch
        mse, var, new_param = self.__learn_batch(last_book_id)

        slack.post_message(
            'Learn complete' + '\n' +
            ('mse: %s' % str(mse)) + '\n' +
            ('var: %s' % str(var)) + '\n' +
            'new param: %s' % str(map(lambda x: '%.3f' % x, new_param)))

    def __learn_batch(self, book_id):
        # pick up at most 100 states and fit parameters

        mse, var, new_param = self.__fit_parameters()

        print 'Learn complete:'
        print mse
        print var
        print new_param

        # store parameter
        self.__update_parameters(book_id, new_param)

        return mse, var, new_param

    def __update_state_by_book(self, book_id, book):
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
                _, _ = self.update_state_map(turn, side, last_turn - int(turn['turn']), value)
        return book_id

    def __fit_parameters(self):
        sampled_x, sampled_y = self.random_sample(50000)
        x = np.array(sampled_x)
        y = np.array(sampled_y)

        num = len(y)
        x, y = resample(x, y, n_samples=num)

        lr = linear_model.LinearRegression(fit_intercept=True)

        lr.fit(x, y)
        # lr.coef_
        # lr.intercept_

        # RMSE
        stest_x, stest_y = self.random_sample(50000)
        test_x = np.array(stest_x)
        test_y = np.array(stest_y)
        mse = sqrt(np.mean((lr.predict(test_x) - test_y) ** 2))
        var = lr.score(test_x, test_y)

        return mse, var, tuple([i * 20 for i in lr.coef_])

    def __norm(self, a, b):
        ret = 0
        for i in range(len(a)):
            ret += (a[i] - b[i]) ** 2
        return math.sqrt(ret)

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

    def read_parameters(self):
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