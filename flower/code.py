# import board
import sys
import time
from math import floor

import _bleio

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


MAX_ANGEL = 145
MIN_ANGEL = 92
TARGET = 'C8:AE:54:01:AC:A9'

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
        self.calculation_mode = 0

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

    def update(self):
        """
        Updates the flowers appearence based on the current air quality level,
        air quality should be between 0 and 10 inclusive, lower the better.

        The air qulaity level is calculated based on the current calculation_mode,
        0: Take the maximum intensity of co2 and tvoc levels
        1: Take the average intensity of co2 and tvoc levels
        2: Add the co2 and tvoc levels
        3: Hold, keep the same value as last time (update manually)
        """
        co2_intensity = self.co2Intensity(self.current_co2)
        tvoc_intensity  = self.tvocIntensity(self.current_tvoc)
        if self.calculation_mode == 0:
            self.current_level = max(co2_intensity, tvoc_intensity)
        elif self.calculation_mode == 1:
            self.current_level = (co2_intensity + tvoc_intensity) // 2
        elif self.calculation_mode == 2:
            self.current_level = (co2_intensity + tvoc_intensity)
        elif self.calculation_mode == 3:
            pass # Hold the current value
        else:
            print("Invalid mode")
            return

        # keep intensity level within bounds
        self.current_level = min(max(self.current_level, 0), self.num_intensity_levels)

        self.change_colour(self.current_level)

        target = MAX_ANGEL - self.current_level * ((MAX_ANGEL - MIN_ANGEL) // self.num_intensity_levels)
        self._servo.move(target)


    def open_and_close(self):
        """
        Test function that opens and closes the flower by cycling
        through intensity levels, from 0 to 10 then back from 10 to 0.
        """
        mode = self.calculation_mode
        self.calculation_mode = 3
        for i in list(range(0,10)) + list(range(10, -1, -1)):
            self.current_level = i
            self.update()
        self.calculation_mode = mode

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

    def __init__(self, crickit_servo, initial_angle = MAX_ANGEL):
        self._angle = initial_angle
        self._servo = crickit_servo

    def move(self, target):
        if target < MIN_ANGEL or target > MAX_ANGEL:
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
    return range(start, end) if start < end else range(start, end, -1)


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


def scan_and_connect_to_sensor():
    client = None
    for adv in ble.start_scan(timeout=1):
        if adv.address.address_bytes == target_address:
            client = ble.connect(adv)
            print("Connected to air quality sensor")
        if client:
            break
        time.sleep(0.01)
    ble.stop_scan()
    return client


def advertise_for_base_station():
    global ble
    global adv
    print("start advertising")
    base_station = None
    time.sleep(0.2)
    adv_start_time = current_time_ms()
    # gui cant connect while actually advertiseing, or scanning,
    # so do nothing for a while
    ble.start_advertising(adv, interval=0.1)
    while not ble.connected and not time_elapsed_since(adv_start_time, 2):
        pass
    if not ble.connected:
        print("Failed to find base station")
    else:
        print("Found base station")
        base_station = ble.connections[0]
    ble.stop_advertising()
    print("stop advertising")
    last_advertisement = current_time_ms()
    return base_station


# BEGIN CODE
servo = ServoMotor(crickit.servo_1)
flower = Flower(servo)

# open and close flower 3 times, just so that we know it works
for i in range(3):
    flower.open_and_close()

# transform target address to apropriate format
target_address = TARGET.split(":")
target_address.reverse()
target_address = unhexlify(''.join(target_address))

ble = adafruit_ble.BLERadio()
ble.name = "CSSE4011 FLOWER"

client = None
base_station = None

threshold_svc = FlowerThresholdService()
air_quality_svc = FlowerAirQualityService()
adv = ProvideServicesAdvertisement()

# last update values
threshold_last_update = 0
flower_air_quality_last_update = 0
last_advertisement = 0
last_air_quality_read = 0
last_flower_update = 0


while True:

    # Advertise when not connected to base station.
    if ((not base_station or not base_station.connected)
        and time_elapsed_since(last_advertisement, 10)):
        # Cannot advertise while connected to another device
        client = None
        while ble.connected:
            for connection in ble.connections:
                connection.disconnect()
        base_station = advertise_for_base_station()
        last_advertisement = current_time_ms()

    # Scan and connect client if not connected to sensor.
    if not client or not client.connected:
        try:
            print("Scanning")
            client = scan_and_connect_to_sensor()
        except MemoryError:
            print("Scan allocated too much memory")

    # Read air quality values from sensor, if connected.
    if client and client.connected and time_elapsed_since(last_air_quality_read, 0.5):
        try:
            if AirQualityService in client:
                service = client[AirQualityService]
                co2_value = service.air_quality_co2
                tvoc_value = service.air_quality_tvoc
                flower.current_co2 = co2_value
                flower.current_tvoc = tvoc_value
                print("Air Quality: Co2 =", co2_value, "| TVOC =", tvoc_value)
        except ConnectionError:
            print("Not connected")
            client.disconnect()
            client = None
        except AttributeError:
            print("Service not available, disconnecting")
            client.disconnect()
            client = None
        last_air_quality_read = current_time_ms()

    # Update threshold service values
    if time_elapsed_since(threshold_last_update, 1):
        flower.co2min = threshold_svc.minCO2
        flower.co2max = threshold_svc.maxCO2
        flower.tvocmin = threshold_svc.minTVOC
        flower.tvocmax = threshold_svc.maxTVOC
        flower.num_intensity_levels = threshold_svc.num_levels
        threshold_last_update = current_time_ms()

    # Update air quality service values
    if time_elapsed_since(flower_air_quality_last_update, 1):
        air_quality_svc.co2ppm = flower.current_co2
        air_quality_svc.tvocppb = flower.current_tvoc
        if air_quality_svc.last_current_level != air_quality_svc.current_level:
            flower.current_level = air_quality_svc.current_level
        else:
            # set value to be read
            air_quality_svc.current_level = flower.current_level
        air_quality_svc.last_current_level = flower.current_level

        flower_air_quality_last_update = current_time_ms()


    # Update flower
    if (time_elapsed_since(last_flower_update, 1)):
        flower.update()
        last_flower_update = current_time_ms()



    time.sleep(0.01)


