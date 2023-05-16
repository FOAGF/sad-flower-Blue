import time
import digitalio
import board
from adafruit_circuitplayground import cp

cp.pixels.auto_write = False
cp.pixels.brightness = 0.1


def colour_change(rgb):
    cp.pixels.fill(rgb)
    cp.pixels.show()

pin6 = digitalio.DigitalInOut(board.A6)
pin7 = digitalio.DigitalInOut(board.A7)
pin6.direction = digitalio.Direction.INPUT
pin7.direction = digitalio.Direction.INPUT

count = 0
while True:
    if (not pin6.value) and (not pin7.value):
        colour_change((255, 255, 255))
    elif (pin6.value) and (not pin7.value):
        colour_change((255, 0, 0))
    elif (pin6.value) and (pin7.value):
        colour_change((0, 255, 0))
    elif (not pin6.value) and (pin7.value):
        colour_change((0, 0, 255))

