import sys
import logging
import ipaddress
from GUI.MainWindow import MainWindow
from PyQt6.QtWidgets import QApplication
from core.enums import AppArguments
import configparser

logging.basicConfig(filename='logs.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("__main__")
config = configparser.ConfigParser()

def args_validate(args) -> int:
    config.read('config.ini')
    code = 0

    try:
        args[AppArguments.IP_VALIDATE.value] = config['API']["IP"]
        args[AppArguments.IP_PRINTER.value] = config['Printer']["IP"]
        args[AppArguments.PORT_PRINTER.value] = config['Printer']["port"]
        args[AppArguments.RESET_INTERVAL.value] = config['System']["reset_interval"]
    except Exception as ex:
        logger.error(f"read config.ini error: {ex}")
        code += 1

    if code == 0:
        try:
            ipaddress.ip_address(args[AppArguments.IP_VALIDATE.value])
            ipaddress.ip_address(args[AppArguments.IP_PRINTER.value])
        except ValueError:
            logger.error("Invalid IP addresses provided: \n" + args[AppArguments.IP_VALIDATE.value] + "\n" + args[AppArguments.IP_PRINTER.value])
            code += 1

    if code == 0:
        if args[AppArguments.PORT_PRINTER.value].isdigit():
            if int(args[AppArguments.PORT_PRINTER.value]) < 1 or int(args[AppArguments.PORT_PRINTER.value]) > 65535:
                logger.error("Port number out of valid range (1-65535): \n" + args[AppArguments.PORT_PRINTER.value])
                code += 1
        else:
            logger.error("Ports are not a valid integer: \n" + args[AppArguments.PORT_PRINTER.value])
            code += 1  

    if code == 0:
        if args[AppArguments.RESET_INTERVAL.value].isdigit():
            if int(args[AppArguments.RESET_INTERVAL.value]) < 5 or int(args[AppArguments.RESET_INTERVAL.value]) > 50:
                logger.error("Reset interval out of valid range (5-50): \n" + args[AppArguments.RESET_INTERVAL.value])
                code += 1
        else:
            logger.error("Reset interval is not a valid integer: \n" + args[AppArguments.RESET_INTERVAL.value])
            code += 1
    return code
    
if __name__ == '__main__':
    logger.info("Application started.")
    args = ["","","",""]

    code = args_validate(args)
    if code > 0:
        sys.exit(code)

    try:
        app = QApplication(sys.argv)
        w = MainWindow(args)
        app.exec()
    except Exception as ex:
        logger.fatal("Unhandled exception: " + str(ex))
    finally:
        logger.info("Application closed.")   
 