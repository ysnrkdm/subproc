from pyres import setup_logging
from pyres.worker import Worker
from eljem_task import ElJemTask
import sys
import config

setup_logging(ElJemTask.queue)
conf = config.config_by_filename(sys.argv[1])
server = config.redis_hostname_port_from_config(conf)
Worker.run([ElJemTask.queue], server=server, password=conf['redis_password'])