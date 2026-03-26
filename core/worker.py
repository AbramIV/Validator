import logging
from core.enums import AssociationStatus, Input, MistakeType, Output, StepType
from core.hardware import USB5860, Printer, Scanner
from core.http import HttpClient
from core.production import Shift
import threading
import json

MAX_POSITIONS_COUNT = 4

DEVICE_DESCRIPTION = "USB-5860,BID#0"
PROFILE_PATH = u"../../profile/USB-5860.xml"

class Worker():
    def __init__(self, config):  
        self.scanner = Scanner()
        self.printer = Printer()
        self.client = HttpClient(config["system"]["http_timeout"])
        self.shift = Shift(StepType.Insert)
        
        self.printer.ip = config["printer"]["ip"]
        self.printer.port = config["printer"]["port"]
        self.printer.name = config["printer"]["name"]

        self.ip = config["api"]["ip"]
        self.input = [0, 0, 0, 0, 0, 0, 0, 0]
        self.last_input = self.input
        self.sensors_sum = 0
        self.sensors_last_sum = 0
        self.reset_interval = config["system"]["reset_interval"]
        self.reset_count = 0
        self.reset_delay = 0
        self.output = [0, 0, 0, 0, 0, 0, 0, 0]
        self.message = "Instalar todos partes."
        self.last_message = ""
        self.mistake_msg = ""
        self.pcb1 = ""
        self.pcb2 = ""
        self.heatsink = ""
        self.heatsink_printed = ""
        self.side = ""
        self.url = ""
        self.zpl = ""
        self.error = False
        self.mistake = MistakeType.Nope
        self.association = AssociationStatus.Nope

        try:
            self.device = USB5860(DEVICE_DESCRIPTION, PROFILE_PATH)
        except Exception as ex:
            self.error = False
            logging.error("Advantech USB-5860 init error: " + str(ex))
            self.message = "Advantech USB-5860 init error!"
        
        self.scanner_thread = threading.Thread(target=self.scanner.scan, daemon=True)
        self.scanner_thread.start()

    def work(self):
        if not self.poll() or self.reset(): return
        
        if self.shift.currentStep.type == StepType.Insert:
            if self.sensors_sum == MAX_POSITIONS_COUNT:
                self.client.reset()
                self.shift.step(StepType.Pick)
                self.sensors_last_sum = self.sensors_sum
                self.message = "Elige uno parte!"
                
                if self.mistake == MistakeType.MoreThanOneTaken:
                    self.mistake = MistakeType.Nope
            else:
                self.message = "Instalar todos partes!"
        
        if self.shift.currentStep.type == StepType.Pick:
            self.scanCount = 0
            self.validateCount = 0
            self.pcb1 = ""
            self.pcb2 = ""
            self.heatsink_printed = ""
            if self.sensors_last_sum != self.sensors_sum:
                self.mistake = MistakeType.Nope
                self.association = AssociationStatus.Nope
                self.client.reset()
                if  self.sensors_sum > self.sensors_last_sum: 
                    self.mistake = MistakeType.AddedAfterStart
                    self.mistake_msg = "No devuelva las piezas!\nElige uno parte para continuar!"
                if (self.sensors_last_sum - self.sensors_sum) == 1:   
                    if self.input[Input.RH1.value] != self.last_input[Input.RH1.value]:
                        self.message = "Esta parte de la izquierda!\n"
                        self.side = "LH"
                    elif self.input[Input.RH2.value] != self.last_input[Input.RH2.value]:
                        self.message = "Esta parte de la izquierda!\n"
                        self.side = "LH"
                    elif self.input[Input.LH1.value] != self.last_input[Input.LH1.value]:
                        self.message = "Esta parte de la derecha!\n"
                        self.side = "RH"
                    else:
                        self.message = "Esta parte de la derecha!\n"
                        self.side = "RH"
                    self.shift.step(StepType.Scan_PCB_1)
                    self.scanner.reset()
                    self.message += "Escanear el codigo 1!"
                    self.sensors_last_sum = self.sensors_sum
                else:
                    self.shift = Shift(StepType.Insert)
                    
        if self.shift.currentStep.type == StepType.Scan_PCB_1:
            if not self.is_position_valid(): return

            if self.scanner.isScanned:
                self.pcb1 = "".join(self.scanner.buffer)
                self.message = "Escanear el codigo 2!"
                self.shift.step(StepType.Scan_PCB_2)
                self.scanner.reset()

        if self.shift.currentStep.type == StepType.Scan_PCB_2:
            if not self.is_position_valid(): return

            if self.scanner.isScanned:
                self.pcb2 = "".join(self.scanner.buffer)
                if self.pcb1 == self.pcb2:
                    self.mistake = MistakeType.CodeScannedTwice
                    self.mistake_msg = "Escaneaste lo mismo!\nEscanea el segundo codigo QR!"
                else:
                    self.url = f"http://{self.ip}/apiDB/api/getHeatsink/?pcb1={self.pcb1}&pcb2={self.pcb2}&side={self.side}"
                    self.mistake = MistakeType.Nope
                    self.shift.step(StepType.Valid_PCB)
                    self.message = "Validacion, espera..."
                self.scanner.reset()

        if self.shift.currentStep.type == StepType.Valid_PCB:
            if self.client.get(self.url): 
                if self.is_position_valid():
                    python_object = json.loads(self.client.response)
                    if python_object[self.client.api1.result] == "true" or "ya existen" in python_object[self.client.api1.message]:
                        
                        if "ya existen" in python_object[self.client.api1.message]:
                            serial = str(python_object[self.client.api1.message]).split()[-1]
                            self.heatsink = serial
                            self.zpl = f"^XA\r\n^MMT\r\n^PW472\r\n^LL0354\r\n^LS0\r\n^FT32,149^A0N,49,50^FH\\^FD20260313^FS\r\n^FT113,303^A0N,50,50^FH\\^FD12:39^FS\r\n^FO258,117^GB189,189,5^FS\r\n^FT28,73^A0N,58,64^FH\\^FD1144.006.0630^FS\r\n^FT32,305^A0N,50,50^FH\\^FD00^FS\r\n^FT32,225^A0N,42,40^FH\\^FD0000000005^FS\r\n^BY144,144^FT282,285^BXN,8,200,18,18,1,~\r\n^FH\\^FD{serial}^FS\r\n^PQ1,0,1,Y^XZ"
                        else:
                            self.zpl = python_object[self.client.api1.zpl]
                            self.heatsink = python_object[self.client.api1.heatsink]
                        
                        self.message = "Impresion..."
                        self.shift.step(StepType.Print)
                        self.reprint = True
                    else:
                        logging.warning(python_object[self.client.api1.message])
                        if self.sensors_sum == 0:
                            self.message = python_object[self.client.api1.message] + "\nInstalar todos partes."
                            self.shift.save()
                            self.shift = Shift(StepType.Insert)
                        else:
                            self.shift = Shift(StepType.Pick)
                            self.message = python_object[self.client.api1.message] + "\nElige uno parte."            
            else:
                if self.is_position_valid():
                    logging.error(self.client.message)                    
                    if self.sensors_sum == 0:
                        self.shift.save()
                        self.message = "HTTP pedido error!\nContactar con soporte O\ninstalar todos para continuar!"
                        self.shift = Shift(StepType.Insert)
                    else:
                        self.message = "HTTP pedido error!\nContactar con soporte O\nelige uno parte para continuar!"
                        self.shift = Shift(StepType.Pick)

        if self.shift.currentStep.type == StepType.Scan_Heatsink:
            if not self.is_position_valid(): return

            if self.input[Input.Button.value]:
                self.shift.step(StepType.Print)
                return
            
            if self.scanner.isScanned:
                self.heatsink_printed = "".join(self.scanner.buffer)
                if self.heatsink_printed in (self.pcb1, self.pcb2):
                    self.mistake = MistakeType.CodeScannedTwice
                    self.mistake_msg = "Escaneó el código de la pieza. ¡Escanee el código impreso!"
                elif self.heatsink_printed != self.heatsink:
                    self.mistake = MistakeType.PrintedCodeInvalid
                    self.mistake_msg = "El código escaneado está no correcto!\nEscanea el codigo impreso!"
                else:
                    self.url = f"http://{self.ip}/apiDB/api/validateHeatsink/?pcb1={self.pcb1}&pcb2={self.pcb2}&heat={self.heatsink}&side={self.side}"
                    self.mistake = MistakeType.Nope
                    self.shift.step(StepType.Valid_Heatsink)
                    self.message = "Validacion, espera..."
                self.scanner.reset()

        if self.shift.currentStep.type == StepType.Print:
            if self.printer.print_via_usb(self.zpl):
                self.message = "Escanear el codigo impreso!\nSi la pegatina está dañada, pulse el botón para volver a imprimirla."
                self.shift.step(StepType.Scan_Heatsink)
            else:
                logging.error(self.printer.error)
                if self.sensors_sum == 0:
                    self.shift = Shift(StepType.Insert)
                    self.message = self.printer.error + " Instalar todos partes."
                else: 
                    self.shift = Shift(StepType.Pick)
                    self.message = self.printer.error + " Elige uno parte!"
                self.printer.reset()
        
        if self.shift.currentStep.type == StepType.Valid_Heatsink:
            if self.client.get(self.url):
                if self.is_position_valid():    
                    python_object = json.loads(self.client.response)
                    self.association = AssociationStatus.HeatsinkAssociated if python_object[self.client.api2.result] == "true" else AssociationStatus.HeatsinkNotAssociated
                    if self.sensors_sum == 0: 
                        self.shift = Shift(StepType.Insert)
                        self.shift.save()
                        self.message = python_object[self.client.api2.message] + "\nInstalar todos partes."
                    else:
                        self.shift = Shift(StepType.Pick)
                        self.message = python_object[self.client.api2.message] + "\nElige uno parte!"
            else: 
                if self.is_position_valid():
                    logging.error(self.client.response)                    
                    if self.sensors_sum == 0:
                        self.shift.save()
                        self.message = "HTTP pedido error!\nContactar con soporte O\ninstalar todos para continuar!"
                        self.shift = Shift(StepType.Insert)
                    else:
                        self.message = "HTTP pedido error!\nContactar con soporte O\nelige uno parte para continuar!"
                        self.shift = Shift(StepType.Pick)
                
        self.last_input = self.input

    def is_position_valid(self):
        if self.sensors_last_sum != self.sensors_sum:
            if self.sensors_last_sum > self.sensors_sum:
                self.mistake = MistakeType.MoreThanOneTaken
                self.mistake_msg = "No extraiga la pieza hasta que haya terminado el último proceso!\nInstalar todos partes para continuar!"
            else:
                self.mistake = MistakeType.AddedAfterStart
                if self.sensors_sum == MAX_POSITIONS_COUNT:
                    self.mistake_msg = "No agregue piezas después de comenzar el proceso!\nElige uno parte para continuar!"
                else:
                    self.mistakeMsg = "No devuelva las piezas!\nInstalar todos partes para continuar!"
            self.clear()
            return False
        return True
    
    def poll(self):
        try:
            self.input = self.device.readInputsAsList()
            self.sensors_sum = self.input[Input.RH1.value] + self.input[Input.RH2.value] + self.input[Input.LH1.value] + self.input[Input.LH2.value]
            self.output = self.device.readOutputsAsList()

            if self.error:
                self.error = False
                logging.error("Advantech USB-5860 conexion ha sido restaurada.")
        except Exception as ex:
            self.clear()
            if not self.error:
                self.error = True
                self.message = "Advantech USB-5860 encuesta error!"
                logging.error("Advantech USB-5860 request error: " + str(ex))
            if self.device.isDisposed:
                self.device = USB5860("USB-5860,BID#0", u"../../profile/USB-5860.xml")
            return False
        return True
            
    def reset(self):
        if self.input[Input.Button.value]:
            if self.reset_delay < 15:
                self.reset_delay += 1
                if self.reset_delay == 1: return False
                return True
        
            if self.reset_count >= self.reset_interval:
                self.clear()
                self.mistake = MistakeType.Nope
                self.shift.step(StepType.Insert)
                self.mistake_msg = ""
                self.message = "Sistema reiniciado.\nSuelte el boton!"
                return True
            if self.reset_count < 1:
                self.last_message = self.message
            self.reset_count += 1
            self.message = f"Reiniciando el sistema\nNo suelte el botón... {self.reset_interval-self.reset_count}"
            logging.warning(f"Botón de reinicio presionado: {self.reset_interval-self.reset_count}.")
            return True
        else:
            if self.reset_count > 0:
                self.reset_count = 0
                self.message = self.last_message
                self.last_message = ""
            self.reset_delay = 0
        return False

    def clear(self):
        self.sensors_last_sum = 0
        self.pcb1 = ""
        self.pcb2 = ""
        self.heatsink = ""
        self.heatsink_printed = ""
        self.side = ""
        self.url = ""
        self.shift.save()
        self.scanner.reset()
        self.client.reset()
        self.shift = Shift(StepType.Insert)
