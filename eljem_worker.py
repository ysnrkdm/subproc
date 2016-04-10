from pyres import setup_logging
from pyres.worker import Worker
from eljem_task import ElJemTask
import sys
import config

setup_logging(ElJemTask.queue)
conf = config.config_by_filename(sys.argv[1])
Worker.run([ElJemTask.queue], password=conf['redis_password'])