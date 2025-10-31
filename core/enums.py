from enum import Enum

class StepType(Enum):
    Fill = 0
    Pick = 1
    Scan = 2
    Validate = 4
    Restore = 7
    Nope = 8
    
class Input(Enum):
    TopLeft = 2
    BottomLeft = 3
    TopRight = 0
    BottomRight = 1
    Reset = 4
    Reserve_5 = 5
    Reserve_6 = 6
    Reserve_7 = 7
    
class Output(Enum):
    Print = 0
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
    IP = 0
    Port = 1
    Nope = 2
    