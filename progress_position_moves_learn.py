import random
import slack
from learn_base import LearnBasePlus
import numpy as np
from sklearn.utils import resample
from sklearn import linear_model
from math import sqrt
from itertools import chain
from parameter_progress_position_moves_learn import ProgressPositionMovesParameter
from parameter import board_from_a_book


class ProgressPositionMovesLearn(LearnBasePlus):
    def __init__(self):
        super(ProgressPositionMovesLearn, self).__init__()
        self.a = 0.03
        self.b = 0.003           # learning rate
        self.l = 0.90            # turn decay in TD-lambda
        self.parameter = ProgressPositionMovesParameter()

    def name(self):
        return 'progresspositionmovelearn'

    # State related functions

    def __update_state_for_a_book(self, book_id, book):
        print book[0]       # terminal book
        last_turn = int(book[0]['turn'])
        last_board = board_from_a_book(book[0])
        value_for_black = last_board.n_black() - last_board.n_white()
        value_for_white = last_board.n_white() - last_board.n_black()
        # update values
        for a_book in book:
            for (side, value) in [('O', value_for_black), ('X', value_for_white)]:
                # update state map
                _, _ = self.__update_state_map(a_book, side, last_turn - int(a_book['turn']), value)
        return book_id

    def __update_state_map(self, a_book, side, turn_left, value):
        r_param = self._param_store()
        key = ['param', 'state', self.parameter.hash_from_book(a_book, side)]
        if not r_param.exists(key):
            r_param.set(key, 0)

        current_value = float(r_param.get(key))
        new_value = float(value) * (self.l ** turn_left)
        if current_value == 0:
            r_param.set(key, new_value)
        else:
            r_param.set(key, current_value * (1-self.a) + new_value * self.a)
        return current_value, r_param.get(key)

    # Learning related functions

    def __random_sample(self, num, p_min, p_max):
        r_param = self._param_store()
        states = r_param.keys(['param', 'state', '*'])
        ret = set()
        for num_try in range(5):
            for i in range(num):
                key_rand = random.choice(states)
                progress = self.parameter.phase_from_hash(key_rand)
                value = float(r_param.get(key_rand))
                if p_min <= progress <= p_max:
                    ret.add((self.parameter.features_from_hash(key_rand), value))
            if len(ret) >= num:
                break

        y = []
        x = []
        for state, value in list(ret):
            y.append(value)
            x.append(list(state))

        return x, y

    def learn_and_update_batch(self, books):
        last_book_id = -1
        for book_id, book, _ in books:
            last_book_id = self.__update_state_for_a_book(book_id, book)

        # learn batch
        mse, var, new_param, nsamples = self.__learn_batch(last_book_id)

        slack.post_message(
            ('Learn complete[%s]' % self.name()) + '\n' +
            ('mse: %s' % str(mse)) + '\n' +
            ('var: %s' % str(var)) + '\n' +
            ('used samples: %s' % str(nsamples)) + '\n' +
            'new param: %s' % str(map(lambda arr: map(lambda x: '%.3f' % x, arr), new_param)))

    def __learn_batch(self, book_id):
        # pick up at most 100 states and fit parameters
        mse, var, new_param, nsamples = self.__fit_parameters()

        # store parameter
        self.__update_parameters(book_id, new_param)

        return mse, var, new_param, nsamples

    def __fit_parameters(self):
        mses = []
        scores = []
        params = []
        nsamples = []
        for (phase_from, phase_to) in [(0, 16), (17, 32), (33, 48), (49, 64)]:
            mse, score, param, nsample = self.__fit_parameter(phase_from, phase_to)
            mses.append(mse)
            scores.append(score)
            params.append(param)
            nsamples.append(nsample)

        print 'params learned:'
        print params

        return mses, scores, params, nsamples

    def __fit_parameter(self, phase_from, phase_to):
        sampled_x, sampled_y = self.__random_sample(50000, phase_from, phase_to)
        x = np.array(sampled_x)
        y = np.array(sampled_y)

        num = len(y)
        x, y = resample(x, y, n_samples=num)

        lr = linear_model.LinearRegression(fit_intercept=True)

        lr.fit(x, y)

        # RMSE
        stest_x, stest_y = self.__random_sample(50000, phase_from, phase_to)
        test_x = np.array(stest_x)
        test_y = np.array(stest_y)
        mse = sqrt(np.mean((lr.predict(test_x) - test_y) ** 2))
        score = lr.score(test_x, test_y)
        coef = 127/max(map(lambda q: abs(q), lr.coef_))
        param = tuple([i*coef for i in lr.coef_])
        nsample = len(sampled_x)

        return mse, score, param, nsample

    # db related functions

    def last_processed(self):
        r_param = self._param_store()
        key_last_processed = ['last_processed']
        if not r_param.exists(key_last_processed):
            r_param.set(key_last_processed, -1)

        return int(r_param.get(key_last_processed))

    def __store_parameters(self, parameters_in):
        start = ord('A')
        parameters = list(chain.from_iterable(parameters_in))
        r_param = self._param_store()
        iparameters = map(lambda x: int(x), parameters)
        for par in iparameters:
            r_param.hset(['param'], chr(start), par)
            start += 1

    def __update_parameters(self, id_processed, parameters):
        self.__store_parameters(parameters)

        r_param = self._param_store()
        r_param.set(['last_processed'], id_processed)

    def read_parameters(self):
        r_param = self._param_store()
        key = ['param']
        if not r_param.exists(key):
            self.__store_parameters(self.parameter.default_value())
        start = ord('A')
        ret = [self.parameter.header()]
        for i in range(len(list(chain.from_iterable(self.parameter.default_value())))):
            ret.append(int(r_param.hget(key, chr(start + i))))

        print 'read parameter %s' % str(tuple(ret))
        print '%d elements' % len(ret)

        return tuple(ret)
