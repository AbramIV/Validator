import sys
import logging
import ipaddress
from GUI.MainWindow import MainWindow
from PyQt6.QtWidgets import QApplication
from core.enums import AppArguments
import configparser

from core.hardware import Printer

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler('logs.log'), logging.StreamHandler(sys.stdout)])
config = configparser.ConfigParser()

zpl = "^XA\r\n^MMT\r\n^PW472\r\n^LL0354\r\n^LS0\r\n^FT32,149^A0N,49,50^FH\\^FD20260313^FS\r\n^FT113,303^A0N,50,50^FH\\^FD12:39^FS\r\n^FO258,117^GB189,189,5^FS\r\n^FT28,73^A0N,58,64^FH\\^FD1144.006.0630^FS\r\n^FT32,305^A0N,50,50^FH\\^FD00^FS\r\n^FT32,225^A0N,42,40^FH\\^FD0000000005^FS\r\n^BY144,144^FT282,285^BXN,8,200,18,18,1,~\r\n^FH\\^FD1144.006.06300000000000058Q^FS\r\n^PQ1,0,1,Y^XZ"

def args_validate(args) -> int:
    config.read('config.ini')
    code = 0

    try: 
        args[AppArguments.IP_VALIDATE.value] = config['API']["IP"]
        args[AppArguments.IP_PRINTER.value] = config['Printer']["IP"]
        args[AppArguments.PORT_PRINTER.value] = config['Printer']["port"]
        args[AppArguments.RESET_INTERVAL.value] = config['System']["reset_interval"]
    except Exception as ex:
        logging.error(f"read config.ini error: {ex}")
        code += 1

    if code == 0:
        try:
            ipaddress.ip_address(args[AppArguments.IP_VALIDATE.value])
            ipaddress.ip_address(args[AppArguments.IP_PRINTER.value])
        except ValueError:
            logging.error("Invalid IP addresses provided: \n" + args[AppArguments.IP_VALIDATE.value] + "\n" + args[AppArguments.IP_PRINTER.value])
            code += 1
  
    if code == 0:
        if args[AppArguments.PORT_PRINTER.value].isdigit():
            if int(args[AppArguments.PORT_PRINTER.value]) < 1 or int(args[AppArguments.PORT_PRINTER.value]) > 65535:
                logging.error("Port number out of valid range (1-65535): \n" + args[AppArguments.PORT_PRINTER.value])
                code += 1
        else:
            logging.error("Ports are not a valid integer: \n" + args[AppArguments.PORT_PRINTER.value])
            code += 1

    if code == 0:
        if args[AppArguments.RESET_INTERVAL.value].isdigit():
            if int(args[AppArguments.RESET_INTERVAL.value]) < 5 or int(args[AppArguments.RESET_INTERVAL.value]) > 50:
                logging.error("Reset interval out of valid range (5-50): \n" + args[AppArguments.RESET_INTERVAL.value])
                code += 1
        else:
            logging.error("Reset interval is not a valid integer: \n" + args[AppArguments.RESET_INTERVAL.value])
            code += 1
    return code
    
if __name__ == '__main__':
    logging.info("Application started.")
    args = ["","","",""]
    code = args_validate(args)
    if code > 0:
        sys.exit(code)

    try:
        app = QApplication(sys.argv)
        w = MainWindow(args)
        app.exec()
        #printer = Printer()
        #printer.set_ip(args[AppArguments.IP_PRINTER.value])
        #printer.set_port(int(args[AppArguments.PORT_PRINTER.value]))
        #printer.print(zpl)
    except Exception as ex:
        logging.fatal("Unhandled exception: " + str(ex))
    finally:
        logging.info("Application closed.")   
 