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
        arguments[AppArguments.IP_VALIDATE.value] = config['API']["IP"]
        arguments[AppArguments.IP_PRINTER.value] = config['Printer']["IP"]
        arguments[AppArguments.PORT_PRINTER.value] = config['Printer']["port"]
        arguments[AppArguments.RESET_INTERVAL.value] = config['System']["reset_interval"]
    except Exception as ex:
        logger.error(f"read config.ini error: {ex}")
        code += 1

    if code == 0:
        try:
            ipaddress.ip_address(arguments[AppArguments.IP_VALIDATE.value])
            ipaddress.ip_address(arguments[AppArguments.IP_PRINTER.value])
        except ValueError:
            logger.error("Invalid IP addresses provided: \n" + arguments[AppArguments.IP_VALIDATE.value] + "\n" + arguments[AppArguments.IP_PRINTER.value])
            code += 1

    if code == 0:
        if arguments[AppArguments.PORT_PRINTER.value].isdigit():
            if int(arguments[AppArguments.PORT_PRINTER.value]) < 1 or int(arguments[AppArguments.PORT_PRINTER.value]) > 65535:
                logger.error("Port number out of valid range (1-65535): \n" + arguments[AppArguments.PORT_PRINTER.value])
                code += 1
        else:
            logger.error("Ports are not a valid integer: \n" + arguments[AppArguments.PORT_PRINTER.value])
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
        