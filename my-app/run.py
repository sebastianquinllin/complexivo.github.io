# Declarando nombre de la aplicación e inicializando Flask
from app import app

# Importando todos los routers (rutas) activos
from routers.router_login import *
from routers.router_home import *

# Importando MQTT
from controllers.mqtt_client import conectar_mqtt

# Ejecutando el objeto Flask
if __name__ == '__main__':
    app.debug = True
    app.run()

if __name__ == '__main__':
    conectar_mqtt()
    app.debug = True
    app.run()