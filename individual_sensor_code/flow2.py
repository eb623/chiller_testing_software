# Imports
import time
import RPi.GPIO as GPIO

# Set-up pins
BUTTON_GPIO1 = 16
BUTTON_GPIO2 = 26

# global count
count1 = 0
count2 = 0

# Set values
FEP1 = 27 # GPM
FRP1 = 1000 #0 # Hz

# function counting, dependent on if port is rising
def my_callback1(channel):
    # increment count
    global count1
    count1 = count1 + 1

def my_callback2(channel):
    # increment count
    global count2
    count2 = count2 + 1

# function that runs every ~.5 second to grab count, reset it, calculate freq
def get_freq1(wait_time):
    global count1
    freq = count1/wait_time
    count1 = 0
    return(freq)

def get_freq2(wait_time):
    global count2
    freq = count2/wait_time
    count2 = 0
    return(freq)

# function to calculate flow from frequency
def get_flow(freq):
    # the % of the FRP1 = the % of the FEP1
    per_freq = freq/FRP1
    flow = FEP1*per_freq
    return(flow)


def main():
    # Set up pins 1
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON_GPIO1, GPIO.IN) # down bc i think flow "pulls" up to 1, rather than down to 0
    GPIO.add_event_detect(BUTTON_GPIO1, GPIO.RISING, callback=my_callback1)#, bouncetime=1) # sets up interrupt for rising edge

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON_GPIO2, GPIO.IN) # down bc i think flow "pulls" up to 1, rather than down to 0
    GPIO.add_event_detect(BUTTON_GPIO2, GPIO.RISING, callback=my_callback2)

    wait_time = 1

    while True:
        time.sleep(wait_time)
        # Pin 1
        print("Count1: ", count1, "    Count2: ", count2)
        freq1 = get_freq1(wait_time)
        freq2 = get_freq2(wait_time)
        flow1 = get_flow(freq1)
        flow2 = get_flow(freq2)
        print("Freq1: ", freq1, "    Freq2: ", freq2)
        print("Flow rate1: ", flow1, "GPM    Flow rate2: ", flow2, "\n")


if __name__ == '__main__':
    main()
