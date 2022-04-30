import time

import RPi.GPIO as GPIO
#https://learn.sparkfun.com/tutorials/raspberry-gpio/gpio-pinout
#17, right switch
#27, left switch
pin = 27

#17 and 27

GPIO.setmode(GPIO.BCM)
GPIO.setup(pin, GPIO.IN)

start = 0
stop = 0

continueFlag = 1
while 1:

    while GPIO.input(pin) == 0:
        start = time.time()

    while GPIO.input(pin) == 1:
        stop = time.time()

    Elapsed = (stop - start) * 1E6

    if Elapsed > 900 and Elapsed < 1200:
        print("UP")

    elif Elapsed > 1350 and Elapsed < 1650:
        print("Middle")

    elif Elapsed > 1850 and Elapsed < 2100:
        print("Down")