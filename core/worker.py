
import requests
from core.enums import Input, MistakeType, Output, StepType
from core.hardware import USB5860, Scanner
from core.http import HttpClient
from core.production import Shift
import threading

class Worker():  
    def __init__(self, logger, ip):
        self.logger = logger
        
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
        self.url = ""
        self.mistake = MistakeType.Nope
        self.error = False
        self.side = ""
        
        try:
            self.device = USB5860("USB-5860,BID#0", u"../../profile/USB-5860.xml")
        except Exception as ex:
            self.logger.error("Advantech USB-5860 init error: " + str(ex))
            self.message = "Advantech USB-5860 init error!"
        
        threading.Thread(target=self.scanner.scan, daemon=True).start()

    def work(self):
        self.poll()
        
        if self.error: return
        
        if self.shift.currentStep.type == StepType.Fill:
            if self.sensors_sum == 4:
                self.client.error = False
                self.shift.nextStep(StepType.Pick)
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
                    elif self.input[Input.BottomLeft.value]!= self.last_input[Input.BottomLeft.value]:
                        self.message = "Esta parte de la izquierda!\n"
                        self.side = "LH"
                    elif self.input[Input.TopRight.value] != self.last_input[Input.TopRight.value]:
                        self.message = "Esta parte de la derecha!\n"
                        self.side = "RH"
                    else:
                        self.message = "Esta parte de la derecha!\n"
                        self.side = "RH"
                    self.shift.nextStep(StepType.Scan)
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
                self.scanner.reset()
                self.message = ""
                self.scanCount = 0
                self.qr1 = ""
                self.qr2 = ""
                self.url = ""
                self.shift.nextStep(StepType.Fill)
            
            if self.scanner.isScanned:
                self.scanCount += 1
                if self.scanCount == 1:
                    self.qr1 = "".join(self.scanner.buffer)
                    self.message = "Escanear el codigo 2!"
                elif self.scanCount == 2:
                    self.qr2 = "".join(self.scanner.buffer)
                    if self.qr1 == self.qr2:
                        self.mistake = MistakeType.CodeScannedTwice
                        self.mistakeMsg = "Escaneaste lo mismo! Escanea el segundo codigo QR!" 
                        self.scanCount -= 1
                    else:
                        self.url = f"http://{self.IP}/Route/to/Define?productSerial1={self.qr1}&productSerial2={self.qr2}&side={self.side}"
                        self.mistake = MistakeType.Nope
                        self.shift.nextStep(StepType.Validate)
                        self.message = "Validacion, espera..."
                else:
                    self.qr3 = "".join(self.scanner.buffer)
                    if self.qr3 in (self.qr1, self.qr2):
                        self.mistake = MistakeType.CodeScannedTwice
                        self.mistakeMsg = "Escaneó el código de la pieza. ¡Escanee el código impreso!"
                        self.scanCount -= 1
                    else:
                        self.url = f"http://{self.IP}/Route/to/Define?productSerial={self.qr3}&side={self.side}"
                        self.mistake = MistakeType.Nope
                        self.scanCount = 0
                        self.shift.nextStep(StepType.Validate)
                        self.message = "Validacion, espera..." 
                self.scanner.reset()
                return
                       
        if self.shift.currentStep.type == StepType.Validate:
            self.validateCount += 1
            if self.validateCount == 1:
                if self.client.get(self.url):
                    if self.client.response.status_code == requests.codes.ok:
                        self.device.setOutput(Output.Print.value)
                        self.message = "Escanear el codigo impreso!"
                        self.shift.nextStep(StepType.Scan)
                    else:
                        if self.sensors_sum == 0:
                            self.message = "No valido! Instalar todos partes."
                            self.shift.save()
                            self.shift = Shift(StepType.Fill)
                        else:
                            self.shift = Shift(StepType.Pick)
                            self.message = "No valido! Elige uno parte."            
                else:
                    self.logger.error(self.client.errorMsg)
                    self.message = "HTTP pedido error!\nContactar con soporte O\ninstalar todos para continuar!"
                    self.shift.save()
                    self.shift = Shift(StepType.Fill)
            else:
                self.client.get(self.url)
                print(self.client.response.status_code)
                if self.client.error:
                    self.logger.error(self.client.errorMsg)                    
                    if self.sensors_sum == 0:
                        self.shift.save()
                        self.message = "HTTP pedido error!\nContactar con soporte O\ninstalar todos para continuar!"
                        self.shift = Shift(StepType.Fill)
                    else:
                        self.message = "HTTP pedido error!\nContactar con soporte O\nelige uno parte para continuar!"
                        self.shift = Shift(StepType.Pick)
                else: 
                    if self.client.response.status_code == 200:
                        if self.sensors_sum == 0: self.shift = Shift(StepType.Fill)
                        else: self.shift = Shift(StepType.Pick)
                    else:
                        if self.sensors_sum == 0:
                            self.message = "No valido! Instalar todos partes."
                            self.shift.save()
                            self.shift = Shift(StepType.Fill)
                        else:
                            self.shift = Shift(StepType.Pick)
                            self.message = "No valido! Elige uno parte."

        self.last_input = self.input

    def poll(self):
        try:
            self.input = self.device.readInputsAsList()
            self.sensors_sum = self.input[Input.TopLeft.value] + self.input[Input.BottomLeft.value] + self.input[Input.TopRight.value] + self.input[Input.BottomRight.value]
            self.output = self.device.readOutputsAsList()
            self.reset = self.input[Input.Reset.value]
            if self.output[Output.Print.value]:
                self.device.resetOutput(Output.Print.value)

            if self.error:
                self.clear()
                self.error = False
        except Exception as ex:
            self.error = True
            self.message = "Advantech USB-5860 encuesta error!"
            self.logger.error("Advantech USB-5860 request error: " + str(ex))
            if self.device.isDisposed:
                self.device = USB5860("USB-5860,BID#0", u"../../profile/USB-5860.xml")
            
    def clear(self):
        self.sensors_last_sum = 0
        self.scanCount = 0
        self.validateCount = 0
        self.qr1 = ""
        self.qr2 = ""
        self.qr3 = ""
        self.url = ""
        self.message = ""
        self.mistake = MistakeType.Nope
        self.shift.save()
        self.shift = Shift(StepType.Fill)