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

from adafruit_ble_adafruit.adafruit_service import AdafruitServerAdvertisement
from adafruit_ble_adafruit.temperature_service import TemperatureService

from binascii import unhexlify

from adafruit_crickit import crickit

from custom_services.flower_threshold_service import FlowerThresholdService
from custom_services.flower_air_quality_service import FlowerAirQualityService


class Flower:

    def __init__(self, servo):
        self.co2min = 400
        self.co2max = 2000
        self.tvocmin = 0
        self.tvocmax = 2000
        self.num_intensity_levels = 10
        self.current_co2 = 400
        self.current_tvoc = 0
        self.current_level = 0

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

    def update(self, co2ppm):
        """
        Updates the flowers appearence based on the current air quality level,
        air quality should be between 0 and 10 inclusive, lower the better.
        """
        air_quality = self.co2Intensity(co2ppm)
        if (air_quality > 10 or air_quality < 0):
            return

        self.change_colour(air_quality)

        target = 135 - air_quality * (50 // self.num_intensity_levels)
        self._servo.move(target)

    def open_and_close(self):
        """
        Test function that opens and closes the flower by cycling
        through intensity levels, from 0 to 10 then back from 10 to 0.
        """
        for i in list(range(0,10)) + list(range(10, -1, -1)):
            self.update(i)

    def co2Intensity(self, co2ppm):
        """
        Converts a co2 concentration to an intensity level between 0 and 10 inclusive.

        :param co2ppm: co2 concentration in ppm (parts per million)
        :return: Intensity level from 0 to 10 inclusive
        """

        if co2ppm < self.co2min:
            return 0
        elif co2ppm > self.co2max:
            return self.num_intensity_levels
        return floor(self.num_intensity_levels * (co2ppm - self.co2min) / (self.co2max - self.co2min))

    def tvocIntensity(self, tvocppb):
        """
        Converts a TVOC concentration to an intensity level between 0 and 10 inclusive.

        :param tvocppb: tvoc concentration in ppb (parts per billion)
        :return: Intensity level from 0 to 10 inclusive
        """

        if tvocppb < self.tvocmin:
            return 0
        elif tvocppb > self.tvocmax:
            return self.num_intensity_levels
        return floor(self.num_intensity_levels * (tvocppb - self.tvocmin) / (self.tvocmax - self.tvocmin))


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
    air_quality_co2 = Uint16Characteristic(
        uuid=VendorUUID("C55E4011-C55E-4011-0000-C55E40110002"),
        properties=(Characteristic.READ | Characteristic.NOTIFY),
        write_perm=Attribute.NO_ACCESS,
    )
    """Air Quality: co2ppm, ranges from 400-32768ppm"""

    air_quality_tvoc = Uint16Characteristic(
        uuid=VendorUUID("C55E4011-C55E-4011-0000-C55E40110003"),
        properties=(Characteristic.READ | Characteristic.NOTIFY),
        write_perm=Attribute.NO_ACCESS,
    )
    """Air Quality: tvocppb, ranges from 0-29206ppb"""


def range_list(start, end):
    if (start < end):
        return range(start, end)
    else:
        return range(start, end, -1)



def current_time_ms():
    """
    Gets the current time since start up in milliseconds.

    :return: number of milliseconds since start up
    """
    return time.monotonic_ns() // 1000000


def time_elapsed_since(start_time, s):
    """
    checks whether s seconds have elapsed since a start_time.
    """
    return current_time_ms() - start_time > (s * 1000)


# BEGIN CODE
servo = ServoMotor(crickit.servo_1)
flower = Flower(servo)

# open and close flower 3 times, just so that we know it works
for i in range(3):
    flower.open_and_close()

TARGET = 'C8:AE:54:01:AC:A9'
target_address = TARGET.split(":")
target_address.reverse()
target_address = unhexlify(''.join(target_address))

ble = adafruit_ble.BLERadio()
ble.name = "CSSE4011 FLOWER"

client = None

threshold_svc = FlowerThresholdService()
threshold_last_update = 0

air_quality_svc = AirQualityService()
flower_air_quality_last_update = 0

adv = ProvideServicesAdvertisement(threshold_svc)


last_advertisement = 0
last_air_quality_read = 0

while True:

    # Advertise when not connected.
    if not ble.connected and time_elapsed_since(last_advertisement, 10):
        print("start advertising")
        adv_start_time = current_time_ms()
        ble.start_advertising(adv)
        while not ble.connected and not time_elapsed_since(adv_start_time, 5):
            pass
        if not ble.connected:
            print("Failed to find base station")
        ble.stop_advertising()
        print("stop advertising")
        last_advertisement = current_time_ms()


    if not client:
        print("scanning for air quality sensor")
        for adv in ble.start_scan(timeout=1):
            if not client and adv.address.address_bytes == target_address:
                client = ble.connect(adv)
                print("connected AQS")
            if client:
                break
        ble.stop_scan()
        print("stopped scanning")


    if client and client.connected and time_elapsed_since(last_air_quality_read, 0.5):
        try:
            if AirQualityService in client:
                service = client[AirQualityService]
                c02_value = service.air_quality_co2
                tvoc_value = service.air_quality_tvoc
                print("Co2:", c02_value)
                print("TVOC:", tvoc_value)
                flower.update(c02_value)
        except:
            print("Not connected or service unavailable")
            client = None
        last_air_quality_read = current_time_ms()


    if client and not client.connected:
        client = None


    if time_elapsed_since(threshold_last_update, 1):
        flower.co2min = threshold_svc.minCO2
        flower.co2max = threshold_svc.maxCO2
        threshold_last_update = current_time_ms()

    if time_elapsed_since(flower_air_quality_last_update, 1):
        air_quality_svc.co2 = flower.current_co2
        air_quality_svc.tvoc = flower.current_tvoc
        flower.co2max = threshold_svc.maxCO2
        flower_air_quality_last_update = current_time_ms()


    time.sleep(0.01)


