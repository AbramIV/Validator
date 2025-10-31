from PyQt6.QtWidgets import QMainWindow
from GUI.Qt import Ui_MainWindow
from PyQt6.QtCore import QTimer
from core.enums import Input, MistakeType
from core.worker import Worker
from GUI import styles

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, ip, *args, obj=None, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.mistakeMsg.hide()
        
        self.worker = Worker(ip)
        
        self.timer = QTimer()
        self.timer.setInterval(200)
        self.timer.timeout.connect(self.cycle)
        self.timer.start()
        
        self.show()    
    
    def cycle(self):  
        self.worker.work()

        self.tipMsg.setText(self.worker.message)

        if not self.worker.error:
            self.tipMsg.setStyleSheet(styles.TEXT_BOX[styles.BLUE])

        self.lable_tl.setStyleSheet(styles.INDICATOR[self.worker.input[Input.TopLeft.value]])
        self.lable_tl.setText(styles.INDICATOR_TEXT[self.worker.input[Input.TopLeft.value]])

        self.label_bl.setStyleSheet(styles.INDICATOR[self.worker.input[Input.BottomLeft.value]])
        self.label_bl.setText(styles.INDICATOR_TEXT[self.worker.input[Input.BottomLeft.value]])

        self.label_tr.setStyleSheet(styles.INDICATOR[self.worker.input[Input.TopRight.value]])
        self.label_tr.setText(styles.INDICATOR_TEXT[self.worker.input[Input.TopRight.value]])

        self.label_br.setStyleSheet(styles.INDICATOR[self.worker.input[Input.BottomRight.value]])
        self.label_br.setText(styles.INDICATOR_TEXT[self.worker.input[Input.BottomRight.value]])
        
        if self.worker.mistake.value: 
            if self.worker.mistake in (MistakeType.AddedAfterStart, MistakeType.MoreThanOneTaken):
                self.mistakeMsg.setStyleSheet(styles.TEXT_BOX[styles.RED])
            else:
                self.mistakeMsg.setStyleSheet(styles.TEXT_BOX[styles.YELLOW])   
            self.mistakeMsg.setText(self.worker.mistakeMsg)
            self.mistakeMsg.show()
        else:
            self.mistakeMsg.hide()
        
        if self.worker.error or self.worker.client.error:
            self.mistakeMsg.hide()
            self.tipMsg.setStyleSheet(styles.TEXT_BOX[styles.RED])
        