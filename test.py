from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sys


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("QRadioButton")

        # tạo một QGroupBox instance để chứa các QRadioButton
        groupbox = QGroupBox("Options")

        layout = QVBoxLayout()

        for i in range(3):
            # tạo QRadioButton instance với text "Option #"
            opt = QRadioButton(f"Option #{i}")

            # kết nối signal clicked và slot
            opt.pressed.connect(lambda x=i: print(f"option #{x} is chosen"))

            # thêm QRadioButton instance vào layout
            layout.addWidget(opt)

        # cài đặt layout cho QGroupBox instance
        groupbox.setLayout(layout)

        self.setCentralWidget(groupbox)


app = QApplication(sys.argv)
window = MainWindow()
window.show()

app.exec()