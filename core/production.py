from datetime import datetime
import queue

from core.enums import StepType

class Shift():
    def __init__(self, firstStepType): 
        self.date = datetime.now()
        self.steps = queue.Queue()
        self.currentStep = Step(firstStepType)
        self.lastStep = Step(StepType.Nope)
        self.steps.put(self.currentStep)
    
    def step(self, nextStepType):
        self.currentStep.stop = datetime.now()
        self.currentStep.duration = self.currentStep.stop - self.currentStep.start
        self.lastStep = self.currentStep
        self.currentStep = Step(nextStepType)
        self.steps.put(self.currentStep)
        
    def save(self):
        self.currentStep.stop = datetime.now()
        self.currentStep.duration = self.currentStep.stop - self.currentStep.start
        # serialize and save or send somewhere

class Step():
    def __init__(self, stepType):
        self.start = datetime.now()
        self.stop = 0
        self.duration = 0
        self.type = stepType
        