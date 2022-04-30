
from distutils.log import Log
import time
import RPi.GPIO as GPIO
from base64 import encode
import serial
import os
import glob
import csv




#IMU_CMD = ("$VNWRG,6,19,2*BEE3\r\n".encode())
ATTITUDE_CMD = ("$VNRRG,8*4B\r\n".encode()) #new one thats not async $VNRRG,8*040E
TARE_CMD = ("$VNTAR*D235\r\n".encode())



IMU_DATALOG_Title = "IMU_Datalog.csv"
ATTITUDE_DATALOG_TITLE = "Attitude_Datalog.csv"




CH1 = 5
CH2 = 6


TimeStart = 0

headerIMU = ["Time", "MagX", "MagY", "MagZ", "AccelX", "AccelY", "AccelZ", "GyroX", "GyroY", "GyroZ", "Temp", "Pressure"]
headerATTITUDE = ["Time", "Pitch", "Yaw", "Roll"]

#nav setup#
serNAV = serial.Serial(
        port='/dev/ttyAMA0',
        baudrate = 230400,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=0.001 #smallest delay tested that results in no data dropout
)

def PollReceiver(channel):

    stop = 0
    start = 0
    state = 0

    #get start and stop time of pulse
    while GPIO.input(channel) == 0:
        start = time.time()

    while GPIO.input(channel) == 1:
        stop = time.time()
    
    #get total pulse width
    elapsed = (stop - start) * 1E6

    if elapsed > 900 and elapsed < 1200:
        state = 1

    else:
        state = 0

    return state




def PollNAV(request, CurrentTime):

    if request == "IMU":
        print("Reading raw IMU data")


        line = serNAV.readline().decode("ascii", "replace")

        while("$VNIMU" not in line):
            line = serNAV.readline().decode("ascii", "replace")
        
        print("Raw IMU data collected")


        IMU_list = line.split(",")
        IMU_list[0] = CurrentTime
        IMU_list[-1] = IMU_list[-1][:-5] # get rid of ending characters

        print("IMU list formed")

        return IMU_list



    elif request == "Attitude":

        print("requesting attitude from VectorNav")


        serNAV.write(ATTITUDE_CMD) #configure nav for attitude data 
        line=serNAV.readline().decode("ascii", "replace")

        while "$VNRRG,08" not in line:
                serNAV.write(ATTITUDE_CMD)
                line=serNAV.readline().decode("ascii", "replace")

        print("Attitude collected")


        ATTITUDE_list = line.split(",")
        ATTITUDE_list = ATTITUDE_list[1:]
        ATTITUDE_list[0] = CurrentTime
        ATTITUDE_list[-1] = ATTITUDE_list[-1][:-5]

        print("Attitude list formed")

        return ATTITUDE_list
                

def InitLog(attempt):
    DataFolder = "Data/Flight" + str(attempt)

    print(DataFolder)

    if not os.path.exists(DataFolder):
        os.makedirs(DataFolder, exist_ok=False)
        print("Successfully created folder")
    
    IMU_Path = DataFolder + "/" + IMU_DATALOG_Title
    ATTITUDE_Path = DataFolder + "/" + ATTITUDE_DATALOG_TITLE

    IMU_Log = open(IMU_Path, "w")
    ATITTUDE_Log = open(ATTITUDE_Path, "w")
    print("Opening CSVs in write mode")

    writerIMU = csv.writer(IMU_Log)
    writerATTITUDE = csv.writer(ATITTUDE_Log)
    print("Creating CSVs")

    writerIMU.writerow(headerIMU)
    writerATTITUDE.writerow(headerATTITUDE)
    print("Writing headers for CSVs")



    return writerIMU, writerATTITUDE


GPIO.setmode(GPIO.BCM)
GPIO.setup(CH1, GPIO.IN)
GPIO.setup(CH2, GPIO.IN)

if os.path.isdir("Data/"):

    if len(sorted(glob.glob("Data/*"))) >= 1:

        LastFile = sorted(glob.glob("Data/*"))[-1]
        attempt = int(LastFile[-1])
        print("Flight Folder Exists:" , attempt)
        attempt += 1

    else:
        attempt = 1
        print("Flight folder does not exist.")

else:
    print("Flight Folder does not exist: ", 1)
    attempt = 1

while 1:
    StartFlag = 0
    
    if PollReceiver(CH2):
        
        i = 0

        TimeStart = time.time()
        if PollReceiver(CH1):
            print("safety off, disarmed")
            StartFlag = 1
    
    while StartFlag == 1:
        if i == 0:
            print("Beginning program...")


            serNAV.write(TARE_CMD)
            time.sleep(3)

            print("Tare complete, collecting data")


            temp = InitLog(attempt)
            writerIMU, writerATTITUDE = temp
            attempt += 1
            i += 1

        currentTime = time.time() - TimeStart

        writerIMU.writerow(PollNAV("IMU", currentTime))        
        writerATTITUDE.writerow(PollNAV("Attitude", currentTime))

        if PollReceiver(CH2) == 0:
            break

        



            
        