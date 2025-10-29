import sys, os
from Automation.BDaq import *
from Automation.BDaq.InstantDiCtrl import InstantDiCtrl
from Automation.BDaq.InstantDoCtrl import InstantDoCtrl
from Automation.BDaq.BDaqApi import AdxEnumToString, BioFailed
from pynput.keyboard import Key, Listener
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

class USB5860():
    def __init__(self, deviceDescription, profilePath):
        self.isBusy = False
        self.isDisposed = True
        self.isDisposing = False
        
        try:
            self.instantDiCtrl = InstantDiCtrl(deviceDescription)
            self.instantDiCtrl.loadProfile = profilePath
            self.instantDoCtrl = InstantDoCtrl(deviceDescription)
            self.instantDoCtrl.loadProfile = profilePath
            self.isDisposed = False
        except Exception as ex:
            ConnectionError(f"An error occurred: {ex}")
        
    def readInputsAsDec(self, start = 0, port = 1):
        error, data = self.instantDiCtrl.readAny(start, port)

        if BioFailed(error):
            enumStr = AdxEnumToString("Read inputs ErrorCode", error.value, 256)
            raise RuntimeError("Error code " + str(error.value) + " " + str(enumStr))
        elif data.__len__ == 0:
            raise ValueError("No values.")
        else:
            return data[0]
        
    def readInputsAsList(self, start = 0, port = 1): 
        di = [(self.readInputsAsDec(start, port) >> i) & 1 for i in range(8 - 1, -1, -1)]
        di.reverse()
        return di
    
    def readInput(self, bit):
        error, bit = self.instantDiCtrl.readBit(0, bit)

        if BioFailed(error):
            enumStr = AdxEnumToString("Read inputs ErrorCode", error.value, 256)
            raise RuntimeError("Some error occurred. And the last error code is %#x. [%s]" % (error.value, enumStr)) 
        else:
            return bit
    
    def readOutputsAsDec(self, start = 0, port = 1):
        error, data = self.instantDoCtrl.readAny(start, port)

        if BioFailed(error):
            enumStr = AdxEnumToString("Read outputs ErrorCode", error.value, 256)
            raise RuntimeError("Some error occurred. And the last error code is %#x. [%s]" % (error.value, enumStr)) 
        else:
            return data[0]
      
    def readOutputsAsList(self, start = 0, port = 1):
        do = [(self.readOutputsAsDec(start, port) >> i) & 1 for i in range(8 - 1, -1, -1)]
        do.reverse()
        return do
        
    def readOutput(self, bit):
        error, bit = self.instantDoCtrl.readBit(0, bit)

        if BioFailed(error):
            enumStr = AdxEnumToString("Read inputs ErrorCode", error.value, 256)
            raise RuntimeError("Some error occurred. And the last error code is %#x. [%s]" % (error.value, enumStr)) 
        else:
            return bit
      
    def writeOutputsAsDec(self, value = 0):
        error = self.instantDoCtrl.writeAny(0, 1, [value])    
        
        if BioFailed(error):
            enumStr = AdxEnumToString("Write outputs ErrorCode", error.value, 256)
            raise RuntimeError("Some error occurred. And the last error code is %#x. [%s]" % (error.value, enumStr)) 
            
    def writeOutput(self, bit, value):
        error = self.instantDoCtrl.writeBit(0, bit, value)

        if BioFailed(error):
            enumStr = AdxEnumToString("Write output ErrorCode", error.value, 256)
            raise RuntimeError("Some error occurred. And the last error code is %#x. [%s]" % (error.value, enumStr)) 
        else:
            return bit
     
    def setOutput(self, bit):
        self.writeOutput(bit, 1)
    
    def resetOutput(self, bit):
        self.writeOutput(bit, 0)
      
    def dispose(self):
        if self.isDisposed: return
        
        self.instantDiCtrl.dispose()
        self.instantDoCtrl.dispose()
        self.isDisposing = False
        self.isDisposed = True
        
class Scanner():
    def __init__(self):
        self.isScanned = False
        self.buffer = []
                
    def on_press(self, key):
        if key in (Key.shift, None): return True
        if key == Key.enter:
            self.isScanned = True
            return True
        try:
            self.buffer.append(key.char)
        except AttributeError:
            pass
        return True

    def scan(self):
        with Listener(on_press=self.on_press) as listener:
            listener.join()
    def reset(self):
        self.isScanned = False
        self.buffer.clear()