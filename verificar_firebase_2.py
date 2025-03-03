import firebase_admin
from firebase_admin import credentials, firestore

# Configurar Firebase
cred = credentials.Certificate("firebase_credentials.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Ejecutar consulta
print("🔎 Buscando documentos en Firestore...")

docs = db.collection("horas_extra").where("hora_salida", "==", None).stream()

encontrados = 0
for doc in docs:
    data = doc.to_dict()
    print(f"📂 Documento encontrado: {data}")  # 🔍 Ver todos los documentos sin salida
    encontrados += 1

if encontrados == 0:
    print("✅ No se encontraron usuarios sin salida en Firebase.")
else:
    print(f"⚠️ Se encontraron {encontrados} usuarios sin salida.")
