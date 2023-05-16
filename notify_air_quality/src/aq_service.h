#ifndef AQ_SERVICE_H
#define AQ_SERVICE_H


#define BT_UUID_AIR_QUALITY_SERVICE \
	BT_UUID_128_ENCODE(0xc55e4011, 0xc55e, 0x4011, 0x0000, 0xc55e40110001)

#define BT_UUID_AIR_QUALITY_NOTIFICATION \
	BT_UUID_128_ENCODE(0xc55e4011, 0xc55e, 0x4011, 0x0000, 0xc55e40110002)

static struct bt_uuid_128 aqs_service_uuid = BT_UUID_INIT_128(
	BT_UUID_AIR_QUALITY_SERVICE);

static struct bt_uuid_128 aqs_notify_uuid = BT_UUID_INIT_128(
	BT_UUID_AIR_QUALITY_NOTIFICATION);

void aqs_init(void);
void aqs_notify(void);

#endif