from replearn import get_learn


class ParallelLearnerTask(object):
    queue = "ParallelLearnerWorker"

    @staticmethod
    def perform(args):
        conf, phase_from, phase_to = args
        # Firstly, fetch the param, and generate param file
        print 'start learning...'
        learn = get_learn(conf)
        mse, score, param, nsample = learn.fit_parameter(phase_from, phase_to)
        r_param = learn._param_store()
        key = ['fitting', str(phase_from), str(phase_to)]
        mapping = {
            "mse": mse,
            "score": score,
            "param": param,
            "nsample": nsample
        }
        r_param.hmset(key, mapping)
        print 'done learning for %d - %d, waiting for next task, %s' % (phase_from, phase_to, str(mapping))
