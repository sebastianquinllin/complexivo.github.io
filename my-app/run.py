from app import app
from conexion.conexionFB import *   

# Importa los routers necesarios
from routers.router_login import *
from routers.router_home import *


if __name__ == '__main__':
    app.debug = True
    app.run()
