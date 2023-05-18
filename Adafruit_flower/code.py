# import board
import sys
import time
from math import floor

import adafruit_ble
from adafruit_ble.advertising import Advertisement
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.uuid import VendorUUID
from adafruit_ble.attributes import Attribute
from adafruit_ble.services import Service
from adafruit_ble.characteristics import Characteristic
from adafruit_ble.characteristics.int import Uint16Characteristic

from binascii import unhexlify

from adafruit_crickit import crickit

class Flower:

    def __init__(self, servo):
        self._servo = servo
        self._output_1 = crickit.SIGNAL1
        self._output_2 = crickit.SIGNAL2
        ss = crickit.seesaw
        ss.pin_mode(crickit.SIGNAL1, ss.OUTPUT)
        ss.pin_mode(crickit.SIGNAL2, ss.OUTPUT)

    def change_colour(self, val):
        # On when val between 4 and 8, off otherwise
        crickit.seesaw.digital_write(self._output_1, 4 <= val < 9)
        # On when val greater than 7, off otherwise
        crickit.seesaw.digital_write(self._output_2, val >= 7)

    def update(self, air_quality):
        """
        Updates the flowers appearence based on the current air quality level,
        air quality should be between 0 and 10 inclusive, lower the better.
        """
        air_quality = int(air_quality)
        if (air_quality > 10 or air_quality < 0):
            return

        self.change_colour(air_quality)

        target = 135 - air_quality * 5
        self._servo.move(target)

    def open_and_close(self):
        """
        Test function that opens and closes the flower by cycling
        through intensity levels, from 0 to 10 then back from 10 to 0.
        """
        for i in list(range(0,10)) + list(range(10, -1, -1)):
            self.update(i)


class ServoMotor:

    def __init__(self, crickit_servo, initial_angle = 135):
        self._angle = initial_angle
        self._servo = crickit_servo

    def move(self, target):
        if target < 85 or target > 140:
            print("Angle is outside acceptable range:", target)
            return

        for i in range_list(self._angle, target + 1):
            self._servo.angle = i
            time.sleep(0.01)
        self._angle = target


class AirQualityService(Service):
    """Custom air quality sensor value service."""

    uuid = VendorUUID("C55E4011-C55E-4011-0000-C55E40110001")
    air_quality = Uint16Characteristic(
        uuid=VendorUUID("C55E4011-C55E-4011-0000-C55E40110002"),
        properties=(Characteristic.READ | Characteristic.NOTIFY),
        write_perm=Attribute.NO_ACCESS,
    )
    """Air Quality: co2ppm, ranges from 400-8192ppm"""

########### Helper funcitons ##############

#ONLY for int inputs
def range_list(start, end):
    if (start < end):
        return range(start, end)
    else:
        return range(start, end, -1)


def co2Intensity(co2ppm):
    """
    Converts a co2 concentration to an intensity level between 0 and 10 inclusive.

    :param co2ppm: co2 concentration in ppm (parts per million)
    :return: Intensity level from 0 to 10 inclusive
    """

    CO2MIN = 400
    CO2MAX = 2000
    NUM_LEVLES = 10

    if co2ppm < CO2MIN:
        return 0
    elif co2ppm > CO2MAX:
        return NUM_LEVLES
    return floor(NUM_LEVLES * (co2ppm - CO2MIN) / (CO2MAX - CO2MIN))


# BEGIN CODE
servo = ServoMotor(crickit.servo_1)
flower = Flower(servo)
flower.open_and_close()

TARGET = 'C8:AE:54:01:AC:A9'
target_address = TARGET.split(":")
target_address.reverse()
target_address = unhexlify(''.join(target_address))

ble = adafruit_ble.BLERadio()
if ble.connected:
    for c in ble.connections:
        c.disconnect()

client = None

while True:
    if not client:
        print("Trying to connect to BLE Server...")
        for adv in ble.start_scan(ProvideServicesAdvertisement, timeout=10):
            if adv.address.address_bytes == target_address:
                client = ble.connect(adv)
                print("connected")
                break
        ble.stop_scan()

    if client and client.connected:
        if AirQualityService in client:
            try:
                service = client[AirQualityService]
            except:
                print("Not connected or service unavailable")
                client = None
            else:
                air_quality_value = service.air_quality
                print("Air Quality:", air_quality_value, co2Intensity(air_quality_value))
                flower.air_quality(co2Intensity(air_quality_value))

    if client and not client.connected:
        client = None

    time.sleep(0.5)


