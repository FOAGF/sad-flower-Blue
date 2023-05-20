"""
`custom_service.flower_air_quality_service`
================================================================================

BLE service for reading current air quality metrics of the flower,
can also be used to set the level of the flower.

* Author(s): Ben Thorpe
"""

from adafruit_ble.characteristics import Characteristic
from adafruit_ble.characteristics.int import Uint8Characteristic, Uint16Characteristic
from adafruit_ble.services import Service
from adafruit_ble.uuid import VendorUUID


class FlowerAirQualityService(Service):
    """Read current air quality metrics of the flower,
    can also be used to set the flower level directly"""

    uuid = VendorUUID("C55E4011-C55E-4011-0002-C55E40110000")

    co2ppm = Uint16Characteristic(
        uuid=VendorUUID("C55E4011-C55E-4011-0002-C55E40110001"),
        properties=(Characteristic.READ),
        initial_value=400,
    )

    tvocppb = Uint16Characteristic(
        uuid=VendorUUID("C55E4011-C55E-4011-0002-C55E40110002"),
        properties=(Characteristic.READ),
        initial_value=0,
    )

    current_level = Uint16Characteristic(
        uuid=VendorUUID("C55E4011-C55E-4011-0002-C55E40110003"),
        properties=(Characteristic.READ | Characteristic.WRITE),
        initial_value=0,
    )


