from datetime import datetime
import queue

from core.enums import StepType

class Shift():
    def __init__(self, first_step_type): 
        self.date = datetime.now()
        self.steps = queue.Queue()
        self.current_step = Step(first_step_type)
        self.last_step = Step(StepType.Nope)
        self.steps.put(self.current_step)
    
    def step(self, next_step_type):
        self.current_step.stop = datetime.now()
        self.current_step.duration = self.current_step.stop - self.current_step.start
        self.last_step = self.current_step
        self.current_step = Step(next_step_type)
        self.steps.put(self.current_step)
        
    def save(self):
        self.current_step.stop = datetime.now()
        self.current_step.duration = self.current_step.stop - self.current_step.start
        # serialize and save or send to somewhere

class Step():
    def __init__(self, stepType):
        self.start = datetime.now()
        self.stop = 0
        self.duration = 0
        self.type = stepType
        