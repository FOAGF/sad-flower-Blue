/** @file
 *  @brief CTS Service sample
 */

/*
 * Copyright (c) 2016 Intel Corporation
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zephyr/types.h>
#include <stddef.h>
#include <string.h>
#include <stdio.h>
#include <errno.h>
#include <zephyr/sys/printk.h>
#include <zephyr/sys/byteorder.h>
#include <zephyr/kernel.h>

#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/hci.h>
#include <zephyr/bluetooth/conn.h>
#include <zephyr/bluetooth/uuid.h>
#include <zephyr/bluetooth/gatt.h>

#include <zephyr/drivers/sensor.h>
#include <zephyr/drivers/sensor/ccs811.h>

#include "aq_service.h"

#define AQS_THREAD_SIZE 1000
#define AQS_THREAD_PRIORITY 5

static void aqs_thread(void *, void *, void *);

K_THREAD_DEFINE(aqs_thread_id, AQS_THREAD_SIZE,
                aqs_thread, NULL, NULL, NULL,
                AQS_THREAD_PRIORITY, 0, 0);


static uint8_t aq[4];

static void aq_ccc_cfg_changed(const struct bt_gatt_attr *attr, uint16_t value)
{
	/* TODO: Handle value */
}

static ssize_t read_aq(struct bt_conn *conn, const struct bt_gatt_attr *attr,
		       void *buf, uint16_t len, uint16_t offset)
{
	uint8_t *data = (uint8_t *) attr->user_data;
	return bt_gatt_attr_read(conn, attr, buf, len, offset, data ,
				 sizeof(aq)/2);
}

/* Current Time Service Declaration */
BT_GATT_SERVICE_DEFINE(aqs_cvs,
	BT_GATT_PRIMARY_SERVICE(&aqs_service_uuid),
	BT_GATT_CHARACTERISTIC(&aqs_co2.uuid,
				   BT_GATT_CHRC_READ | BT_GATT_CHRC_NOTIFY,
			       BT_GATT_PERM_READ,
			       read_aq, NULL, &aq[0]),	
	BT_GATT_CHARACTERISTIC(&aqs_tvoc.uuid, 
				   BT_GATT_CHRC_READ | BT_GATT_CHRC_NOTIFY,
			       BT_GATT_PERM_READ,
			       read_aq, NULL, &aq[2]),
	BT_GATT_CCC(aq_ccc_cfg_changed, BT_GATT_PERM_READ),
);


void aqs_init(void)
{
	// do nothing (start thread)
}

void aqs_notify(void)
{	

	bt_gatt_notify(NULL, &aqs_cvs.attrs[1], &aq, sizeof(aq));
}

static bool app_fw_2;

static const char *now_str(void)
{
	static char buf[16]; /* ...HH:MM:SS.MMM */
	uint32_t now = k_uptime_get_32();
	unsigned int ms = now % MSEC_PER_SEC;
	unsigned int s;
	unsigned int min;
	unsigned int h;

	now /= MSEC_PER_SEC;
	s = now % 60U;
	now /= 60U;
	min = now % 60U;
	now /= 60U;
	h = now;

	snprintf(buf, sizeof(buf), "%u:%02u:%02u.%03u",
		 h, min, s, ms);
	return buf;
}

static int do_fetch(const struct device *dev)
{
	struct sensor_value co2, tvoc, voltage, current;
	int rc = 0;

	if (rc == 0) {
		rc = sensor_sample_fetch(dev);
	}
	if (rc == 0) {
		const struct ccs811_result_type *rp = ccs811_result(dev);

		sensor_channel_get(dev, SENSOR_CHAN_CO2, &co2);
		sensor_channel_get(dev, SENSOR_CHAN_VOC, &tvoc);
		sensor_channel_get(dev, SENSOR_CHAN_VOLTAGE, &voltage);
		sensor_channel_get(dev, SENSOR_CHAN_CURRENT, &current);
		printk("\n[%s]: CCS811: %u ppm eCO2; %u ppb eTVOC\n",
		       now_str(), co2.val1, tvoc.val1);
		printk("Voltage: %d.%06dV; Current: %d.%06dA\n", voltage.val1,
		       voltage.val2, current.val1, current.val2);

		if (app_fw_2 && !(rp->status & CCS811_STATUS_DATA_READY)) {
			printk("STALE DATA\n");
		}

		if (rp->status & CCS811_STATUS_ERROR) {
			printk("ERROR: %02x\n", rp->error);
		}
		
		aq[0] = (uint8_t) (co2.val1 >> 0);
		aq[1] = (uint8_t) (co2.val1 >> 8);		
		aq[2] = (uint8_t) (tvoc.val1 >> 0);
		aq[3] = (uint8_t) (tvoc.val1 >> 8);
	}
	return rc;
}


static void fetch_value(const struct device *dev)
{
	
	int rc = do_fetch(dev);

	if (rc == 0) {
		printk("Timed fetch got %d\n", rc);
	} else if (-EAGAIN == rc) {
		printk("Timed fetch got stale data\n");
	} else {
		printk("Timed fetch failed: %d\n", rc);
	}
}


// Initilises air quality sensor and updates every second
static void aqs_thread(void *, void *, void *) {

	const struct device *const dev = DEVICE_DT_GET_ONE(ams_ccs811);
	struct ccs811_configver_type cfgver;
	int rc;

	if (!device_is_ready(dev)) {
		printk("Device %s is not ready\n", dev->name);
		return;
	}

	printk("device is %p, name is %s\n", dev, dev->name);

	rc = ccs811_configver_fetch(dev, &cfgver);
	if (rc == 0) {
		printk("HW %02x; FW Boot %04x App %04x ; mode %02x\n",
		       cfgver.hw_version, cfgver.fw_boot_version,
		       cfgver.fw_app_version, cfgver.mode);
		app_fw_2 = (cfgver.fw_app_version >> 8) > 0x11;
	}


	while (1)
	{
		fetch_value(dev);
		k_sleep(K_MSEC(1000));
	}
}

