import network
from machine import PWM, Pin
import time
from umqtt.simple import MQTTClient
import json

# WiFi配置
WIFI_SSID = "你的WiFi名称"
WIFI_PASSWORD = "你的WiFi密码"

# MQTT配置
MQTT_BROKER = "你的MQTT服务器"
MQTT_PORT = 1883
MQTT_TOPIC = b"garbage/category"
CLIENT_ID = "esp32_garbage_control"

# 舵机配置
SERVO_PINS = {
    "other": 27,     # 其他垃圾桶舵机引脚
    "kitchen": 12,   # 厨余垃圾桶舵机引脚
    "recyclable": 14,# 可回收物垃圾桶舵机引脚
    "harmful": 13    # 有害垃圾桶舵机引脚
}

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('连接到WiFi...')
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        # 等待连接或超时
        max_wait = 10
        while max_wait > 0:
            if wlan.isconnected():
                break
            max_wait -= 1
            print('等待连接...')
            time.sleep(1)

    if wlan.isconnected():
        print('WiFi连接成功')
        print('网络配置:', wlan.ifconfig())
        return True
    else:
        print('WiFi连接失败')
        return False

# 初始化舵机
servos = {}
for category, pin in SERVO_PINS.items():
    servos[category] = PWM(Pin(pin, Pin.OUT), freq=50)

def set_angle(servo, angle):
    if angle < 0 or angle > 180:
        return
    ns = int(angle/(180/(2500000-500000))+500000)
    servo.duty_ns(ns)
    time.sleep(0.5)

def open_close_bin(category):
    if category in servos:
        servo = servos[category]
        # 打开垃圾桶 (0度)
        set_angle(servo, 0)
        time.sleep(2)  # 等待2秒
        # 关闭垃圾桶 (90度)
        set_angle(servo, 90)

def mqtt_callback(topic, msg):
    category = msg.decode()
    print(f"收到垃圾类别: {category}")
    open_close_bin(category)

def main():
    # 首先连接WiFi
    if not connect_wifi():
        print("WiFi连接失败，程序退出")
        return

    # 连接MQTT服务器
    try:
        client = MQTTClient(CLIENT_ID, MQTT_BROKER, port=MQTT_PORT)
        client.set_callback(mqtt_callback)
        client.connect()
        client.subscribe(MQTT_TOPIC)
        print("已连接到MQTT服务器")

        while True:
            client.check_msg()
            time.sleep(0.1)
    except Exception as e:
        print(f"错误: {e}")
        client.disconnect()

if __name__ == "__main__":
    main()