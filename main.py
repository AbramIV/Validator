import sys
import logging
import ipaddress
from PyQt6.QtWidgets import QApplication
from core.gui import MainWindow
import yaml

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler('logs.log'), logging.StreamHandler(sys.stdout)])
    
def load_config():
    with open('config.yaml', 'r') as stream:
        config = yaml.safe_load(stream)

    ipaddress.ip_address(config['api']['ip'])
    ipaddress.ip_address(config['printer']['ip'])
    int(config['printer']['port'])
    int(config['system']['reset_interval'])
    int(config['system']['http_timeout'])
    
    if int(config['printer']['port']) < 1 or int(config['printer']['port']) > 65535:
        raise ValueError("Port number out of valid range (1-65535): %s", config['printer']['port'])

    if config["printer"]["name"] == "":
        raise ValueError("Printer name cannot be empty.")
    
    if int(config['system']['reset_interval']) < 5 or int(config['system']['reset_interval']) > 50:
        raise ValueError("Reset interval out of valid range (5-50): %s", config['system']['reset_interval'])
    
    if int(config['system']['http_timeout']) < 1 or int(config['system']['http_timeout']) > 10:
        raise ValueError("HTTP timeout out of valid range (1-10): %s", config['system']['http_timeout'])

    return config

if __name__ == '__main__':
    logging.info("Application started.")

    try:
        config = load_config()
        app = QApplication(sys.argv)
        w = MainWindow(config)
        app.exec()  
    except Exception as ex:
        logging.fatal("Unhandled exception: " + str(ex))
    finally:
        logging.info("Application closed.")  

 