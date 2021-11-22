import logging
import sys
from threading import Thread

from app.controllers.webserver import start

logging.basicConfig(level=logging.INFO, stream=sys.stdout)


if __name__ == '__main__':

    serverThread = Thread(target=start)
    serverThread.start()
    serverThread.join()