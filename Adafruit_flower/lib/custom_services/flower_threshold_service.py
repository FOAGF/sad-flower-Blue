"""
`custom_service.flower_threshold_service`
================================================================================

BLE control of CSSE4011 flower  threshold values, these includes CO2 and TVOC
min/max values, how many air quality levels there are, and how the levels are
calculated.

* Author(s): Ben Thorpe
"""

from adafruit_ble.characteristics import Characteristic
from adafruit_ble.characteristics.int import Uint8Characteristic, Uint16Characteristic
from adafruit_ble.services import Service
from adafruit_ble.uuid import VendorUUID


class FlowerThresholdService(Service):
    """Control threshold levels of flower, min CO2, max CO2 etc"""

    uuid = VendorUUID("C55E4011-C55E-4011-0001-C55E40110000")

    minCO2 = Uint16Characteristic(
        uuid=VendorUUID("C55E4011-C55E-4011-0001-C55E40110001"),
        properties=(Characteristic.READ | Characteristic.WRITE),
        initial_value=400,
    )

    maxCO2 = Uint16Characteristic(
        uuid=VendorUUID("C55E4011-C55E-4011-0001-C55E40110002"),
        properties=(Characteristic.READ | Characteristic.WRITE),
        initial_value=2000,
    )

    minTVOC = Uint16Characteristic(
        uuid=VendorUUID("C55E4011-C55E-4011-0001-C55E40110003"),
        properties=(Characteristic.READ | Characteristic.WRITE),
        initial_value=0,
    )

    maxTVOC = Uint16Characteristic(
        uuid=VendorUUID("C55E4011-C55E-4011-0001-C55E40110004"),
        properties=(Characteristic.READ | Characteristic.WRITE),
        initial_value=200,
    )

    num_levels = Uint8Characteristic(
        uuid=VendorUUID("C55E4011-C55E-4011-0001-C55E40110005"),
        properties=(Characteristic.READ | Characteristic.WRITE),
        initial_value=0,
    )

    mode = Uint8Characteristic(
        uuid=VendorUUID("C55E4011-C55E-4011-0001-C55E40110006"),
        properties=(Characteristic.READ | Characteristic.WRITE),
        initial_value=0,
    )


