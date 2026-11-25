import time
import random
import threading
import paho.mqtt.client as mqtt

# ================= KONFIGURASI =================
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
NIM = "2410010475"
MQTT_CLIENT_ID = f"PythonDevice-{NIM}"

TOPIC_SUHU = f"iot/{NIM}/sensor/suhu"
TOPIC_RELAY = f"iot/{NIM}/aktuator/relay"
TOPIC_PWM = f"iot/{NIM}/aktuator/pwm"
TOPIC_STATUS_RELAY = f"iot/{NIM}/status/relay"

INTERVAL_PUBLISH = 3  # Mengirim data suhu setiap 3 detik sesuai tugas

# ================= STATE SIMULASI PIN GPIO =================
gpio_26_relay = "OFF"  # Simulasi GPIO 26 (Relay)
gpio_23_pwm = 0        # Simulasi GPIO 23 (LED PWM 0-255)


# ================= CALLBACK MQTT =================
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[MQTT] Terhubung ke broker ({MQTT_BROKER}:{MQTT_PORT})")
        client.subscribe(TOPIC_RELAY, qos=0)
        client.subscribe(TOPIC_PWM, qos=0)
        print(f"[MQTT] Subscribe topik Relay : {TOPIC_RELAY}")
        print(f"[MQTT] Subscribe topik PWM   : {TOPIC_PWM}")
    else:
        print(f"[MQTT] Gagal terhubung, kode: {rc}")


def on_message(client, userdata, msg):
    global gpio_26_relay, gpio_23_pwm
    payload = msg.payload.decode("utf-8").strip()

    # 1. Kontrol Relay pada GPIO 26
    if msg.topic == TOPIC_RELAY:
        if payload in ("ON", "1"):
            gpio_26_relay = "ON"
            print("[GPIO 26 - RELAY] Status: ON (Relay Aktif / Menyala)")
        elif payload in ("OFF", "0"):
            gpio_26_relay = "OFF"
            print("[GPIO 26 - RELAY] Status: OFF (Relay Mati)")
        else:
            print(f"[GPIO 26 - RELAY] Perintah tidak dikenal: {payload}")
            return

        # Kirim feedback status relay ke Node-RED
        client.publish(TOPIC_STATUS_RELAY, gpio_26_relay, qos=0)

    # 2. Kontrol Kecerahan LED (PWM 0-255) pada GPIO 23
    elif msg.topic == TOPIC_PWM:
        try:
            nilai_pwm = int(float(payload))
            if 0 <= nilai_pwm <= 255:
                gpio_23_pwm = nilai_pwm
                persen = round((gpio_23_pwm / 255) * 100)
                print(f"[GPIO 23 - PWM] Kecerahan LED diatur ke: {gpio_23_pwm}/255 ({persen}%)")
            else:
                print(f"[GPIO 23 - PWM] Nilai di luar rentang (0-255): {nilai_pwm}")
        except ValueError:
            print(f"[GPIO 23 - PWM] Payload bukan angka valid: {payload}")


def on_disconnect(client, userdata, rc):
    print(f"[MQTT] Terputus (kode: {rc}). Mencoba reconnect...")


# ================= PEMBACAAN SENSOR =================
def baca_suhu_dht22():
    """Simulasi pembacaan suhu sensor DHT22 (24.0 - 30.0 °C)."""
    base = 27.0
    noise = random.uniform(-1.5, 1.5)
    return round(base + noise, 2)


# ================= THREAD PUBLISH SENSOR =================
def publish_loop(client):
    while True:
        suhu = baca_suhu_dht22()
        client.publish(TOPIC_SUHU, str(suhu), qos=0)
        print(f"[DHT22 -> {TOPIC_SUHU}] Suhu: {suhu} °C")
        time.sleep(INTERVAL_PUBLISH)


# ================= MAIN =================
def main():
    client = mqtt.Client(client_id=MQTT_CLIENT_ID, protocol=mqtt.MQTTv311)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.reconnect_delay_set(min_delay=1, max_delay=30)

    print(f"[MQTT] Menghubungkan ke {MQTT_BROKER}:{MQTT_PORT}...")
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_start()
    time.sleep(1)

    publisher = threading.Thread(target=publish_loop, args=(client,), daemon=True)
    publisher.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[MAIN] Menghentikan program...")
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()