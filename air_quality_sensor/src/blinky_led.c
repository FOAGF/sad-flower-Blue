#include <zephyr/kernel.h>
#include <zephyr/drivers/gpio.h>

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


// Initilises all led's and blinks red led every second
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