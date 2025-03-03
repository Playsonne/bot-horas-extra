import logging
import firebase_admin
from firebase_admin import credentials, firestore
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext, JobQueue
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import telegram

# Configurar Firebase
cred = credentials.Certificate("firebase_credentials.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Configurar Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
gs_credentials = ServiceAccountCredentials.from_json_keyfile_name("google_sheets_credentials.json", scope)
gc = gspread.authorize(gs_credentials)
sheet = gc.open_by_key("1-KpZmMWVPoCRNW4UfgfYgBQQvpbKSRE3W7fUARN5z7g")

# Configurar logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# 🔹 Función para el comando /start
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("👋 ¡Hola! Usa /entrada para registrar tu hora de inicio y /salida para registrar la salida.")

# 🔹 Función para registrar la entrada
async def entrada(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    fecha = datetime.now().strftime("%Y-%m-%d")
    hora_entrada = datetime.now().strftime("%H:%M:%S")

    doc_id = f"{user_id}_{fecha}"
    doc_ref = db.collection("horas_extra").document(doc_id)
    doc = doc_ref.get()

    if doc.exists:
        nuevo_doc_ref = db.collection("horas_extra").document()
        nuevo_doc_ref.set({
            "usuario": user_id,
            "fecha": fecha,
            "hora_entrada": hora_entrada
        })
        print(f"🆕 Nueva entrada guardada con ID: {nuevo_doc_ref.id}")
        await update.message.reply_text(f"🆕 Nueva entrada registrada a las {hora_entrada}.")
    else:
        datos = {
            "usuario": user_id,
            "fecha": fecha,
            "hora_entrada": hora_entrada
        }
        print(f"📝 Guardando en Firebase: {datos}")
        doc_ref.set(datos, merge=True)
        await update.message.reply_text(f"✅ Entrada registrada a las {hora_entrada}.")

# 🔹 Función para registrar la salida
async def salida(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    fecha = datetime.now().strftime("%Y-%m-%d")
    hora_salida = datetime.now().strftime("%H:%M:%S")

    try:
        docs = (
            db.collection("horas_extra")
            .where("usuario", "==", user_id)
            .where("fecha", "==", fecha)
            .order_by("hora_entrada", direction=firestore.Query.DESCENDING)
            .limit(1)
            .stream()
        )

        doc_ref = None
        data = None
        for doc in docs:
            doc_ref = db.collection("horas_extra").document(doc.id)
            data = doc.to_dict()
            break

        if doc_ref and data:
            hora_entrada = data.get("hora_entrada", None)

            if hora_entrada:
                fmt = "%H:%M:%S"
                entrada_dt = datetime.strptime(hora_entrada, fmt)
                salida_dt = datetime.strptime(hora_salida, fmt)

                total_trabajado = (salida_dt - entrada_dt).total_seconds() / 3600
                JORNADA_LABORAL = 8
                horas_extra = round(max(0, total_trabajado - JORNADA_LABORAL), 2)

                doc_ref.update({
                    "hora_salida": hora_salida,
                    "horas_extra": horas_extra
                })

                sheet_data = sheet.worksheet("Horas Extra")
                sheet_data.append_row([user_id, fecha, hora_entrada, hora_salida, horas_extra])

                await update.message.reply_text(
                    f"✅ Salida registrada a las {hora_salida}.\nHoras extra: {horas_extra:.2f}. Resumen actualizado."
                )
            else:
                await update.message.reply_text("⚠️ No se encontró una hora de entrada para hoy. Usa /entrada primero.")
        else:
            await update.message.reply_text("⚠️ No se encontró ninguna entrada para hoy. Usa /entrada primero.")

    except Exception as e:
        print(f"❌ Error en salida: {e}")
        await update.message.reply_text("⚠️ Error al registrar la salida. Inténtalo de nuevo más tarde.")

# 🔹 Función para verificar y enviar recordatorios
async def verificar_horas_extra(context: CallbackContext) -> None:
    ahora = datetime.now()
    dia_semana = ahora.weekday()  # Lunes = 0, Domingo = 6
    hora_actual = ahora.hour

    # Verifica si el horario es válido para enviar notificaciones
    if not ((0 <= dia_semana <= 4 and 15 <= hora_actual < 19) or (dia_semana == 5 and 13 <= hora_actual < 14)):
        print(f"⏳ Fuera del horario de notificaciones. No se enviarán recordatorios ahora.")
        return

    print(f"🔍 Verificando usuarios sin salida... {ahora.strftime('%H:%M:%S')}")

    usuarios = db.collection("horas_extra").stream()
    encontrados = 0

    for doc in usuarios:
        data = doc.to_dict()
        user_id = data.get("usuario")
        hora_entrada = data.get("hora_entrada")
        fecha = data.get("fecha")

        if "hora_salida" not in data or not data["hora_salida"]:
            encontrados += 1
            try:
                fecha_hora_entrada = datetime.strptime(f"{fecha} {hora_entrada}", "%Y-%m-%d %H:%M:%S")
            except ValueError:
                print(f"❌ Error al convertir la hora de entrada para el usuario {user_id}: {hora_entrada}")
                continue

            diferencia = ahora - fecha_hora_entrada
            tiempo_transcurrido = diferencia.total_seconds()

            # Enviar notificación solo si han pasado al menos 8 horas desde la entrada
            if tiempo_transcurrido >= 8 * 3600:
                print(f"⚠️ Enviando recordatorio a {user_id} - Diferencia: {tiempo_transcurrido:.2f} segundos")
                try:
                    await context.bot.send_message(chat_id=user_id, text="⚠️ Recuerda registrar tu salida con /salida")
                except telegram.error.BadRequest:
                    print(f"❌ No se pudo enviar mensaje a {user_id}. Chat no encontrado.")
                except Exception as e:
                    print(f"⚠️ Error inesperado con {user_id}: {e}")
            else:
                print(f"✅ Aún no han pasado 8 horas para el usuario {user_id}. No se envía notificación.")

    if encontrados == 0:
        print("✅ No se encontraron usuarios sin salida.")

# 🔹 Configurar el bot
def main():
    TOKEN = "7574046635:AAHY7LJT5jqliRcXOC-BIzv0K_7bsTPj6x0"

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("entrada", entrada))
    app.add_handler(CommandHandler("salida", salida))

    job_queue = app.job_queue
    job_queue.run_repeating(verificar_horas_extra, interval=1800, first=5)  # Cada 30 minutos

    print("✅ Bot iniciado correctamente...")
    app.run_polling()

if __name__ == "__main__":
    main()
