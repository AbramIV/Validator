import sys
from GUI.MainWindow import MainWindow
from PyQt6.QtWidgets import QApplication
import logging

from core.enums import AppArguments

logging.basicConfig(filename='logs.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Logger")

if __name__ == '__main__':
    try:
        if len(sys.argv) > 1:
            arguments = sys.argv[1:]
            logger.info(f"Arguments received: {arguments}")
            for i, arg in enumerate(arguments):
                logger.info(f"Argument {i+1}: {arg}")
        else:
            logger.error("No arguments provided. IP address is required.")
            sys.exit(1)

        app = QApplication(sys.argv)
        w = MainWindow(logger, arguments[AppArguments.IP.value])
        app.exec()
    except Exception as ex:
        logger.fatal("Unhandled exception: " + str(ex))
        
    