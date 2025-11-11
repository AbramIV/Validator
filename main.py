import sys
import logging
import ipaddress
from GUI.MainWindow import MainWindow
from PyQt6.QtWidgets import QApplication
from core.enums import AppArguments

logging.basicConfig(filename='logs.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Logger")
code = 0

if __name__ == '__main__':
    logger.info("Application started.")

    if len(sys.argv) > 4:
        arguments = sys.argv[1:]
        for i, arg in enumerate(arguments):
            logger.info(f"Argument {i+1}: {arg}")
    else:
        logger.error("No arguments provided. Expected 2 IP addresses and ports.")
        code = 1

    if code == 0:
        try:
            ipaddress.ip_address(arguments[AppArguments.IP1.value])
            ipaddress.ip_address(arguments[AppArguments.IP2.value])
        except ValueError:
            logger.error("Invalid IP addresses provided: \n" + arguments[AppArguments.IP1.value] + "\n" + arguments[AppArguments.IP2.value])
            code = 2

    if code == 0:
        if arguments[AppArguments.Port1.value].isdigit() and arguments[AppArguments.Port2.value].isdigit():
            if int(arguments[AppArguments.Port1.value]) < 1 or int(arguments[AppArguments.Port2.value]) > 65535:
                logger.error("Port number out of valid range (1-65535): \n" + arguments[AppArguments.Port1.value] + "\n" + arguments[AppArguments.Port2.value] )
                code = 4
        else:
            logger.error("Ports are not a valid integer: \n" + arguments[AppArguments.Port1.value] + "\n" + arguments[AppArguments.Port2.value])
            code = 3  

    if code > 0:
        sys.exit(code)

    try:
        app = QApplication(sys.argv)
        w = MainWindow(arguments)
        app.exec()
    except Exception as ex:
        logger.fatal("Unhandled exception: " + str(ex))
    finally:
        logger.info("Application closed.")
        