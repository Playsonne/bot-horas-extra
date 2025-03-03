import asyncio
import telegram

TOKEN = "7574046635:AAHY7LJT5jqliRcXOC-BIzv0K_7bsTPj6x0"  # Reemplaza con tu token real
USER_ID = 5432495959  # Reemplaza con tu ID real

async def verificar_usuario():
    bot = telegram.Bot(TOKEN)
    
    try:
        chat = await bot.get_chat(USER_ID)
        print(f"✅ Usuario válido: {chat.id}. Se puede enviar mensaje.")
        await bot.send_message(chat_id=USER_ID, text="🚀 Este es un mensaje de prueba desde Python.")
    except telegram.error.BadRequest:
        print("❌ Error: El usuario no ha iniciado el bot o el ID es incorrecto.")
    except Exception as e:
        print(f"⚠️ Error inesperado: {e}")

# Ejecutar la función asincrónica
asyncio.run(verificar_usuario())
