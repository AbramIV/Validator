import ipaddress
import sys
from GUI.MainWindow import MainWindow
from PyQt6.QtWidgets import QApplication
import logging

from core.enums import AppArguments

logging.basicConfig(filename='logs.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Logger")
code = 0

if __name__ == '__main__':
    logger.info("Application started.")

    if len(sys.argv) > 2:
        arguments = sys.argv[1:]
        for i, arg in enumerate(arguments):
            logger.info(f"Argument {i+1}: {arg}")
    else:
        logger.error("No arguments provided. Expected IP address and Port.")
        code = 1

    if code == 0:
        try:
            ipaddress.ip_address(arguments[AppArguments.IP.value])
        except ValueError:
            logger.error("Invalid IP address provided: " + arguments[AppArguments.IP.value])
            code = 2

    if code == 0:
        if arguments[AppArguments.Port.value].isdigit():
            if int(arguments[AppArguments.Port.value]) < 1 or int(arguments[AppArguments.Port.value]) > 65535:
                logger.error("Port number out of valid range (1-65535): " + arguments[AppArguments.Port.value])
                code = 4
        else:
            logger.error("Port is not a valid integer: " + arguments[AppArguments.Port.value])
            code = 3  

    if code > 0:
        sys.exit(code)

    try:
        app = QApplication(sys.argv)
        w = MainWindow(arguments[AppArguments.IP.value] + ":" + arguments[AppArguments.Port.value])
        app.exec()
    except Exception as ex:
        logger.fatal("Unhandled exception: " + str(ex))
    finally:
        logger.info("Application closed.")
        