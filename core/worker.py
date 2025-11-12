import logging
import requests
from core.enums import AppArguments, Input, MistakeType, Output, PrinterStatus, StepType
from core.hardware import USB5860, Printer, Scanner
from core.http import HttpClient
from core.production import Shift
import threading
import json

MAX_POSITIONS_COUNT = 4

DEVICE_DESCRIPTION = "USB-5860,BID#0"
PROFILE_PATH = u"../../profile/USB-5860.xml"

class Worker():
    def __init__(self, arguments):
        self.logger = logging.getLogger("__main__")
        
        self.ip_api = arguments[AppArguments.IP_VALIDATE.value]

        self.scanner = Scanner()
        self.printer = Printer(arguments[AppArguments.IP_PRINTER.value], arguments[AppArguments.PORT_PRINTER.value])
        self.client = HttpClient(1)
        self.shift = Shift(StepType.Fill)
        
        self.input = [0, 0, 0, 0, 0, 0, 0, 0]
        self.last_input = self.input
        self.sensors_sum = 0
        self.sensors_last_sum = 0
        self.reset = 0
        self.output = [0, 0, 0, 0, 0, 0, 0, 0]
        self.message = ""
        self.mistakeMsg = ""
        self.scanCount = 0
        self.validateCount = 0
        self.qr1 = ""
        self.qr2 = ""
        self.qr3 = ""
        self.side = ""
        self.url = ""
        self.zpl = ""
        self.mistake = MistakeType.Nope
        self.error = False

        try:
            self.device = USB5860(DEVICE_DESCRIPTION, PROFILE_PATH)
        except Exception as ex:
            self.error = False
            self.logger.error("Advantech USB-5860 init error: " + str(ex))
            self.message = "Advantech USB-5860 init error!"
        
        self.scanner_thread = threading.Thread(target=self.scanner.scan, daemon=True)
        self.scanner_thread.start()

    def work(self):
        if not self.poll(): return
        
        if self.shift.currentStep.type == StepType.Fill:
            if self.sensors_sum == MAX_POSITIONS_COUNT:
                self.client.reset()
                self.shift.step(StepType.Pick)
                self.sensors_last_sum = self.sensors_sum
                self.message = "Elige uno parte!"
                if self.mistake == MistakeType.MoreThanOneTaken:
                    self.mistake = MistakeType.Nope
            else:
                if not self.client.error:
                    self.message = "Instalar todos partes."
        
        if self.shift.currentStep.type == StepType.Pick:
            self.scanCount = 0
            self.validateCount = 0
            if self.sensors_last_sum != self.sensors_sum:
                self.mistake = MistakeType.Nope
                self.client.reset()
                if  self.sensors_sum > self.sensors_last_sum: 
                    self.mistake = MistakeType.AddedAfterStart
                    self.mistakeMsg = "No devuelva las piezas, finalice el proceso!\nElige uno parte para continuar!"
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
                    self.shift.step(StepType.Scan)
                    self.scanner.reset()
                    self.message += "Escanear el codigo 1!"
                    self.sensors_last_sum = self.sensors_sum
                else:
                    self.shift = Shift(StepType.Fill)
                    
        if self.shift.currentStep.type == StepType.Scan:
            if not self.is_position_valid(): return
            
            if self.input[Input.Button.value]:
                self.shift.step(StepType.Print)
                return

            if self.scanner.isScanned:
                if self.scanCount == 0:
                    self.qr1 = "".join(self.scanner.buffer)
                    self.message = "Escanear el codigo 2!"
                    self.scanCount += 1
                elif self.scanCount == 1:
                    self.qr2 = "".join(self.scanner.buffer)
                    if self.qr1 == self.qr2:
                        self.mistake = MistakeType.CodeScannedTwice
                        self.mistakeMsg = "Escaneaste lo mismo!\nEscanea el segundo codigo QR!" 
                    else:
                        self.url = f"http://{self.ip_api}/apiDB/api/zkw/serials?pcb1={self.qr1}&pcb2={self.qr2}&side={self.side}"
                        self.mistake = MistakeType.Nope
                        self.shift.step(StepType.Valid)
                        self.message = "Validacion, espera..."
                        self.scanCount += 1
                else:
                    self.qr3 = "".join(self.scanner.buffer)
                    if self.qr3 in (self.qr1, self.qr2):
                        self.mistake = MistakeType.CodeScannedTwice
                        self.mistakeMsg = "Escaneó el código de la pieza. ¡Escanee el código impreso!"
                    else:
                        self.scanCount = 0
                        self.url = f"http://{self.ip_api}/apiDB/api/zkw/linked?pcb1={self.qr1}&pcb2={self.qr2}&heatsink={self.qr3}"
                        self.mistake = MistakeType.Nope
                        self.shift.step(StepType.Valid)
                        self.message = "Validacion, espera..."
                self.scanner.reset()
                self.last_input = self.input
                return
                       
        if self.shift.currentStep.type == StepType.Valid:
            if self.validateCount < 1:
                if self.client.get(self.url):
                    if self.is_position_valid():
                        python_object = json.loads(self.client.message)
                        if python_object['SUCCESS']:
                            self.zpl = python_object['ZPL']
                            self.message = "Impresion..."
                            self.shift.step(StepType.Print)
                            self.reprint = True
                            self.validateCount += 1      
                        else:
                            self.logger.warning(python_object['MESSAGE'])
                            if self.sensors_sum == 0:
                                self.message = python_object['MESSAGE'] + "\nInstalar todos partes."
                                self.shift.save()
                                self.shift = Shift(StepType.Fill)
                            else:
                                self.shift = Shift(StepType.Pick)
                                self.message = python_object['MESSAGE'] + "\nElige uno parte."            
                else:
                    if self.is_position_valid():
                        self.logger.error(self.client.message)                    
                        if self.sensors_sum == 0:
                            self.shift.save()
                            self.message = "HTTP pedido error!\nContactar con soporte O\ninstalar todos para continuar!"
                            self.shift = Shift(StepType.Fill)
                        else:
                            self.message = "HTTP pedido error!\nContactar con soporte O\nelige uno parte para continuar!"
                            self.shift = Shift(StepType.Pick)
            else:
                if self.client.get(self.url):   
                    if self.is_position_valid():    
                        python_object = json.loads(self.client.message)
                        if python_object['SUCCESS']:
                            if self.sensors_sum == 0: 
                                self.shift = Shift(StepType.Fill)
                                self.message = "Instalar todos partes."
                            else: 
                                self.shift = Shift(StepType.Pick)
                                self.message = "Elige uno parte!"
                        else:
                            if self.sensors_sum == 0:
                                self.message = python_object['MESSAGE'] + "\nInstalar todos partes."
                                self.shift.save()
                                self.shift = Shift(StepType.Fill)
                            else:
                                self.shift = Shift(StepType.Pick)
                                self.message = python_object['MESSAGE'] + "\nNo valido! Elige uno parte." 
                else: 
                    if self.is_position_valid():
                        self.logger.error(self.client.message)                    
                        if self.sensors_sum == 0:
                            self.shift.save()
                            self.message = "HTTP pedido error!\nContactar con soporte O\ninstalar todos para continuar!"
                            self.shift = Shift(StepType.Fill)
                        else:
                            self.message = "HTTP pedido error!\nContactar con soporte O\nelige uno parte para continuar!"
                            self.shift = Shift(StepType.Pick)

        if self.shift.currentStep.type == StepType.Print:
            if (self.printer.print(self.zpl)):
                self.message = "Escanear el codigo impreso!\nSi la pegatina está dañada, pulse el botón para volver a imprimirla."
                Shift.step(StepType.Scan)
            else:
                self.logger.error(self.printer.message)
                if self.sensors_sum == 0: 
                    self.shift = Shift(StepType.Fill)
                    self.message = self.printer.message + " Instalar todos partes."
                else: 
                    self.shift = Shift(StepType.Pick)
                    self.message = self.printer.message + " Elige uno parte!"
        
        """   
        if self.shift.currentStep.type == StepType.Print:
            status = self.printer.get_status()
            if status == PrinterStatus.Printing:
                if not self.is_position_valid():
                    self.clear()
            else:
                self.printer.print(self.zpl)
                self.message = "Escanear el codigo impreso!\nSi la pegatina está dañada, pulse el botón para volver a imprimirla."
                Shift.step(StepType.Scan)
        """
                
        self.last_input = self.input

    def is_position_valid(self):
        if self.sensors_last_sum != self.sensors_sum:
            if self.sensors_last_sum > self.sensors_sum:
                self.mistake = MistakeType.MoreThanOneTaken
                self.mistakeMsg = "No extraiga la pieza hasta que haya terminado el último proceso!\nInstalar todos partes para continuar!"
            else:
                self.mistake = MistakeType.AddedAfterStart
                self.mistakeMsg = "No devuelva las piezas, finalice el proceso!\nElige uno parte para continuar!"
            self.clear()
            return False
        return True

    def poll(self):
        try:
            self.input = self.device.readInputsAsList()
            self.sensors_sum = self.input[Input.RH1.value] + self.input[Input.RH2.value] + self.input[Input.LH1.value] + self.input[Input.LH2.value]
            self.output = self.device.readOutputsAsList()
            self.reset = self.input[Input.Button.value]
            if self.output[Output.Reserve_0.value]:
                self.device.resetOutput(Output.Reserve_0.value)
            if self.error:
                self.error = False
                self.logger.error("Advantech USB-5860 conexion ha sido restaurada.")
        except Exception as ex:
            self.clear()
            if not self.error:
                self.error = True
                self.message = "Advantech USB-5860 encuesta error!"
                self.logger.error("Advantech USB-5860 request error: " + str(ex))
            if self.device.isDisposed:
                self.device = USB5860("USB-5860,BID#0", u"../../profile/USB-5860.xml")
            return False
        return True
            
    def clear(self):
        self.sensors_last_sum = 0
        self.scanCount = 0
        self.validateCount = 0
        self.qr1 = ""
        self.qr2 = ""
        self.qr3 = ""
        self.url = ""
        self.shift.save()
        self.scanner.reset()
        self.client.reset()
        self.shift = Shift(StepType.Fill)
