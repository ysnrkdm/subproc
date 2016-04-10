import paramgen
import subproc


class ElJemTask(object):
    queue = "SimpleLearnWorker"

    @staticmethod
    def perform(args):
        conf, params = args
        # Firstly, fetch the param, and generate param file
        print 'start paramgen...'
        paramgen.write_data(params)
        print 'paramgen done. starting match...'
        print 'param used : %s' % params

        # Then, match
        subproc.do_match(conf)
        print 'done'
