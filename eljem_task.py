import paramgen
import subproc


class ElJemTask(object):
    queue = "SimpleLearnWorker"

    @staticmethod
    def perform(params):
        # Firstly, fetch the param, and generate param file
        print 'start paramgen...'
        paramgen.write_data(params)
        print 'paramgen done. starting match...'
        print 'param used : %s' % params

        # Then, match
        subproc.do_match('/Users/Yoshinori/Documents/OneDrive/codes/FlatReversi/subproc/subproc.cfg')
        print 'done'