# five sensors in series to one gpio pin

import os
import glob
import time
from datetime import datetime
 
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
 
base_dir = '/sys/bus/w1/devices/'
device_folder1 = glob.glob(base_dir + '28*')[0] # first sensor on right
device_file1 = device_folder1 + '/w1_slave'
device_folder2 = glob.glob(base_dir + '28*')[1] # last sensor on left
device_file2 = device_folder2 + '/w1_slave'
device_folder3 = glob.glob(base_dir + '28*')[2] # middle sensor
device_file3 = device_folder3 + '/w1_slave'
device_folder4 = glob.glob(base_dir + '28*')[3] # 
device_file4 = device_folder4 + '/w1_slave'
device_folder5 = glob.glob(base_dir + '28*')[4] # 
device_file5 = device_folder5 + '/w1_slave'

units = 1 # 0 for celsius, 1 for farenheight

class Temperature:
    def __init__(self):
        self.temp1 = []
        self.temp2 = []
        self.temp3 = []
        self.temp4 = []
        self.temp5 = []
    
    def update_temp(self, temp1, temp2, temp3, temp4, temp5):
        self.temp1.append(temp1)
        self.temp2.append(temp2)
        self.temp3.append(temp3)
        self.temp4.append(temp4)
        self.temp5.append(temp5)
 
def read_temp_raw(device_file):
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines
 
def read_temp(device_file):
    lines = read_temp_raw(device_file)
    while lines[0].strip()[-3:] != 'YES':
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return temp_c, temp_f

def print_temp(temp1, temp2, temp3, temp4, temp5):
    print("Temp1=", temp1, " Temp2=", temp2, " Temp3=", temp3, " Temp4=", temp4, " Temp5=", temp5, "\n")

def reading(file_name, temps):
    temp1c, temp1f = read_temp(device_file1)
    temp2c, temp2f = read_temp(device_file2)
    temp3c, temp3f = read_temp(device_file3)
    temp4c, temp4f = read_temp(device_file4)
    temp5c, temp5f = read_temp(device_file5)

    if (units): # if farenheight
        print_temp(temp1f, temp2f, temp3f, temp4f, temp5f)
        temps.update_temp(temp1f, temp2f, temp3f, temp4f, temp5f)
    else:   # if celsius
        print_temp(temp1c, temp2c, temp3c, temp4c, temp5c)
        temps.update_temp(temps, temp1c, temp2c, temp3c, temp4c, temp5c)

def save_csv(file_name, temps):
    temp1 = temps.temp1
    temp2 = temps.temp2
    temp3 = temps.temp3
    temp4 = temps.temp4
    temp5 = temps.temp5

    f = open(file_name, "w")
    f.write("Temp1,Temp2,Temp3,Temp4,Temp5\n")

    for i in range(len(temp1)):
        f.write(str(temp1[i])+","+str(temp2[i])+","+str(temp3[i])+","+str(temp4[i])+","+str(temp5[i])+"\n")
    
    f.close()
    

if __name__ == '__main__':
    path = "tests/"
    cur_time = datetime.now().strftime("%m-%d-%I:%M:%S")
    file_name = path+cur_time+"temp5_data.csv"

    f = open(file_name, "w")
    f.write("Temp1,Temp2,Temp3,Temp4,Temp5\n")
    f.close()

    temps = Temperature()
    
    try:
        while True:
            reading(file_name, temps)
            time.sleep(.8)
    except KeyboardInterrupt:
        pass
    finally:
        save_csv(file_name, temps)
