# General imports
import os
import glob
import time
from datetime import datetime

# Data management imports
import numpy as np
from numpy import genfromtxt
import csv

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

class Active_Data(Data):
    def __init__(self, fluid):
        # Data class inheritance + raw values
        super().__init__()
        self.temp1 = []
        self.temp2 = []
        self.temp3 = []
        self.temp4 = []
        self.temp5 = []
        self.flow1 = []
        self.flow2 = []
        self.pressure1 = []
        self.pressure2 = []

        self.data = []
        self.load_data()

        # Calculation constants  [EDIT to be determined by user input]
        w, s = fluid_dict[fluid]
        self.fluid_weight = w   # lbs/gal
        self.specific_heat = s  # BTU/lb*F


        # Sample count
        self.sample_count = 0

        # Global constants (modifiable as needed)
        self.avg_val = 10   # number of raw values averaged to get one value

        # For duration calculation
        self.start_time = datetime.now()
    
    def load_data(self):
        file_name = "gen_data.csv"
        data = genfromtxt(file_name, delimiter=',', dtype=float)
        self.data = data

    def temp_reading(self):
        i = self.sample_count
        self.temp1.append(self.data[i, 0])
        self.temp2.append(self.data[i, 1])
        self.temp3.append(self.data[i, 2])
        self.temp4.append(self.data[i, 3])
        self.temp5.append(self.data[i, 4])
    
    def get_flow(self): # gets freq from pulse count, flow rate from freq
        i = self.sample_count
        self.flow1.append(self.data[i, 5])
        self.flow2.append(self.data[i, 6])
    
    def get_pressure(self):
        i = self.sample_count
        self.pressure1.append(self.data[i, 7])
        self.pressure2.append(self.data[i, 8])
    
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

        # Average temperatures
        for i in range(self.sample_count-self.avg_val, self.sample_count):
            temp_temp_in += (self.temp3[i]+self.temp4[i])/2
            temp_temp_out += (self.temp1[i]+self.temp5[i])/2
            temp_temp_amb += self.temp2[i]
            temp_flow += (self.flow1[i]+self.flow2[i])/2
        
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
        
        if (self.active_data.sample_count % 10 == 0):
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
        f.write("Time(s),TempIn(F),TempInR(F),TempInAvg(F),TempOut(F),TempOutR(F),TempOutAvg(F),TempAmb(F),TempAmbAvg(F),Flow1(gpm),Flow2(gpm),FlowAvg(gpm),Pressure1(psi),Pressure2(psi),CoolingCapacity(BTU/hr)\n")
        f.close()
    
    def add_csv(self):
        end = len(self.active_data.temp1)
        f = open(self.file, "a")

        for i in range(self.start, end):
            time_s = str(self.active_data.time[i])+","
            temp_in_s = str(self.active_data.temp3[i])+","+str(self.active_data.temp4[i])+","+str(self.active_data.temp_in[i])
            temp_out_s = ","+str(self.active_data.temp1[i])+","+str(self.active_data.temp5[i])+","+str(self.active_data.temp_out[i])
            temp_amb_s = ","+str(self.active_data.temp2[i])+","+str(self.active_data.temp_amb[i])
            flow_s = ","+str(self.active_data.flow1[i])+","+str(self.active_data.flow2[i])+","+str(self.active_data.flow[i])
            pres_s = ","+str(self.active_data.pressure1[i])+","+str(self.active_data.pressure2[i])
            cc_s = ","+str(self.active_data.cc[i])+"\n"
            f.write(time_s+temp_in_s+temp_out_s+temp_amb_s+flow_s+pres_s+cc_s)
        
        f.close()

        self.start = end
