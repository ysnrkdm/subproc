from pyres import setup_logging
from pyres.worker import Worker
from parallel_learner_task import ParallelLearnerTask
import sys
import config

setup_logging(ParallelLearnerTask.queue)
conf = config.config_by_filename(sys.argv[1])
server = config.redis_hostname_port_from_config(conf)
Worker.run([ParallelLearnerTask.queue], server=server, password=conf['redis_password'])
