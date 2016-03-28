import redis
import board
import random
import math


def update_parameters(id_processed, parameters):
    (a, b, c, d, e, f, g, h) = parameters
    # update param to db
    r_param = redis_param()
    key = key_for_param(['param'])
    r_param.hset(key, 'a', int(a))
    r_param.hset(key, 'b', int(b))
    r_param.hset(key, 'c', int(c))
    r_param.hset(key, 'd', int(d))
    r_param.hset(key, 'e', int(e))
    r_param.hset(key, 'f', int(f))
    r_param.hset(key, 'g', int(g))
    r_param.hset(key, 'h', int(h))
    # update last processed id
    key_last_processed = key_for_param(['last_processed'])
    r_param.set(key_last_processed, id_processed)


def read_parameters():
    r_param = redis_param()
    key = key_for_param(['param'])
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


def key_for_param(keys):
    a_keys = ['othelloparam', 'simplelearn'] + keys
    return ':'.join(a_keys)


def redis_param():
    r_param = redis.Redis(host='localhost', port=6379, db=2)
    return r_param


def mask_count(book, side, mask):
    ret = 0
    for i in range(0, 64):
        if (mask >> i) & 1 > 0:
            if book['book'][63 - i] == side:
                ret += 1
    return ret


def last_processed():
    r_param = redis_param()
    key_last_processed = key_for_param(['last_processed'])
    if not r_param.exists(key_last_processed):
        r_param.set(key_last_processed, -1)

    return int(r_param.get(key_last_processed))


class SimpleLearn:
    def __init__(self):
        self.a = 0.03
        self.b = 0.003           # learning rate
        self.l = 0.90           # turn decay in TD-lambda

    def update_state_map(self, a_book, side, turn_left, value):
        r_param = redis_param()
        key = key_for_param(['param', 'state', self.hash_from_book(a_book, side)])
        if not r_param.exists(key):
            r_param.set(key, 0)

        current_value = float(r_param.get(key))
        new_value = float(value) * (self.l ** turn_left)
        if current_value == 0:
            r_param.set(key, new_value)
        else:
            r_param.set(key, current_value * (1-self.a) + new_value * self.a)
        return current_value, r_param.get(key)

    def hash_from_book(self, a_book, side):
        (a, b, c, d, e, f, g, h) = self.counts(a_book, side)
        return ':'.join([str(a), str(b), str(c), str(d), str(e), str(f), str(g), str(h)])

    def state_from_hash(self, state):
        a = state.split(':')
        return int(a[4]), int(a[5]), int(a[6]), int(a[7]), int(a[8]), int(a[9]), int(a[10]), int(a[11])

    def random_sample(self, num):
        r_param = redis_param()
        key = key_for_param(['param', 'state', '*'])
        print key
        states = r_param.keys(key)
        len(states)
        ret = set()
        for i in range(num):
            key_rand = random.choice(states)
            ret.add((self.state_from_hash(key_rand), r_param.get(key_rand)))

        return list(ret)

    def store_batch_stats(self, books):
        pass

    def learn_and_update_batch(self, books):
        self.store_batch_stats(books)

        for book_id, book in books:
            self.learn_and_update_one(book_id, book)

    def learn_and_update_one(self, book_id, book):
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
        parameters = read_parameters()
        samples = self.random_sample(500)
        err, new_param = self.fit_parameters(parameters, samples)
        print 'Learn complete:'
        print err
        print new_param

        # store parameter
        update_parameters(book_id, new_param)

    def fit_parameters(self, parameters, samples):
        err = 99999
        for i in range(10000):
            new_parameters = self.fit_parameters_once(parameters, samples)
            err = self.norm(parameters, new_parameters)
            print 'param is %s, err: %f' % (str(new_parameters), err)
            if err < 0.005:
                parameters = new_parameters
                break
            parameters = new_parameters
        return err, parameters

    def norm(self, a, b):
        ret = 0
        for i in range(len(a)):
            ret += (a[i] - b[i]) ** 2
        return math.sqrt(ret)

    def fit_parameters_once(self, parameters, samples):
        w = list(parameters)
        new_w = list(parameters)
        for j in range(8):
            q = 0
            for i in samples:
                e_i = float(i[1])
                e_i_d = self.eval_vector(w, i[0])
                f_j_p_i = i[0][j]
                # print '[%s] e_i %f, e_i_d %f, f_j_p_i %f' % (str(i), e_i, e_i_d, f_j_p_i)
                q += (e_i - e_i_d) * f_j_p_i
            a = self.b / len(samples)
            new_w[j] = w[j] + 2 * a * q
            print 'q is %f' % q
            print 'Updated %d %f -> %f' % (j, w[j], new_w[j])
        return tuple(new_w)

    def eval_vector(self, parameters, features):
        ret = 0
        for i in range(len(parameters)):
            ret += parameters[i] * features[i]
        return ret

    def counts(self, a_book, side):
        a = mask_count(a_book, side, 0x8100000000000081)
        b = mask_count(a_book, side, 0x4281000000008142)
        c = mask_count(a_book, side, 0x0042000000004200)
        d = mask_count(a_book, side, 0x2400810000810024)
        e = mask_count(a_book, side, 0x1800008181000018)
        f = mask_count(a_book, side, 0x003C424242423C00)
        g = mask_count(a_book, side, 0x0000240000240000)
        h = mask_count(a_book, side, 0x0000183C3C180000)
        return a, b, c, d, e, f, g, h

    def eval(self, a_book, side, parameters):
        (a, b, c, d, e, f, g, h) = self.counts(a_book, side)
        (ca, cb, cc, cd, ce, cf, cg, ch) = parameters
        return a * ca + b * cb + c * cc + d * cd + e * ce + f * cf + g * cg + h * ch
