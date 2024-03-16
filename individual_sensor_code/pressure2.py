import time
from datetime import datetime
import spidev
CAP = 'SPI'
PHY = '1x6'

class PmodAD1:
    
    def __init__(self, DSPMod6):
        
        self.port = DSPMod6
        self.cs = self.port.pin1
        self.d0 = self.port.pin2
        self.d1 = self.port.pin3 #miso
        self.clk = self.port.pin4
        
        self.spi = spidev.SpiDev()
        self.__startSPI()
       
    def __startSPI(self):
        if self.cs == 18: #CE0, SPI1
            self.spi.open(1,0)
        elif self.cs == 8: #CE0, SPI0
            self.spi.open(0,0)
        else:
            #throw exception here
            return
        self.spi.max_speed_hz = 100000
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

class Homemade_port_1:
    def __init__(self):
        self.pin1 = 8 # 24 # cs
        self.pin2 = 10 # 19 # mosi
        self.pin3 = 9 # 21 # miso
        self.pin4 = 11 # 23 # clk

class Homemade_port_2:
    def __init__(self):
        self.pin1 = 18   # cs
        self.pin2 = 20  # mosi
        self.pin3 = 19   # miso
        self.pin4 = 21  # clk

def save_csv(file_name, volts1, pres1, volts2, pres2):
    f = open(file_name, "a")
    f.write(str(volts1)+","+str(pres1)+","+str(volts2)+","+str(pres2)+"\n")
    f.close()    

if __name__ == '__main__':
    port1 = Homemade_port_1()
    port2 = Homemade_port_2()

    # Set up file name
    path = "tests/"
    cur_time = datetime.now().strftime("%m-%d-%I:%M:%S")
    file_name = path+cur_time+"pressure_data.csv"

    # Set up file
    f = open(file_name, "w")
    f.write("Voltage1(V),Pressure1(psi),Voltage2(V),Pressure2(psi)\n")
    f.close()

    time.sleep(1)
    
    try:
        while True:
            adc1 = PmodAD1(port1)
            volts1 = adc1.readA1Volts()
            adc2 = PmodAD1(port2)
            volts2 = adc2.readA1Volts()
            
            if (round(volts1, 4) < .72):   # from the formula derived during calibration
                pres1 = 0
            else :
                pres1 = 69.444*volts1-50

            if (round(volts2, 4) < .72):   # from the formula derived during calibration
                pres2 = 0
            else :
                pres2 = 69.444*volts2-50

            print("Volts1: ", round(volts1, 4), "  Pressure1: ", round(pres1, 4), "Volts2: ", round(volts2, 4), "Pressure2: ", round(pres2, 4), "\n")
            save_csv(file_name, volts1, pres1, volts2, pres2)
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        adc1.cleanup()
        adc2.cleanup()
