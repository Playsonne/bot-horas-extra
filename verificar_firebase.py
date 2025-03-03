import firebase_admin
from firebase_admin import credentials, firestore

# Inicializar Firebase
cred = credentials.Certificate("firebase_credentials.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# 🔍 Buscar documentos donde "hora_salida" no esté definida o esté vacía
usuarios_sin_salida = db.collection("horas_extra").stream()

print("🔎 Buscando registros sin salida en Firebase...")

encontrados = 0
for doc in usuarios_sin_salida:
    data = doc.to_dict()
    print(f"📂 Documento encontrado: {data}")  # 🔍 Ver todos los documentos

    if "hora_salida" not in data or not data["hora_salida"]:  # Si no tiene hora de salida
        print(f"📄 Usuario sin salida: {data}")
        encontrados += 1

if encontrados == 0:
    print("✅ No se encontraron usuarios sin salida en Firebase.")
else:
    print(f"⚠️ Se encontraron {encontrados} usuarios sin salida.")
