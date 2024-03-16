import csv
import datetime
import numpy as np              # pip3 install numpy
import matplotlib.pyplot as plt # pip3 install matplotlib

from docxtpl import DocxTemplate, InlineImage # pip3 install docxtpl
from docx.shared import Mm

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
            values.append(item) 
        
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
        month = date[1]
        day = date[2]
        year = date[0]

        return(datetime.date(int(year), int(month), int(day)))

class Data:
    def __init__(self): # note -- ensure only floats?
        self.time = []
        self.temp_in = []
        self.temp_out = []
        self.temp_amb = []
        self.flow = []
        self.cc = []

class Passive_Data(Data):
    def __init__(self, file):
        super().__init__()
        self.file_name = file # string

        Passive_Data.load_csv(self)
    
    def load_csv(self):
        # Open file
        file = open(self.file_name)
        csv_raw = csv.reader(file)

        # Extract the headers
        header= []
        header = next(csv_raw)
        header = next(csv_raw)
        
        # Load the data values
        data = []
        for row in csv_raw:
            data.append(row)
        file.close()
        
        # Convert into np array
        data_np = np.array(data)
        data_fl = data_np.astype(float)

        # Store data
        self.time = data_fl[:, 0]
        self.temp_in = data_fl[:, 3]
        self.temp_out = data_fl[:, 6]
        self.temp_amb = data_fl[:, 7]
        self.flow = data_fl[:, 10]
        self.cc = data_fl[:, 14]

class PS_Info():
    template = "PST_template.docx"
    def __init__(self, file):
        self.file_name = file                               # filename
        self.data = Passive_Data(self.file_name)
        self.gen_info = Gen_Info()
        self.gen_info.load_from_csv(self.file_name)
        self.graph_cc = PS_Info.create_cc_graph(self)       # filename
        self.graph_temp = PS_Info.create_temp_graph(self)   # filename
        self.filled_pst = PS_Info.generate_ps(self)         # filename
    
    def create_cc_graph(self):
        # Extract relevant data
        time = self.data.time
        cc = self.data.cc

        # Plot graph
        plt.plot(time, cc)
        plt.title("Cooling Capacity vs Time")
        plt.grid()
        plt.xlabel("Time (s)")
        plt.ylabel("Cooling Capacity (BTU/hr)")

        # Create png name
        date_string = self.gen_info.dot.strftime('%Y-%m-%d')
        graph_name = "graphs/"+self.gen_info.model+"_"+date_string+"_cc_graph.png"

        # save graph as .png
        plt.savefig(graph_name)
        return(graph_name)
    
    def create_temp_graph(self):
        # Extract relevant data
        time = self.data.time
        temp_in = self.data.temp_in
        temp_out = self.data.temp_out
        temp_amb = self.data.temp_amb

        # Plot graph
        plt.figure()
        plt.plot(time, temp_in, label = "Temperature In") 
        plt.plot(time, temp_out, label = "Temperature Out") 
        plt.plot(time, temp_amb, label = "Ambient Temperature")
        plt.legend() 
        plt.title("Temperature vs Time")
        plt.grid()
        plt.xlabel("Time (s)")
        plt.ylabel("Temperature (F)")

        # Create png name
        date_string = self.gen_info.dot.strftime('%Y-%m-%d')
        graph_name = "graphs/"+self.gen_info.model+"_"+date_string+"_temp_graph.png"

        # save graph as .png
        plt.savefig(graph_name)
        return(graph_name) 
    
    def generate_ps(self):
        # Set-Up
        template = DocxTemplate(PS_Info.template)
        cc_graph = InlineImage(template, self.graph_cc, height=Mm(90), width=Mm(90))
        temp_graph = InlineImage(template, self.graph_temp, height=Mm(90), width=Mm(90))
        avg_in = round(np.average(self.data.temp_in), 2)
        avg_out = round(np.average(self.data.temp_out), 2)
        avg_amb = round(np.average(self.data.temp_amb), 2)
        avg_flow = round(np.average(self.data.flow), 2)
        avg_cc = round(np.average(self.data.cc), 2)

        context = {
            "MODEL": self.gen_info.model,
            "DOP": self.gen_info.dop.strftime("%Y-%m-%d"),
            "FLUID": self.gen_info.test_fluid,
            "AVG_IN": avg_in,
            "AVG_OUT": avg_out,
            "AVG_AMB": avg_amb,
            "AVG_FLOW": avg_flow,
            "AVG_CC": avg_cc,
            "DOT": self.gen_info.dot.strftime("%Y-%m-%d"),
            "TESTER": self.gen_info.tester,
            "PLACE_HOLDER1": cc_graph,
            "PLACE_HOLDER2": temp_graph,
        }
        template.render(context)

        date_string = self.gen_info.dot.strftime('%Y-%m-%d')
        PS_name = "performance_sheets/"+self.gen_info.model+"_"+date_string+"_PS.docx"
        template.save(PS_name)
        return(PS_name)
        

if __name__ == '__main__':
    test = 3
    if (test == 1):
        pdata1 = Passive_Data("tests/test_data.csv")
        print(pdata1.temp_in)
    elif (test == 2):
        gi1 = Gen_Info("tests/test_data.csv")
        print(gi1.model, gi1.dop, gi1.dot, gi1.tester, gi1.test_fluid)
    elif(test == 3):
        file = "tests/test_data.csv"
        PS1 = PS_Info(file)