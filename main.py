import sys
import logging
import ipaddress
from GUI.MainWindow import MainWindow
from PyQt6.QtWidgets import QApplication
from core.enums import AppArguments
import configparser

logging.basicConfig(filename='logs.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Logger")
config = configparser.ConfigParser()
code = 0

if __name__ == '__main__':
    logger.info("Application started.")
    arguments = ["","","",""]

    config.read('config.ini')

    try:
        arguments[AppArguments.IP1.value] = config['HOST1']["IP"]
        arguments[AppArguments.Port1.value] = config['HOST1']["port"]
        arguments[AppArguments.IP2.value] = config['HOST2']["IP"]
        arguments[AppArguments.Port2.value] = config['HOST2']["port"]
    except Exception as ex:
        logger.error(f"read config.ini error: {ex}")
        code += 1

    if code == 0:
        try:
            ipaddress.ip_address(arguments[AppArguments.IP1.value])
            ipaddress.ip_address(arguments[AppArguments.IP2.value])
        except ValueError:
            logger.error("Invalid IP addresses provided: \n" + arguments[AppArguments.IP1.value] + "\n" + arguments[AppArguments.IP2.value])
            code += 1

    if code == 0:
        if arguments[AppArguments.Port1.value].isdigit() and arguments[AppArguments.Port2.value].isdigit():
            if int(arguments[AppArguments.Port1.value]) < 1 or int(arguments[AppArguments.Port2.value]) > 65535:
                logger.error("Port number out of valid range (1-65535): \n" + arguments[AppArguments.Port1.value] + "\n" + arguments[AppArguments.Port2.value] )
                code += 1
        else:
            logger.error("Ports are not a valid integer: \n" + arguments[AppArguments.Port1.value] + "\n" + arguments[AppArguments.Port2.value])
            code += 1  

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
        