from PyQt6.QtWidgets import QMainWindow
from GUI.Qt import Ui_MainWindow
from PyQt6.QtCore import QTimer
from core.enums import Input, MistakeType
from core.worker import Worker
from GUI import styles

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, arguments, *args, obj=None, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.mistakeMsg.hide()
        
        self.worker = Worker(arguments)
        
        self.timer = QTimer()
        self.timer.setInterval(200)
        self.timer.timeout.connect(self.cycle)
        self.timer.start()
        
        self.show()    
    
    def cycle(self):  
        self.worker.work()

        self.tipMsg.setText(self.worker.message)
        self.tipMsg.setStyleSheet(styles.MESSAGE[self.worker.error or self.worker.client.error])
        if self.worker.error or self.worker.client.error:
            self.mistakeMsg.hide()

        self.lable_RH1.setStyleSheet(styles.INDICATOR[self.worker.input[Input.RH1.value]])
        self.lable_RH1.setText("RH 1 " + styles.INDICATOR_TEXT[self.worker.input[Input.RH1.value]])

        self.label_RH2.setStyleSheet(styles.INDICATOR[self.worker.input[Input.RH2.value]])
        self.label_RH2.setText("RH 2 " + styles.INDICATOR_TEXT[self.worker.input[Input.RH2.value]])

        self.label_LH1.setStyleSheet(styles.INDICATOR[self.worker.input[Input.LH1.value]])
        self.label_LH1.setText("LH 1 " + styles.INDICATOR_TEXT[self.worker.input[Input.LH1.value]])

        self.label_LH2.setStyleSheet(styles.INDICATOR[self.worker.input[Input.LH2.value]])
        self.label_LH2.setText("LH 2 " + styles.INDICATOR_TEXT[self.worker.input[Input.LH2.value]])

        if self.worker.mistake.value: 
            if self.worker.mistake in (MistakeType.AddedAfterStart, MistakeType.MoreThanOneTaken):
                self.mistakeMsg.setStyleSheet(styles.BACKGROUND[styles.RED])
            else:
                self.mistakeMsg.setStyleSheet(styles.BACKGROUND[styles.YELLOW])   
            self.mistakeMsg.setText(self.worker.mistakeMsg)
            self.mistakeMsg.show()
        else:
            self.mistakeMsg.hide()
