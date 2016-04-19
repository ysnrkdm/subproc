import board
import random
import math
import slack
from learn_base import LearnBasePlus
import numpy as np
from sklearn.utils import resample
from sklearn import linear_model
from math import sqrt
from itertools import chain


def mask_count(book, side, mask):
    ret = 0
    for i in range(0, 64):
        if (mask >> i) & 1 > 0:
            if book['book'][63 - i] == side:
                ret += 1
    return ret


def count(book):
    ret = 0
    for i in range(0, 64):
        if book['book'][63 - i] != '-':
                ret += 1
    return ret


class ProgressPositionLearn(LearnBasePlus):
    def __init__(self):
        super(ProgressPositionLearn, self).__init__()
        self.a = 0.03
        self.b = 0.003           # learning rate
        self.l = 0.90            # turn decay in TD-lambda

    def name(self):
        return 'progresspositionlearn'

    # State related functions

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
        (p, a, b, c, d, e, f, g, h) = self.__counts(a_book, side)
        return ':'.join([str(p), str(a), str(b), str(c), str(d), str(e), str(f), str(g), str(h)])

    def __state_from_hash(self, state):
        a = state.split(':')
        return int(a[4]), int(a[5]), int(a[6]), int(a[7]), int(a[8]), int(a[9]), int(a[10]), int(a[11]), int(a[12])

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

    def __progress(self, a_book):
        cnt = count(a_book)
        return cnt

    def __counts(self, a_book, side):
        a = mask_count(a_book, side, 0x8100000000000081)
        b = mask_count(a_book, side, 0x4281000000008142)
        c = mask_count(a_book, side, 0x0042000000004200)
        d = mask_count(a_book, side, 0x2400810000810024)
        e = mask_count(a_book, side, 0x1800008181000018)
        f = mask_count(a_book, side, 0x003C424242423C00)
        g = mask_count(a_book, side, 0x0000240000240000)
        h = mask_count(a_book, side, 0x0000183C3C180000)
        return self.__progress(a_book), a, b, c, d, e, f, g, h

    # Learning related functions

    def random_sample(self, num, p_min, p_max):
        r_param = self._redis_param()
        key = self.key_for_param(['param', 'state', '*'])
        print key
        states = r_param.keys(key)
        len(states)
        ret = set()
        for i in range(num):
            key_rand = random.choice(states)
            state = self.__state_from_hash(key_rand)
            progress = state[0]
            value = float(r_param.get(key_rand))
            if p_min <= progress <= p_max:
                ret.add((state, value))

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
            ('Learn complete[%s]' % self.name()) + '\n' +
            ('mse: %s' % str(mse)) + '\n' +
            ('var: %s' % str(var)) + '\n' +
            'new param: %s' % str(map(lambda arr: map(lambda x: '%.3f' % x, arr), new_param)))

    def __learn_batch(self, book_id):
        # pick up at most 100 states and fit parameters
        mse, var, new_param = self.__fit_parameters()

        # store parameter
        self.__update_parameters(book_id, new_param)

        return mse, var, new_param

    def __fit_parameters(self):
        mses = []
        vars = []
        params = []
        for (p_min, p_max) in [(0, 16), (17, 32), (33, 48), (49, 64)]:
            sampled_x, sampled_y = self.random_sample(50000, p_min, p_max)
            x = np.array(sampled_x)
            y = np.array(sampled_y)

            num = len(y)
            x, y = resample(x, y, n_samples=num)

            lr = linear_model.LinearRegression(fit_intercept=True)

            lr.fit(x, y)

            # RMSE
            stest_x, stest_y = self.random_sample(50000, p_min, p_max)
            test_x = np.array(stest_x)
            test_y = np.array(stest_y)
            mse = sqrt(np.mean((lr.predict(test_x) - test_y) ** 2))
            var = lr.score(test_x, test_y)
            mses.append(mse)
            vars.append(var)
            params.append(tuple([i * 20 for i in lr.coef_]))

        return mses, vars, params

    # db related functions

    def last_processed(self):
        r_param = self._redis_param()
        key_last_processed = self.key_for_param(['last_processed'])
        if not r_param.exists(key_last_processed):
            r_param.set(key_last_processed, -1)

        return int(r_param.get(key_last_processed))

    def store_parameters(self, parameters_in):
        start = ord('A')
        parameters = list(chain.from_iterable(parameters_in))
        r_param = self._redis_param()
        key = self.key_for_param(['param'])
        iparameters = map(lambda x: int(x), parameters)
        for par in iparameters:
            r_param.hset(key, chr(start), par)
            start += 1

    def __update_parameters(self, id_processed, parameters):
        self.store_parameters(parameters)

        r_param = self._redis_param()
        key_last_processed = self.key_for_param(['last_processed'])
        r_param.set(key_last_processed, id_processed)

    def read_parameters(self):
        r_param = self._redis_param()
        key = self.key_for_param(['param'])
        if not r_param.exists(key):
            self.store_parameters([
                [99, -1, -1, -1, -1, 3, 8, 20],
                [99, 2,  -5,  7,  6,  4,  5, 5],
                [99, 2,  -5,  -7,  -6,  4,  5, 5],
                [100, 50, 30, 30, 30, 30, 30, 30]
            ])
        start = ord('A')
        ret = [1]
        for i in range(8*4):
            ret.append(int(r_param.hget(key, chr(start + i))))

        return tuple(ret)