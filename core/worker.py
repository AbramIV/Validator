import logging
import requests
from core.enums import Input, MistakeType, Output, StepType
from core.hardware import USB5860, Scanner
from core.http import HttpClient
from core.production import Shift
import threading

MAX_POSITIONS_COUNT = 4

DEVICE_DESCRIPTION = "USB-5860,BID#0"
PROFILE_PATH = u"../../profile/USB-5860.xml"

class Worker():
    def __init__(self, ip):
        self.logger = logging.getLogger("__main__")
        
        self.scanner = Scanner()
        self.client = HttpClient()
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
        self.IP = ip
        self.qr1 = ""
        self.qr2 = ""
        self.qr3 = ""
        self.side = ""
        self.url = ""
        self.mistake = MistakeType.Nope
        self.error = False

        try:
            self.device = USB5860(DEVICE_DESCRIPTION, PROFILE_PATH)
        except Exception as ex:
            self.logger.error("Advantech USB-5860 init error: " + str(ex))
            self.message = "Advantech USB-5860 init error!"
        
        self.scanner_thread = threading.Thread(target=self.scanner.scan, daemon=True)
        self.scanner_thread.start()

        self.client_thread = threading.Thread(target=self.client.get, daemon=True)

    def work(self):
        if not self.poll(): return
        
        if self.shift.currentStep.type == StepType.Fill:
            if self.sensors_sum == MAX_POSITIONS_COUNT:
                self.client.error = False
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
                if  self.sensors_sum > self.sensors_last_sum: 
                    self.mistake = MistakeType.AddedAfterStart
                    self.mistakeMsg = "No devuelva las piezas, finalice el proceso!\nElige uno parte para continuar!"
                if (self.sensors_last_sum - self.sensors_sum) == 1:   
                    if self.input[Input.TopLeft.value] != self.last_input[Input.TopLeft.value]:
                        self.message = "Esta parte de la izquierda!\n"
                        self.side = "LH"
                    elif self.input[Input.BottomLeft.value] != self.last_input[Input.BottomLeft.value]:
                        self.message = "Esta parte de la izquierda!\n"
                        self.side = "LH"
                    elif self.input[Input.TopRight.value] != self.last_input[Input.TopRight.value]:
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
            if self.sensors_last_sum != self.sensors_sum:
                if self.sensors_last_sum > self.sensors_sum:
                    self.mistake = MistakeType.MoreThanOneTaken
                    self.mistakeMsg = "No extraiga la pieza hasta que haya terminado el último proceso!\nInstalar todos partes para continuar!"
                else:
                    self.mistake = MistakeType.AddedAfterStart
                    self.mistakeMsg = "No devuelva las piezas, finalice el proceso!\nElige uno parte para continuar!"
                self.clear()
            
            if self.scanner.isScanned:
                if self.scanCount == 0:
                    self.qr1 = "".join(self.scanner.buffer)
                    self.message = "Escanear el codigo 2!"
                    self.scanCount += 1
                elif self.scanCount == 1:
                    self.qr2 = "".join(self.scanner.buffer)
                    if self.qr1 == self.qr2:
                        self.mistake = MistakeType.CodeScannedTwice
                        self.mistakeMsg = "Escaneaste lo mismo! Escanea el segundo codigo QR!" 
                    else:
                        self.url = f"http://{self.IP}/Route/to/Define?productSerial1={self.qr1}&productSerial2={self.qr2}&side={self.side}"
                        self.mistake = MistakeType.Nope
                        self.shift.step(StepType.Validate)
                        self.message = "Validacion, espera..."
                        self.scanCount += 1
                else:
                    self.qr3 = "".join(self.scanner.buffer)
                    if self.qr3 in (self.qr1, self.qr2):
                        self.mistake = MistakeType.CodeScannedTwice
                        self.mistakeMsg = "Escaneó el código de la pieza. ¡Escanee el código impreso!"
                    else:
                        self.url = f"http://{self.IP}/Route/to/Define?productSerial={self.qr3}&side={self.side}"
                        self.mistake = MistakeType.Nope
                        self.scanCount = 0
                        self.shift.step(StepType.Validate)
                        self.message = "Validacion, espera..."
                self.scanner.reset()
                self.last_input = self.input
                return
                       
        if self.shift.currentStep.type == StepType.Validate:
            if self.validateCount < 1:
                if self.client.get(self.url):
                    if self.is_valid():
                        if self.client.code == requests.codes.ok:
                            self.device.setOutput(Output.Print.value)
                            self.message = "Escanear el codigo impreso!"
                            self.shift.step(StepType.Scan)
                            self.validateCount += 1      
                        else:
                            self.logger.warning(self.client.message)
                            if self.sensors_sum == 0:
                                self.message = "No valido! Instalar todos partes."
                                self.shift.save()
                                self.shift = Shift(StepType.Fill)
                            else:
                                self.shift = Shift(StepType.Pick)
                                self.message = "No valido! Elige uno parte."            
                else:
                    if self.is_valid():
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
                    if self.is_valid():    
                        if self.client.code == requests.codes.ok:
                            if self.sensors_sum == 0: 
                                self.shift = Shift(StepType.Fill)
                                self.message = "Instalar todos partes."
                            else: 
                                self.shift = Shift(StepType.Pick)
                                self.message = "Elige uno parte!"
                        else:
                            if self.sensors_sum == 0:
                                self.message = "No valido! Instalar todos partes."
                                self.shift.save()
                                self.shift = Shift(StepType.Fill)
                            else:
                                self.shift = Shift(StepType.Pick)
                                self.message = "No valido! Elige uno parte." 
                else: 
                    if self.is_valid():
                        self.logger.error(self.client.message)                    
                        if self.sensors_sum == 0:
                            self.shift.save()
                            self.message = "HTTP pedido error!\nContactar con soporte O\ninstalar todos para continuar!"
                            self.shift = Shift(StepType.Fill)
                        else:
                            self.message = "HTTP pedido error!\nContactar con soporte O\nelige uno parte para continuar!"
                            self.shift = Shift(StepType.Pick)
        
        self.last_input = self.input

    def is_valid(self):
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
            self.sensors_sum = self.input[Input.TopLeft.value] + self.input[Input.BottomLeft.value] + self.input[Input.TopRight.value] + self.input[Input.BottomRight.value]
            self.output = self.device.readOutputsAsList()
            self.reset = self.input[Input.Reset.value]
            if self.output[Output.Print.value]:
                self.device.resetOutput(Output.Print.value)
            self.error = False
        except Exception as ex:
            self.clear()
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
