import os
import requests
import telebot

# 🔹 CONFIGURACIÓN DEL BOT
TOKEN = "7679416003:AAFT1rR5HHeWXXsC_fDgv4FCSB9_lXAfUgQ"  # Obtenlo en @BotFather
USER_ID = "5328074487"  # Obtenlo en @userinfobot
bot = telebot.TeleBot(TOKEN)

# 🔹 Diccionario para almacenar el estado de cada usuario
user_states = {}

### 📌 COMANDO /NEW (CREAR NUEVO PAQUETE) ###
@bot.message_handler(commands=['new'])
def start_new_pack(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "✏️ ¿Cómo quieres llamar a tu paquete de stickers?")
    user_states[chat_id] = {'step': 'awaiting_name'}

@bot.message_handler(func=lambda message: message.chat.id in user_states and user_states[message.chat.id]['step'] == 'awaiting_name')
def receive_pack_name(message):
    chat_id = message.chat.id
    raw_name = message.text.replace(" ", "_")
    sticker_set_name = f"{raw_name}_by_{bot.get_me().username}"
    user_states[chat_id]['sticker_set_name'] = sticker_set_name
    user_states[chat_id]['sticker_title'] = message.text
    user_states[chat_id]['step'] = 'awaiting_first_webm'

    bot.send_message(chat_id, "📤 Ahora envíame el primer archivo `.webm` para crear el paquete.")

### 📥 RECIBE EL PRIMER STICKER PARA CREAR EL PAQUETE ###
@bot.message_handler(content_types=['document'])
def handle_webm(message):
    chat_id = message.chat.id

    if chat_id in user_states:
        step = user_states[chat_id]['step']

        if step in ['awaiting_first_webm', 'awaiting_webms']:  
            file_info = bot.get_file(message.document.file_id)
            file_path = file_info.file_path
            file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"

            webm_filename = f"sticker_{message.document.file_id}.webm"
            download_file(file_url, webm_filename)

            sticker_set_name = user_states[chat_id]['sticker_set_name']

            if step == 'awaiting_first_webm':
                sticker_title = user_states[chat_id]['sticker_title']
                create_sticker_set(sticker_set_name, sticker_title, webm_filename, chat_id)
                del user_states[chat_id]  # ✅ Borra el estado después de crear el paquete

            elif step == 'awaiting_webms':
                add_sticker(sticker_set_name, webm_filename, chat_id)

    else:
        bot.send_message(chat_id, "❌ No estás creando ni actualizando un paquete.")

### 📌 ELIGE UN PAQUETE ENVIANDO UN STICKER ###
@bot.message_handler(content_types=['sticker'])
def choose_sticker_pack(message):
    chat_id = message.chat.id
    sticker_set_name = message.sticker.set_name  

    if not sticker_set_name:
        bot.send_message(chat_id, "❌ Este sticker no pertenece a un paquete válido.")
        return

    user_states[chat_id] = {'step': 'awaiting_webms', 'sticker_set_name': sticker_set_name}
    bot.send_message(chat_id, f"📤 Has seleccionado el paquete `{sticker_set_name}`.\n\nAhora envíame los archivos `.webm` y usa `/fin` cuando termines.", parse_mode="Markdown")

### 📌 COMANDO /FIN (ANTES ERA /FINISH) ###
@bot.message_handler(commands=['fin'])
def finish_update(message):
    chat_id = message.chat.id

    if chat_id not in user_states or user_states[chat_id]['step'] != 'awaiting_webms':
        bot.send_message(chat_id, "❌ No estás actualizando un paquete. Envía un sticker primero.")
        return

    sticker_set_name = user_states[chat_id]['sticker_set_name']
    total_stickers = count_stickers(sticker_set_name)
    bot.send_message(chat_id, f"✅ ¡Listo! Ahora el paquete `{sticker_set_name}` tiene {total_stickers} stickers.", parse_mode="Markdown")

    del user_states[chat_id]

### 📌 COMANDO /PIN (FIJAR MENSAJE) ###
@bot.message_handler(commands=['pin'])
def pin_message(message):
    chat_id = message.chat.id

    # 📌 Mensaje con el link que quieres fijar
    msg_text = "📌 Activa el bot aquí: [Replit](https://replit.com/@putojajalol/hi)"

    # 🔹 Enviar el mensaje con formato Markdown
    msg = bot.send_message(chat_id, msg_text, parse_mode="Markdown")

    # 🔹 Intentar fijar el mensaje automáticamente
    try:
        bot.pin_chat_message(chat_id, msg.message_id)
        bot.send_message(chat_id, "✅ Mensaje fijado correctamente.")
    except Exception as e:
        bot.send_message(chat_id, f"❌ No se pudo fijar el mensaje: {str(e)}")

### 📥 FUNCIONES AUXILIARES ###
def count_stickers(sticker_set_name):
    url = f"https://api.telegram.org/bot{TOKEN}/getStickerSet"
    response = requests.get(url, params={"name": sticker_set_name})

    if response.json().get("ok"):
        return len(response.json()["result"]["stickers"])
    return 0

def download_file(url, output_filename):
    response = requests.get(url)
    with open(output_filename, "wb") as f:
        f.write(response.content)
    print("✅ Archivo descargado.")

def create_sticker_set(sticker_set_name, sticker_title, webm_file, chat_id, emoji="🔥"):
    url = f"https://api.telegram.org/bot{TOKEN}/createNewStickerSet"

    with open(webm_file, "rb") as sticker:
        files = {"webm_sticker": sticker}
        data = {
            "user_id": USER_ID,
            "name": sticker_set_name,
            "title": sticker_title,
            "emojis": emoji,
            "sticker_format": "video"
        }
        response = requests.post(url, data=data, files=files)

    if response.json().get("ok"):
        sticker_link = f"https://t.me/addstickers/{sticker_set_name}"
        bot.send_message(chat_id, f"✅ Paquete creado: [¡Agrégalo aquí!]({sticker_link})", parse_mode="Markdown")

        # 📤 Enviar el sticker al chat
        bot.send_sticker(chat_id, sticker=open(webm_file, "rb"))

    else:
        bot.send_message(chat_id, f"❌ Error al crear el paquete `{sticker_set_name}`:\n{response.json()}", parse_mode="Markdown")

def add_sticker(sticker_set_name, webm_file, chat_id, emoji="🔥"):
    total_stickers = count_stickers(sticker_set_name)

    if total_stickers >= 50:
        bot.send_message(chat_id, f"❌ No se puede agregar más stickers. El paquete `{sticker_set_name}` ya tiene 50 stickers.", parse_mode="Markdown")
        return

    url = f"https://api.telegram.org/bot{TOKEN}/addStickerToSet"

    with open(webm_file, "rb") as sticker:
        files = {"webm_sticker": sticker}
        data = {
            "user_id": USER_ID,
            "name": sticker_set_name,
            "emojis": emoji
        }
        response = requests.post(url, data=data, files=files)

    if response.json().get("ok"):
        total_stickers += 1
        bot.send_message(chat_id, f"✅ Sticker guardado en `{sticker_set_name}`.\n📦 Ahora tiene `{total_stickers}` stickers.", parse_mode="Markdown")

        # 📤 Enviar el sticker al chat
        bot.send_sticker(chat_id, sticker=open(webm_file, "rb"))

    else:
        error_message = response.json()
        bot.send_message(chat_id, f"❌ Error al agregar el sticker `{webm_file}`:\n{error_message}", parse_mode="Markdown")

print("🤖 Bot en ejecución...")
bot.polling(none_stop=True)
