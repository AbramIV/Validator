from enum import Enum

class StepType(Enum):
    Fill = 0
    Pick = 1
    Scan = 2
    Print = 3
    Valid = 4
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

class AppArguments(Enum):
    IP1 = 0
    Port1 = 1
    IP2 = 2
    Port2 = 3
    Nope = 4
    
class PrinterStatus(Enum):
    Normal = 0x00
    HeadOpened = 0x01
    PaperJam = 0x02
    PaperJamAndHeadOpened = 0x03
    OutOfPaper = 0x04
    OutOfPaperAndHeadOpened = 0x05
    OutOfRibbon = 0x08
    OutOfRibbonAndHeadOpened = 0x09
    OutOfRibbonAndPaperJam = 0x0A
    OutOfRibbonPaperJamAndHeadOpened = 0x0B 
    OutOfRibbonAndOutOfPaper = 0x0C
    OutOfRibbonOutOfPaperAndHeadOpened = 0x0D
    Pause = 0x10
    Printing = 0x20
    OtherError = 0x80
    RequestError = 0x110
    Nope = 0x120

class PrinterCommand(Enum):
    Reset = "\x1B!C"
    Status = "\x1B!?"