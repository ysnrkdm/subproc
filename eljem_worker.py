from pyres import setup_logging
from pyres.worker import Worker
from eljem_task import ElJemTask

setup_logging(ElJemTask.queue)
Worker.run([ElJemTask.queue])