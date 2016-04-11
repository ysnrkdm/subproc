import paramgen
import subproc


class ElJemTask(object):
    queue = "SimpleLearnWorker"

    @staticmethod
    def perform(args):
        conf, params = args
        # Firstly, fetch the param, and generate param file
        print 'start paramgen...'
        file_full_path = conf['paramgen_output_path']
        paramgen.write_data(params, file_full_path)
        print 'paramgen done. starting match...'
        print 'param used : %s' % params

        # Then, match
        subproc.do_match(conf)
        print 'done'
