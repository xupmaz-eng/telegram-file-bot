import logging
import random
import string
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ================= CẤU HÌNH =================
BOT_TOKEN = "ĐIỀN_TOKEN_BOT_CỦA_BẠN"
CHANNEL_ID = -1001234567890  # ĐIỀN_ID_CHANNEL_CỦA_BẠN
DEFAULT_LANG = "en"  # "en" cho Tiếng Anh, "zh" cho Tiếng Trung
# ============================================

file_storage = {}

MESSAGES = {
    "en": {
        "start": "👋 Send me any file/photo/video to save it.\nSend the code back to retrieve your file.",
        "file_saved": "✅ **File Saved!**\n\n📌 **Code:** `{code}`\n🏷 **Name:** `{name}`",
        "file_not_found": "❌ File not found. Check your code or name.",
        "retrieving": "📥 Retrieving file, please wait...",
    },
    "zh": {
        "start": "👋 发送任何文件/图片/视频即可保存。\n发送提取码即可取回文件。",
        "file_saved": "✅ **文件保存成功！**\n\n📌 **提取码:** `{code}`\n🏷 **名称:** `{name}`",
        "file_not_found": "❌ 未找到文件，请检查提取码或名称。",
        "retrieving": "📥 正在获取文件，请稍候...",
    }
}

def get_text(key: str, lang: str = DEFAULT_LANG) -> str:
    return MESSAGES.get(lang, MESSAGES["en"]).get(key, "")

def generate_random_code(length: int = 6) -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_text("start"))

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    forwarded_msg = await message.forward(chat_id=CHANNEL_ID)
    
    custom_name = message.caption.strip() if message.caption else None
    code = generate_random_code()
    display_name = custom_name if custom_name else code
    
    file_storage[code.lower()] = {"message_id": forwarded_msg.message_id, "name": display_name}
    if custom_name:
        file_storage[custom_name.lower()] = {"message_id": forwarded_msg.message_id, "name": display_name}

    response_text = get_text("file_saved").format(code=code, name=display_name)
    await message.reply_markdown(response_text)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query_code = update.message.text.strip().lower()
    if query_code in file_storage:
        file_info = file_storage[query_code]
        await update.message.reply_text(get_text("retrieving"))
        await context.bot.copy_message(
            chat_id=update.effective_chat.id,
            from_chat_id=CHANNEL_ID,
            message_id=file_info["message_id"]
        )
    else:
        await update.message.reply_text(get_text("file_not_found"))

def main():
    logging.basicConfig(level=logging.INFO)
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    
    media_filter = filters.PHOTO | filters.VIDEO | filters.Document.ALL | filters.AUDIO
    app.add_handler(MessageHandler(media_filter, handle_media))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    app.run_polling()

if __name__ == "__main__":
    main()
  
