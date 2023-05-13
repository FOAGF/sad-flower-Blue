import time
from adafruit_crickit import crickit

ss = crickit.seesaw

OUTPUT_1 = crickit.SIGNAL1
OUTPUT_2 = crickit.SIGNAL2
ss.pin_mode(OUTPUT_1, ss.OUTPUT)
ss.pin_mode(OUTPUT_2, ss.OUTPUT)
currentAngle = 85

def move_servo(angle):
    #85degree - 140 (135)degree
    print("aim angle is:" + str(angle))
    crickit.servo_1.angle = angle

#ONLY for int inputs
def range_list(start, end):
    if (start < end):
        return range(start, end)
    else:
        current = start
        output = []
        while (current >= end):
            output.append(current)
            current -= 1
    return output

def change_colour(val):
    if (val >= 0 and val < 4):
        ss.digital_write(OUTPUT_1, False)
        ss.digital_write(OUTPUT_2, False)
    elif (val >= 4 and val < 7):
        ss.digital_write(OUTPUT_1, True)
        ss.digital_write(OUTPUT_2, False)
    elif (val >=7 and val < 9):
        ss.digital_write(OUTPUT_1, True)
        ss.digital_write(OUTPUT_2, True)
    elif (val >= 9 and val <= 11):
        ss.digital_write(OUTPUT_1, False)
        ss.digital_write(OUTPUT_2, True)

def air_quality(val):
    global currentAngle
    val = int(val)
    if (val > 10 or val < 0):
        return
    change_colour(val)
    for i in range_list(currentAngle, 135 - val * 5):
        move_servo(i)
        time.sleep(0.01)
    currentAngle = 135 - val * 4

#while True:
#    for i in range(180):
#        move_servo(i)
#        time.sleep(0.5)
#    # and repeat!

move_servo(85)

air_quality(1)
time.sleep(5)
air_quality(10)
time.sleep(5)
air_quality(1)
time.sleep(5)
air_quality(10)
