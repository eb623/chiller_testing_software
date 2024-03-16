# General imports
import os
import glob
import time
from datetime import datetime

# Signal imports
import spidev
import RPi.GPIO as GPIO       # for flow pin

# Data management imports
import numpy as np
import csv

# [EDIT] fix so csv not all at the end
ALL_AT_ONCE = 1

# Fluid dictionary
# formatted as following: "liquid": [fluid_weight, specific_heat]
fluid_dict = {
    "Water": [8.344, 1],
}

class Gen_Info:
    def __init__(self):
        self.model = []         
        self.dop = []           # date of production
        self.dot = []           # date of test
        self.tester = []        
        self.test_fluid = []    
    
    def load_from_csv(self, file_name):
        # Open file
        file = open(file_name)
        csv_raw = csv.reader(file)

        # Read first line (Gen_info)
        header= []
        header = next(csv_raw)
        file.close()

        # Extract information from header
        values = []
        for item in header:
            split = item.split("=")
            values.append(split[1])
        
        # Put information in Gen_info
        self.model = values[0]         # CHECK FOR VALIDITY?
        self.dop = Gen_Info.create_date(values[1])
        self.dot = Gen_Info.create_date(values[2])
        self.tester = values[3]
        self.test_fluid = values[4]    # CHECK FOR VALIDITY?
    
    def load_from_input(self, model, dop, dot, tester, test_fluid):
        self.model = model
        self.dop = dop
        self.dot = dot
        self.tester = tester
        self.test_fluid = test_fluid
    
    @staticmethod
    def create_date(string):
        # Extract numbers
        date = string.split("-")
        month = date[0]
        day = date[1]
        year = date[2]

        return(datetime.date(int(year), int(month), int(day)))

class Data: # shared between testing and PS program
    def __init__(self):
        self.time = []      # duration of test
        self.temp_in = []
        self.temp_out = []
        self.temp_amb = []
        self.flow = []
        self.cc = []       # cooling capacity

# Pressure classes
class Homemade_port_1:
    def __init__(self):
        self.pin1 = 8   # cs
        self.pin2 = 10  # mosi (unneeded, Pmod AD1 only uses MISO)
        self.pin3 = 9   # miso
        self.pin4 = 11  # clk

class Homemade_port_2:
    def __init__(self):
        self.pin1 = 18  # cs
        self.pin2 = 20  # mosi (unneeded, Pmod AD1 only uses MISO)
        self.pin3 = 19  # miso
        self.pin4 = 21  # clk

class PmodAD1:
    def __init__(self, port):
        self.port = port
        self.cs = self.port.pin1
        self.d0 = self.port.pin2    # mosi
        self.d1 = self.port.pin3    # miso
        self.clk = self.port.pin4
        
        self.spi = spidev.SpiDev()
        self.__startSPI()
       
    def __startSPI(self):
        if self.cs == 18: #CE0, SPI1
            self.spi.open(1,0)
        elif self.cs == 8: #CE0, SPI0
            self.spi.open(0,0)
        else:
            #[EDIT add error here]
            return
        self.spi.max_speed_hz = 100000  # [EDIT should i change this?]
        self.spi.mode = 0b00
        
    def __stopSPI(self):
        self.spi.close()   
    
    def __spiRead16(self):
            resp = self.spi.xfer2([0x00, 0x00])
            w = resp[0] 
            w <<= 8
            w |= resp[1]
            return w
    
    def readA1(self):
            return self.__spiRead16()
    
    def readA1Volts(self):
            w = self.__spiRead16()
            
            refV = 3.3
            lsb =  refV/4096
            volts= w*lsb
            
            return volts
 
    def cleanup(self):
            self.__stopSPI()

class Active_Data(Data):
    # file defs for temp sensors
    base_dir = '/sys/bus/w1/devices/'
    device_folder1 = glob.glob(base_dir + '28*')[0] # first sensor on right
    device_file1 = device_folder1 + '/w1_slave'
    device_folder2 = glob.glob(base_dir + '28*')[1] # last sensor on left
    device_file2 = device_folder2 + '/w1_slave'
    device_folder3 = glob.glob(base_dir + '28*')[2] # middle sensor
    device_file3 = device_folder3 + '/w1_slave'
    device_folder4 = glob.glob(base_dir + '28*')[3] # 
    device_file4 = device_folder4 + '/w1_slave'
    #device_folder5 = glob.glob(base_dir + '28*')[4] # 
    #device_file5 = device_folder5 + '/w1_slave'

    # constants for flow
    BUTTON_GPIO1 = 16
    #BUTTON_GPIO2 = 26
    FEP1 = 27 # GPM (set on the flow sensor, max flow rate)
    FRP1 = 1000 # Hz (set on the flow sensor, max frequency)

    # Set-up for pressure sensor
    port1 = Homemade_port_1()
    port2 = Homemade_port_2()
    adc1 = PmodAD1(port1)
    adc2 = PmodAD1(port2)

    def __init__(self, fluid):
        # Data class inheritance + raw values
        super().__init__()
        self.temp1 = []
        self.temp2 = []
        self.temp3 = []
        self.temp4 = []
        #self.temp5 = []
        self.flow1 = []
        #self.flow2 = []
        self.pressure1 = []
        self.pressure2 = []

        # Calculation constants
        w, s = fluid_dict[fluid]
        self.fluid_weight = w   # lbs/gal
        self.specific_heat = s  # BTU/lb*F

        # Sample count
        self.sample_count = 0

        # Global constants (modifiable as needed)
        self.units = 1      # 0 for celsius, 1 for farenheight
        self.avg_val = 10   # number of raw values averaged to get one value

        # Flow frequency counts
        self.count1 = 0
        #self.count2 = 0

        # For duration calculation
        self.start_time = datetime.now()

        # Set up flow pins
        Active_Data.set_up_flow(self)
        self.prev_time = datetime.now()

    def set_up_flow(self):
        # callbacks to count rising edges of frequency signals from flow sensors        
        def my_callback1(channel):
            self.count1 += 1

        #def my_callback2(channel):
        #    self.count2 += 1

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.BUTTON_GPIO1, GPIO.IN) 
        GPIO.add_event_detect(self.BUTTON_GPIO1, GPIO.RISING, callback=my_callback1) # sets up interrupt for rising edge

        #GPIO.setmode(GPIO.BCM)
        #GPIO.setup(self.BUTTON_GPIO2, GPIO.IN)
        #GPIO.add_event_detect(self.BUTTON_GPIO2, GPIO.RISING, callback=my_callback2)
    
    @staticmethod
    def read_temp_raw(device_file): # reads off the pin
        f = open(device_file, 'r')
        lines = f.readlines()
        f.close()
        return lines

    @staticmethod 
    def read_temp(device_file):
        lines = Active_Data.read_temp_raw(device_file)
        equals_pos = lines[1].find('t=')

        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp_c = float(temp_string) / 1000.0
            temp_f = temp_c * 9.0 / 5.0 + 32.0
            return temp_c, temp_f

    def temp_reading(self):
        temp1c, temp1f = Active_Data.read_temp(Active_Data.device_file1)
        temp2c, temp2f = Active_Data.read_temp(Active_Data.device_file2)
        temp3c, temp3f = Active_Data.read_temp(Active_Data.device_file3)
        temp4c, temp4f = Active_Data.read_temp(Active_Data.device_file4)
        #temp5c, temp5f = Active_Data.read_temp(Active_Data.device_file5)

        if (self.units):                    # if farenheight
            self.temp1.append(temp1f)
            self.temp2.append(temp2f)
            self.temp3.append(temp3f)
            self.temp4.append(temp4f)
            #self.temp5.append(temp5f)
        else:                               # if celsius
            self.temp1.append(temp1f)
            self.temp2.append(temp2f)
            self.temp3.append(temp3f)
            self.temp4.append(temp4f)
            #self.temp5.append(temp5f)
    
    def get_flow(self): # gets freq from pulse count, flow rate from freq
        # Calculate time span of current measurement
        cur_time = datetime.now()
        dif = cur_time - self.prev_time
        time_span = dif.total_seconds()
        self.prev_time = datetime.now()

        # calculate frequency
        freq1 = self.count1/time_span
        #freq2 = self.count2/time_span
        self.count1 = 0
        #self.count2 = 0

        # calculate flow - the % of the FRP1 = the % of the FEP1
        per_freq1 = freq1/Active_Data.FRP1
        #per_freq2 = freq2/Active_Data.FRP1
        flow_rate1 = Active_Data.FEP1*per_freq1
        #flow_rate2 = Active_Data.FEP1*per_freq2
        self.flow1.append(flow_rate1)
        #self.flow2.append(flow_rate2)
    
    def get_pressure(self):
        # Read voltage inputs
        #Active_Data.adc1 = PmodAD1(Active_Data.port1) [EDIT take out if unneeded]
        volts1 = Active_Data.adc1.readA1Volts()
        #Active_Data.adc2 = PmodAD1(Active_Data.port2)
        volts2 = Active_Data.adc1.readA1Volts()

        # Calculate pressure [EDIT add 0 protection, error, etc.]
        pres1 = 41.7*volts1-32
        pres2 = 41.7*volts2-32
        self.pressure1.append(pres1)
        self.pressure2.append(pres2)
    
    def calculate_cc(self):
        i = self.sample_count # index
        
        # Calculate cooling capacity
        cc = self.fluid_weight*self.specific_heat*self.flow[i]*60*abs(self.temp_in[i]-self.temp_out[i])
        self.cc.append(cc)
    
    def average(self):
        # Temp variables
        temp_temp_in = 0
        temp_temp_out = 0
        temp_temp_amb = 0
        temp_flow = 0

        # Average values
        for i in range(self.sample_count-self.avg_val, self.sample_count):
            temp_temp_in += (self.temp3[i]+self.temp4[i])/2
            temp_temp_out += (self.temp1[i]+self.temp5[i])/2
            temp_temp_out += self.temp1[i]
            temp_temp_amb += self.temp2[i]
            temp_flow += (self.flow1[i]+self.flow2[i])/2
            temp_flow += self.flow1[i]
        
        self.temp_in.append(temp_temp_in/self.avg_val)
        self.temp_out.append(temp_temp_out/self.avg_val)
        self.temp_amb.append(temp_temp_amb/self.avg_val)
        self.flow.append(temp_flow/self.avg_val)

    def take_measurement(self):
        self.temp_reading()
        self.get_flow()
        self.get_pressure()

        # Averaging
        if (self.sample_count >= self.avg_val):
            self.average()
            self.calculate_cc()
        else:
            self.temp_in.append(0)
            self.temp_out.append(0)
            self.temp_amb.append(0)
            self.flow.append(0)
            self.cc.append(0)
        
        # Update time and sample count
        self.sample_count += 1
        cur_time = datetime.now()
        dif = cur_time - self.start_time
        self.time.append(dif.total_seconds())

class Test_Info:
    def __init__(self, model, dop, fluid, dot, tester, runtime):
        self.gen_info = Gen_Info()
        Gen_Info.load_from_input(self.gen_info, model, dop, dot, tester, fluid)
        self.runtime = runtime
        self.file = self.create_file_name(model)
        self.active_data = Active_Data(fluid)
        self.start = 0

    @staticmethod
    def create_file_name(model):
        # create filename from model and test date
        path = "tests/"
        cur_time = datetime.now().strftime("%m_%d_%I-%M-%S")
        file_name = path+model+"_test_data_"+cur_time+".csv"
        return(file_name)
    
    def start_test(self):
        self.start_csv()
        self.active_data.start_time = datetime.now()
    
    def run_test(self):
        Active_Data.take_measurement(self.active_data)            

        # [EDIT to take out]
        i = self.active_data.sample_count-1
        print("Temp_1: ", self.active_data.temp3[i], "   Temp_2: ", self.active_data.temp4[i], "  Temp_3: ", self.active_data.temp1[i], "  Temp_4: ", self.active_data.temp5[i], "  Temp_5: ", self.active_data.temp5[i], "  Flow1: ", self.active_data.flow1[i], "  Flow2: ", self.active_data.flow2[i], "  Pressure1: ", self.active_data.pressure1[i], "  Pressure2: ", self.active_data.pressure2[i])
        print("Temp_in: ", self.active_data.temp_in[i], "   Temp_out: ", self.active_data.temp_out[i], "   Temp_amb: ", self.active_data.temp_amb[i], "   Flow: ", self.active_data.flow[i], "   CC: ", self.active_data.cc[i])
        
        # [EDIT fix w async stuff]
        if (ALL_AT_ONCE == 0):
            if (self.active_data.sample_count % 60 == 0):
                self.add_csv()
    
    def start_csv(self):
        # Open/Create File
        f = open(self.file, "w")

        # print gen_info
        model = self.gen_info.model
        dop = self.gen_info.dop
        dot = self.gen_info.dot
        tester = self.gen_info.tester
        fluid = self.gen_info.test_fluid
        f.write(model+","+str(dop)+","+str(dot)+","+tester+","+fluid+"\n")

        # print headers for data
        #f.write("Time(s),TempIn(F),TempInR(F),TempInAvg(F),TempOut(F),TempOutR(F),TempOutAvg(F),TempAmb(F),TempAmbAvg(F),Flow1(gpm),Flow2(gpm),FlowAvg(gpm),Pressure1(psi),Pressure2(psi),CoolingCapacity(BTU/hr)\n")
        f.write("Time(s),TempIn(F),TempInR(F),TempInAvg(F),TempOut(F),TempOutAvg(F),TempAmb(F),TempAmbAvg(F),Flow1(gpm),FlowAvg(gpm),Pressure1(psi),Pressure2(psi),CoolingCapacity(BTU/hr)\n")
        f.close()
    
    def add_csv(self):
        end = len(self.active_data.temp1)
        f = open(self.file, "a")

        if (ALL_AT_ONCE):
            self.start = 0

        for i in range(self.start, end):
            time_s = str(self.active_data.time[i])+","
            temp_in_s = str(self.active_data.temp3[i])+","+str(self.active_data.temp4[i])+","+str(self.active_data.temp_in[i])
            #temp_out_s = ","+str(self.active_data.temp1[i])+","+str(self.active_data.temp5[i])+","+str(self.active_data.temp_out[i])
            temp_out_s = ","+str(self.active_data.temp1[i])+","+str(self.active_data.temp_out[i])
            temp_amb_s = ","+str(self.active_data.temp2[i])+","+str(self.active_data.temp_amb[i])
            #flow_s = ","+str(self.active_data.flow1[i])+","+str(self.active_data.flow2[i])+","+str(self.active_data.flow[i])
            flow_s = ","+str(self.active_data.flow1[i])+","+str(self.active_data.flow[i])
            pres_s = ","+str(self.active_data.pressure1[i])+","+str(self.active_data.pressure2[i])
            cc_s = ","+str(self.active_data.cc[i])+"\n"
            f.write(time_s+temp_in_s+temp_out_s+temp_amb_s+flow_s+pres_s+cc_s)
        
        f.close()

        self.start = end