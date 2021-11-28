import logging
import logging.config
import pathlib
from threading import Thread

from app.controllers.webserver import start

# logging.basicConfig(level=logging.INFO, stream=sys.stdout)
base_dir = pathlib.Path(__name__).parent.resolve()
log_file_path = pathlib.Path(base_dir) / 'conf/production/logger.conf'
logging.config.fileConfig(fname=log_file_path, disable_existing_loggers=False)


if __name__ == '__main__':

    serverThread = Thread(target=start)
    serverThread.start()
    serverThread.join()