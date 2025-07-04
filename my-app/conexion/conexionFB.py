import firebase_admin
from firebase_admin import credentials, db

if not firebase_admin._apps:
    cred = credentials.Certificate('api_firebase.json')  # ajusta la ruta si es necesario
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://practica3-46162-default-rtdb.firebaseio.com/'
    })