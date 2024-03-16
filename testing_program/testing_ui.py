import sys
import os
from PyQt5.QtWidgets import * 
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import * 
from PyQt5.QtCore import *
import pyqtgraph as pg

from testing_program import Test_Info

# User input window sizes
UWINDOW_SIZE = 880
UDISPLAY_HEIGHT = 480

# Graph window sizes
WINDOW_SIZE = 1920       # 1920 for screen
DISPLAY_HEIGHT = 1020    # 1080 for screen

# All done window sizes
AWINDOW_SIZE = 680
ADISPLAY_HEIGHT = 280

class WidgetGallery(QDialog):
    def __init__(self, parent=None):
        super(WidgetGallery, self).__init__(parent)

        self.setWindowTitle("Chillerz Testing")
        self.setFixedSize(UWINDOW_SIZE, UDISPLAY_HEIGHT)

        self.create_intro()
        self.create_chiller_info()
        self.create_test_info()

        topLayout = QHBoxLayout()
        topLayout.addWidget(self.intro)
        topLayout.addStretch(1)

        button = QPushButton("Run Test")
        button.clicked.connect(self.TestClick)

        mainLayout = QGridLayout()
        mainLayout.addLayout(topLayout, 0, 0, 1, 2)
        mainLayout.addWidget(self.chiller_info, 1, 0)
        mainLayout.addWidget(self.test_info, 1, 1)
        mainLayout.addWidget(button, 2, 1)
        mainLayout.setRowStretch(1, 1)
        mainLayout.setRowStretch(2, 1)
        mainLayout.setColumnStretch(0, 1)
        mainLayout.setColumnStretch(1, 1)
        self.setLayout(mainLayout)
    
    def create_intro(self):
        self.intro = QGroupBox()

        intro_text = QLabel("Welcome!", alignment=Qt.AlignmentFlag.AlignCenter)
        how_to = QLabel("Fill in the categories below with the relevant information, then click \"Run Test\" when you're ready.\n")
        note = QLabel("Note: it may take a few moments for the test to begin after you click \"Run Test\"")
        # [EDIT more info]

        layout = QGridLayout()
        layout.addWidget(intro_text)
        layout.addWidget(how_to)
        layout.addWidget(note)
        self.intro.setLayout(layout)
    
    def create_chiller_info(self):
        self.chiller_info = QGroupBox("Chiller Information")

        model_label = QLabel("Chiller Model:")
        model_num = QLineEdit('OC-25RO') # [EDIT change to combo box w all models?]

        dop_label = QLabel("Date of Production:")   # [EDIT use maximumDateTime to set limits?]
        dateEdit = QDateEdit(self.chiller_info)
        dateEdit.setDisplayFormat("MM dd yyyy")
        dateEdit.setDate(QDate.currentDate())

        self.model_num = model_num
        self.dop = dateEdit

        layout = QGridLayout()
        layout.addWidget(model_label, 1, 0, 1, 2)
        layout.addWidget(model_num, 1, 1, 1, 2)
        layout.addWidget(dop_label, 2, 0, 1, 2)
        layout.addWidget(dateEdit, 2, 1, 1, 2)
        layout.setRowStretch(5, 1)
        self.chiller_info.setLayout(layout)


    def create_test_info(self):
        self.test_info = QGroupBox("Testing Information")

        fluid_label = QLabel('Test Fluid: ')
        fluid_type = QComboBox()
        fluid_type.addItems(['Water'])


        dot_label = QLabel('Date of Test: ')
        dateEdit = QDateEdit(self.test_info)
        dateEdit.setDisplayFormat("MM dd yyyy")
        dateEdit.setDate(QDate.currentDate())

        tester_label = QLabel('Tester: ')
        tester = QLineEdit('')

        runtime_label = QLabel('Run time (min): ')
        runtime = QLineEdit('60')

        self.fluid_type = fluid_type
        self.dot = dateEdit
        self.tester = tester
        self.runtime = runtime

        layout = QGridLayout()
        layout.addWidget(fluid_label, 1, 0, 1, 2)
        layout.addWidget(fluid_type, 1, 1, 1, 2)
        layout.addWidget(dot_label, 2, 0, 1, 2)
        layout.addWidget(dateEdit, 2, 1, 1, 2)
        layout.addWidget(tester_label, 3, 0, 1, 2)
        layout.addWidget(tester, 3, 1, 1, 2)
        layout.addWidget(runtime_label, 4, 0, 1, 2)
        layout.addWidget(runtime, 4, 1, 1, 2)

        layout.setRowStretch(5, 1)
        self.test_info.setLayout(layout)
    
    def TestClick(self, s):
        print("Run Test clicked", s)

        model = self.model_num.text()
        dop = self.dop.date().toPyDate()
        fluid = self.fluid_type.currentText()
        dot = self.dot.date().toPyDate()
        tester = self.tester.text()
        runtime = int(self.runtime.text())

        self.hold = HoldTight()                
        self.graph_win = GraphWindow(model, dop, fluid, dot, tester, runtime)
        self.hold.close()
        self.close()

class HoldTight(QWidget):
    def __init__(self, parent=None):
        super(HoldTight, self).__init__(parent)

        self.setWindowTitle("Initiating test")

        mainLayout = QGridLayout()
        hold_tight = QLabel('Please wait while the test initializes...')
        mainLayout.addWidget(hold_tight)
        self.setLayout(mainLayout)
        self.show()

class GraphWindow(QDialog):
    def __init__(self, model, dop, fluid, dot, tester, runtime, parent=None):
        super(GraphWindow, self).__init__(parent)

        self.setWindowTitle("Graphical Display")
        self.setFixedSize(WINDOW_SIZE, DISPLAY_HEIGHT)

        self.count = 0
        self.test = Test_Info(model, dop, fluid, dot, tester, runtime)

        self.time = []
        self.temp_in = []
        self.temp_out = []
        self.temp_amb = []
        self.pres1 = 0
        self.pres2 = 0
        self.cc = []

        self.cc_graph()
        self.temp_graph()
        self.value_widgets_l()
        self.value_widgets_r()

        mainLayout = QGridLayout()
        mainLayout.addWidget(self.cc_graph, 1, 0)
        mainLayout.addWidget(self.temp_graph, 1, 1)
        mainLayout.addWidget(self.v_widgetsl, 2, 0)
        mainLayout.addWidget(self.v_widgetsr, 2, 1)
        self.setLayout(mainLayout)

        self.test.start_test()
        while (self.count <= 10):
            self.test.run_test()
            self.time = self.test.active_data.time
            self.count += 1
        
        self.show()
        self.timer = QtCore.QTimer()
        self.timer.setInterval(5000)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()
    
    def cc_graph(self):
        self.cc_graph = pg.PlotWidget()
        self.cc_graph.setBackground("w")
        self.cc_graph.setTitle("Cooling Capacity vs Time", color="b", size="20pt")
        styles = {"color": "red", "font-size": "18px"}
        self.cc_graph.setLabel("left", "Cooling Capacity (BTU/hr)", **styles)
        self.cc_graph.setLabel("bottom", "Time (s)", **styles)
        self.cc_graph.addLegend()
        self.cc_graph.showGrid(x=True, y=True)
        self.cc_graph.setYRange(0, 100000)

        # CC graph
        pen = pg.mkPen(color=(255, 0, 0))
        self.cc_g = self.cc_graph.plot(
            self.time,
            self.cc,
            name="Cooling Capacity",
            pen=pen,
            symbol="o",
            symbolSize=15,
            symbolBrush="r",
        )
  
    def temp_graph(self):
        self.temp_graph = pg.PlotWidget()
        self.temp_graph.setBackground("w")
        self.temp_graph.setTitle("Temperature vs Time", color="b", size="20pt")
        styles = {"color": "red", "font-size": "18px"}
        self.temp_graph.setLabel("left", "Temperature (°F)", **styles)
        self.temp_graph.setLabel("bottom", "Time (s)", **styles)
        self.temp_graph.addLegend()
        self.temp_graph.showGrid(x=True, y=True)
        self.temp_graph.setYRange(0, 100)

        # Temp In
        pen = pg.mkPen(color=(255, 0, 0))
        self.temp_in_line = self.temp_graph.plot(
            self.time,
            self.temp_in,
            name="Temperature In",
            pen=pen,
            symbol="+",
            symbolSize=15,
            symbolBrush="r",
        )

        # Temp Out
        pen = pg.mkPen(color=(0, 255, 0))
        self.temp_out_line = self.temp_graph.plot(
            self.time,
            self.temp_out,
            name="Temperature Out",
            pen=pen,
            symbol="+",
            symbolSize=15,
            symbolBrush="g",
        )

        # Temp Amb
        pen = pg.mkPen(color=(0, 0, 255))
        self.temp_amb_line = self.temp_graph.plot(
            self.time,
            self.temp_amb,
            name="Ambient Temp",
            pen=pen,
            symbol="+",
            symbolSize=15,
            symbolBrush="b",
        )
    
    def value_widgets_l(self):
        self.v_widgetsl = QGroupBox("Values")

        temp_in_label = QLabel('Temperature In')
        temp_out_label = QLabel('Temperature Out')
        cc_label = QLabel('Cooling Capacity')

        self.temp_in_w = QLabel('0 F')
        self.temp_out_w = QLabel('0 F')
        self.cc_w = QLabel('0 BTU/hr')
        
        layout = QGridLayout()
        layout.addWidget(temp_in_label, 0, 0)
        layout.addWidget(temp_out_label, 0, 1)
        layout.addWidget(cc_label, 0, 2)
        layout.addWidget(self.temp_in_w, 1, 0)
        layout.addWidget(self.temp_out_w, 1, 1)
        layout.addWidget(self.cc_w, 1, 2)

        self.v_widgetsl.setLayout(layout)
    
    def value_widgets_r(self):
        self.v_widgetsr = QGroupBox("Values")

        pres1 = QLabel('Pressure 1')
        pres2 = QLabel('Pressure 2')
        drop = QLabel('Pressure Drop')

        self.pres1_w = QLabel('0 psi')
        self.pres2_w = QLabel('0 psi')
        self.drop_w = QLabel('0 psi')

        layout = QGridLayout()
        layout.addWidget(pres1, 0, 0)
        layout.addWidget(pres2, 0, 1)
        layout.addWidget(drop, 0, 2)
        layout.addWidget(self.pres1_w, 1, 0)
        layout.addWidget(self.pres2_w, 1, 1)
        layout.addWidget(self.drop_w, 1, 2)

        self.v_widgetsr.setLayout(layout)
    
    def update_plot(self):
        # Updating values
        self.test.run_test()
        self.time = self.test.active_data.time
        cur_time = self.test.active_data.time[len(self.test.active_data.time)-1]
        self.temp_in = self.test.active_data.temp_in
        self.temp_out = self.test.active_data.temp_out
        self.temp_amb = self.test.active_data.temp_amb
        self.pres1 = self.test.active_data.pressure1[self.count]
        self.pres2 = self.test.active_data.pressure2[self.count]
        self.cc = self.test.active_data.cc

        # Update Widgets
        self.temp_in_w.setText(str(round(self.temp_in[self.count], 2))+' F')
        self.temp_out_w.setText(str(round(self.temp_out[self.count], 2))+' F')
        self.cc_w.setText(str(round(self.cc[self.count], 2))+' BTU/hr')
        self.pres1_w.setText(str(round(self.pres1, 2))+' psi')
        self.pres2_w.setText(str(round(self.pres2, 2))+' psi')
        drop_p = abs(self.pres1-self.pres2)
        # [EDIT threshold check]
        self.drop_w.setText(str(round(drop_p, 2))+' psi')
        self.count += 1

        # Updating graphs
        self.cc_g.setData(self.time, self.cc)
        self.temp_in_line.setData(self.time, self.temp_in)
        self.temp_out_line.setData(self.time, self.temp_out)
        self.temp_amb_line.setData(self.time, self.temp_amb)

        # Check for runtime
        if (cur_time > self.test.runtime*60):
            self.timer.stop()
            self.test.add_csv()
            #self.test.active_data.adc1.cleanup()
            #self.test.active_data.adc2.cleanup()
            self.all_done = AllDone(self.test.file)
            self.close()

class AllDone(QDialog):
    def __init__(self, file_name, parent=None):
        super(AllDone, self).__init__(parent)

        self.setWindowTitle("Test complete")
        self.setFixedSize(AWINDOW_SIZE, ADISPLAY_HEIGHT)

        layout = QVBoxLayout()
        self.file_name = file_name

        string = "Test data is saved a .csv file called "+file_name+"\nTo transfer this file to a USB,\n"+"plug a USB into the Raspberry Pi and hit the \"Transfer\" button when ready."
        filename = QLabel(string)
        button = QPushButton("Transfer")
        button.clicked.connect(self.TransferClick)

        layout.addWidget(filename)
        layout.addWidget(button)

        self.setLayout(layout)
        self.show()
    
    def TransferClick(self, s):
        print("Tranfer clicked", s)
        os.system('sudo mount /dev/sda1 /media/usb -o uid=pi,gid=pi')
        string = "cp "+self.file_name+" /media/usb"
        os.system(string)
        os.system('sudo umount /media/usb')
        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    gallery = WidgetGallery()
    gallery.show()
    sys.exit(app.exec())