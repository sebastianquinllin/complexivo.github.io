import paho.mqtt.client as mqtt

MQTT_BROKER = "localhost"   # Cambia al broker real
MQTT_PORT = 1883

mqtt_client = mqtt.Client()

def conectar_mqtt():
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
        print("✅ Conectado al broker MQTT")
    except Exception as e:
        print(f"❌ Error al conectar con el broker MQTT: {e}")

def publicar_mensaje(instrumento_id, estado):
    topic = f"sensores/instrumentos/{instrumento_id}"
    mensaje = str(estado)
    mqtt_client.publish(topic, mensaje)
    print(f"🔄 Publicado: {mensaje} en {topic}")

# NUEVA FUNCIÓN genérica para LED, música y volumen:
def publicar_mensaje_custom(topic, mensaje):
    mqtt_client.publish(topic, str(mensaje))
    print(f"🔄 Publicado: {mensaje} en {topic}")
