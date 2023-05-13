/* main.c - Application main entry point */

/*
 * Copyright (c) 2015-2016 Intel Corporation
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zephyr/kernel.h>
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/gatt.h>
#include <zephyr/drivers/gpio.h>

#include "aq_service.h"

// ----------------- LED  ----------------- 
/* The devicetree node identifiers for the red green and blue alias'. */
#define LED_RED DT_ALIAS(led0)
#define LED_GREEN DT_ALIAS(led1)
#define LED_BLUE DT_ALIAS(led2)

static const struct gpio_dt_spec led_red = GPIO_DT_SPEC_GET(LED_RED, gpios);
static const struct gpio_dt_spec led_green = GPIO_DT_SPEC_GET(LED_GREEN, gpios);
static const struct gpio_dt_spec led_blue = GPIO_DT_SPEC_GET(LED_BLUE, gpios);

#define LED_BLINK_THREAD_SIZE 1000
#define LED_BLINK_THREAD_PRIORITY 10

static void led_thread(void *, void *, void *);

K_THREAD_DEFINE(led_blink_thread_id, LED_BLINK_THREAD_SIZE,
                led_thread, NULL, NULL, NULL,
                LED_BLINK_THREAD_PRIORITY, 0, 0);

// -----------------  END LED  ----------------- 

static const struct bt_data ad[] = {
	BT_DATA_BYTES(BT_DATA_FLAGS, (BT_LE_AD_GENERAL | BT_LE_AD_NO_BREDR)),
	BT_DATA_BYTES(BT_DATA_UUID16_ALL,
		      BT_UUID_16_ENCODE(BT_UUID_CTS_VAL)),
};

static void connected(struct bt_conn *conn, uint8_t err)
{
	if (err) {
		printk("Connection failed (err 0x%02x)\n", err);
	} else {
		printk("Connected\n");
	}
}

static void disconnected(struct bt_conn *conn, uint8_t reason)
{
	printk("Disconnected (reason 0x%02x)\n", reason);
}

BT_CONN_CB_DEFINE(conn_callbacks) = {
	.connected = connected,
	.disconnected = disconnected,
};

static void bt_ready(void)
{
	int err;

	printk("Bluetooth initialized\n");

	aqs_init();

	err = bt_le_adv_start(BT_LE_ADV_CONN_NAME, ad, ARRAY_SIZE(ad), NULL, 0);
	if (err) {
		printk("Advertising failed to start (err %d)\n", err);
		return;
	}

	printk("Advertising successfully started\n");
}


void main(void)
{

	int err;

	err = bt_enable(NULL);
	if (err) {
		printk("Bluetooth init failed (err %d)\n", err);
		return;
	}

	bt_ready();

	//Implement notification.
	while (1) {
		k_sleep(K_SECONDS(1));
		/* Air Quality Service updates only when new value is read */
		aqs_notify();
	}
}



				
// -----------------  LED  ----------------- 

// Initialise an led from device tree spec
static bool initGpio(const struct gpio_dt_spec *led_dt)
{

	if (!gpio_is_ready_dt(led_dt))
	{
		return true;
	}

	if (gpio_pin_configure_dt(led_dt, GPIO_OUTPUT_ACTIVE) < 0)
	{
		return true;
	}

	gpio_pin_set_dt(led_dt, 0);

	return false;
}


// blinks led every second, signifies mobile node is running
static void led_thread(void *, void *, void *) {

	if (initGpio(&led_red) || initGpio(&led_green) || initGpio(&led_blue))
	{
		return;
	}

	while (1)
	{
		gpio_pin_toggle_dt(&led_red);
		k_sleep(K_MSEC(1000));
	}
}
			
// -----------------  END LED  ----------------- 