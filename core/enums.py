from enum import Enum

class StepType(Enum):
    Insert = 0
    Pick = 1
    Scan_PCB_1 = 2
    Scan_PCB_2 = 3
    Valid_PCB = 4
    Print = 5
    Scan_Heatsink = 6
    Valid_Heatsink = 7
    Nope = 8
    
class Input(Enum):
    RH1 = 2
    RH2 = 3
    LH1 = 0
    LH2 = 1
    Button = 4
    Reserve_5 = 5
    Reserve_6 = 6
    Reserve_7 = 7
    
class Output(Enum):
    Reserve_0 = 0
    Reserve_1 = 1
    Reserve_2 = 2
    Reserve_3 = 3
    Reserve_4 = 4
    Reserve_5 = 5
    Reserve_6 = 6
    Reserve_7 = 7
    
class MistakeType(Enum):
    Nope = 0
    MoreThanOneTaken = 1
    AddedAfterStart = 2
    CodeScannedTwice = 3
    PrintedCodeInvalid = 4
