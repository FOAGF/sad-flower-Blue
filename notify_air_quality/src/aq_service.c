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
#include <errno.h>
#include <zephyr/sys/printk.h>
#include <zephyr/sys/byteorder.h>
#include <zephyr/kernel.h>

#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/hci.h>
#include <zephyr/bluetooth/conn.h>
#include <zephyr/bluetooth/uuid.h>
#include <zephyr/bluetooth/gatt.h>

static uint8_t aq[10];
static uint8_t aq_update;

static void aq_ccc_cfg_changed(const struct bt_gatt_attr *attr, uint16_t value)
{
	/* TODO: Handle value */
}

static ssize_t read_aq(struct bt_conn *conn, const struct bt_gatt_attr *attr,
		       void *buf, uint16_t len, uint16_t offset)
{
 const char *str = "hello";

	return bt_gatt_attr_read(conn, attr, buf, len, offset, str ,
				 sizeof(str ) + 1);
}

static ssize_t write_aq(struct bt_conn *conn, const struct bt_gatt_attr *attr,
			const void *buf, uint16_t len, uint16_t offset,
			uint8_t flags)
{
	uint8_t *value = attr->user_data;

	if (offset + len > sizeof(aq)) {
		return BT_GATT_ERR(BT_ATT_ERR_INVALID_OFFSET);
	}

	memcpy(value + offset, buf, len);
	aq_update = 1U;

	return len;
}

/* Current Time Service Declaration */
BT_GATT_SERVICE_DEFINE(aqs_cvs,
	BT_GATT_PRIMARY_SERVICE(BT_UUID_CTS),
	BT_GATT_CHARACTERISTIC(BT_UUID_CTS_CURRENT_TIME, BT_GATT_CHRC_READ |
			       BT_GATT_CHRC_NOTIFY | BT_GATT_CHRC_WRITE,
			       BT_GATT_PERM_READ | BT_GATT_PERM_WRITE,
			       read_aq, write_aq, aq),
	BT_GATT_CCC(aq_ccc_cfg_changed, BT_GATT_PERM_READ | BT_GATT_PERM_WRITE),
);


void aqs_init(void)
{
	/* Simulate current time for Current Time Service */
	generate_current_time(aq);
}

void aqs_notify(void)
{	/* Current Time Service updates only when time is changed */

	bt_gatt_notify(NULL, &aqs_cvs.attrs[1], &aq, sizeof(aq));
}
