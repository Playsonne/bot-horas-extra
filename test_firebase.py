import firebase_admin
from firebase_admin import credentials, firestore

# Cargar las credenciales de Firebase
cred = credentials.Certificate("firebase_credentials.json")
firebase_admin.initialize_app(cred)

# Conectar con Firestore
db = firestore.client()

# Probar la conexión creando un documento de prueba
doc_ref = db.collection("pruebas").document("conexion")
doc_ref.set({"mensaje": "Conexión exitosa con Firebase"})

print("✅ Firebase configurado correctamente")
