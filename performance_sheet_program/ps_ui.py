import sys
import os
from PyQt5.QtWidgets import * 
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import * 
from PyQt5.QtCore import *

from performance_sheet_program import PS_Info

WINDOW_SIZE = 720       # 1920 for screen
DISPLAY_HEIGHT = 480    # 1080 for screen
BUTTON_SIZE = 100

class Window(QMainWindow):
    def __init__(self):
        super().__init__(parent=None)
        self.setWindowTitle("Chillerz Testing")
        self.setFixedSize(WINDOW_SIZE, WINDOW_SIZE)
        self._createMenu()
        self._createToolBar()
        self._createStatusBar()

        centralWidget = QWidget(self)
        textLabel = QLabel(centralWidget)
        textLabel.setText("Welcome to the Turmoil performance sheet application, to be used with the chiller test system software")
        self.setCentralWidget(centralWidget)

    def _createMenu(self):
        menu = self.menuBar().addMenu("&Menu")
        menu.addAction("&Exit", self.close)

    def _createToolBar(self):
        tools = QToolBar()
        
        # Database
        button_action = QAction("Database", self)
        button_action.setStatusTip("This is your button") #delete?
        button_action.triggered.connect(self.DatabaseClick)
        tools.addAction(button_action)

        # Run PS
        button_action = QAction("Run PS", self)
        button_action.setStatusTip("This is your button") #delete?
        button_action.triggered.connect(self.PSClick)
        tools.addAction(button_action)

        tools.addAction("Exit", self.close)

        self.addToolBar(tools)
    
    def DatabaseClick(self, s):
        print("Database clicked", s)
    
    def PSClick(self, s):
        print("PS clicked", s)
        file_name = str(self.getFileName())
        file = "tests/"+file_name
        per_sheet = PS_Info(file)
        print(per_sheet.filled_pst)
        # [EDIT add notif w filename that it was created successfully]

    def _createStatusBar(self):
        status = QStatusBar()
        status.showMessage("I'm the Status Bar")
        self.setStatusBar(status) 
    
    def _createButtons(self):
        self.buttonMap = {}
        buttonsLayout = QHBoxLayout()
        keyBoard = ["Test Database", "Performance Sheet"]

        for col, key in enumerate(keyBoard):
            self.buttonMap[key] = QPushButton(key)
            self.buttonMap[key].setFixedSize(BUTTON_SIZE, BUTTON_SIZE)
            buttonsLayout.addWidget(self.buttonMap[key], col)
        
        self.generalLayout.addLayout(buttonsLayout)
    
    def getFileName(self):
        file_filter = 'Data File (*.xlsx *.csv *.dat);; Excel File (*.xlsx *.xls);; Image File (*.png *.jpg)'
        response = QFileDialog.getOpenFileName(
            parent=self,
            caption='Select a file',
            directory=os.getcwd(),
            filter=file_filter,
            initialFilter='Data File (*.xlsx *.csv *.dat)'
        )
        file_path = response[0]
        split_path = file_path.split("/")
        x = len(split_path)
        return(str(split_path[x-1]))

if __name__ == "__main__":
    app = QApplication([])
    window = Window()
    window.show()

    sys.exit(app.exec())