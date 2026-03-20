from PyQt6.QtWidgets import QMainWindow
from GUI.Qt import Ui_MainWindow
from PyQt6.QtCore import QTimer
from core.enums import Input, MistakeType, StepType
from core.worker import Worker
from GUI import styles

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, arguments, *args, obj=None, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.mistake_msg.hide()
        
        self.worker = Worker(arguments)
        
        self.timer = QTimer()
        self.timer.setInterval(200)
        self.timer.timeout.connect(self.cycle)
        self.timer.start()
        
        self.show()    
    
    def cycle(self):
        self.worker.work()
        self.tip_msg.setText(self.worker.message)

        self.lable_RH1.setStyleSheet(styles.INDICATOR[self.worker.input[Input.RH1.value]])
        self.lable_RH1.setText("RH 1 " + styles.INDICATOR_TEXT[self.worker.input[Input.RH1.value]])

        self.label_RH2.setStyleSheet(styles.INDICATOR[self.worker.input[Input.RH2.value]])
        self.label_RH2.setText("RH 2 " + styles.INDICATOR_TEXT[self.worker.input[Input.RH2.value]])

        self.label_LH1.setStyleSheet(styles.INDICATOR[self.worker.input[Input.LH1.value]])
        self.label_LH1.setText("LH 1 " + styles.INDICATOR_TEXT[self.worker.input[Input.LH1.value]])

        self.label_LH2.setStyleSheet(styles.INDICATOR[self.worker.input[Input.LH2.value]])
        self.label_LH2.setText("LH 2 " + styles.INDICATOR_TEXT[self.worker.input[Input.LH2.value]])

        self.label_PCB1.setText(self.worker.pcb1)
        self.label_PCB2.setText(self.worker.pcb2)
        self.label_heat.setText(self.worker.heatsink)

        if self.worker.mistake.value and not self.worker.reset_count and not (self.worker.error or self.worker.client.error):
            if self.worker.mistake in (MistakeType.AddedAfterStart, MistakeType.MoreThanOneTaken):
                self.mistake_msg.setStyleSheet(styles.POPUP_MESSAGE[styles.RED])
            else:
                self.mistake_msg.setStyleSheet(styles.POPUP_MESSAGE[styles.YELLOW])
            self.mistake_msg.setText("ACCION INCORRECTA!\n\n" + self.worker.mistakeMsg)
            self.mistake_msg.show()
        else:
            self.mistake_msg.hide()
            if self.worker.reset_count:
                self.tip_msg.setStyleSheet(styles.MESSAGE[styles.YELLOW])
            elif self.worker.error or self.worker.client.error:
                self.tip_msg.setStyleSheet(styles.MESSAGE[styles.RED])
            else:
                self.tip_msg.setStyleSheet(styles.MESSAGE[styles.BLUE])

        self.btn_fill.setChecked(not self.btn_fill.isChecked() and self.worker.shift.currentStep.type == StepType.Fill and not self.worker.error)
        self.btn_pick.setChecked(not self.btn_pick.isChecked() and self.worker.shift.currentStep.type == StepType.Pick and not self.worker.error)
        self.btn_scan_1.setChecked(not self.btn_scan_1.isChecked() and self.worker.shift.currentStep.type == StepType.Scan and not self.worker.error)
        self.btn_scan_2.setChecked(not self.btn_scan_2.isChecked() and self.worker.shift.currentStep.type == StepType.Scan and not self.worker.error)
        self.btn_print.setChecked(not self.btn_print.isChecked() and self.worker.shift.currentStep.type == StepType.Print and not self.worker.error)
        self.btn_scan_3.setChecked(not self.btn_scan_3.isChecked() and self.worker.shift.currentStep.type == StepType.Scan and not self.worker.error)
        self.btn_valid.setChecked(not self.btn_valid.isChecked() and self.worker.shift.currentStep.type == StepType.Valid and not self.worker.error)