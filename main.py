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

# Thiết lập logging để kiểm tra lỗi chi tiết trên Railway
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ================= CẤU HÌNH =================
BOT_TOKEN = "8941322788:AAGn_DWqGXelA4FxTQDmJWRBTF02oikaSDQ"  # Thay bằng Token từ BotFather
CHANNEL_ID = -1007763690474             # ID Channel của bạn
DEFAULT_LANG = "en"                     # "en" cho Tiếng Anh, "zh" cho Tiếng Trung
# ============================================

file_storage = {}

MESSAGES = {
    "en": {
        "start": "👋 Welcome! Send me any file, photo, or video to save it.\nSend the code or name back to retrieve your file.",
        "file_saved": "✅ **File Saved!**\n\n📌 **Code:** `{code}`\n🏷 **Name:** `{name}`",
        "file_not_found": "❌ File not found. Please check your code or name.",
        "retrieving": "📥 Retrieving file, please wait...",
        "error": "⚠️ Failed to save file. Make sure the bot is an Admin in the Channel!"
    },
    "zh": {
        "start": "👋 欢迎使用！发送任何文件、图片或视频即可保存。\n发送提取码或名称即可取回文件。",
        "file_saved": "✅ **文件保存成功！**\n\n📌 **提取码:** `{code}`\n🏷 **名称:** `{name}`",
        "file_not_found": "❌ 未找到文件，请检查提取码或名称。",
        "retrieving": "📥 正在获取文件，请稍候...",
        "error": "⚠️ 保存失败，请确保 Bot 已添加为 Channel 的管理员！"
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
    try:
        # Forward tệp sang Channel riêng tư
        forwarded_msg = await message.forward(chat_id=CHANNEL_ID)
        
        # Lấy tên tuỳ chọn từ Caption nếu có
        custom_name = message.caption.strip() if message.caption else None
        code = generate_random_code()
        display_name = custom_name if custom_name else code
        
        # Lưu vết thông tin message_id
        file_storage[code.lower()] = {"message_id": forwarded_msg.message_id, "name": display_name}
        if custom_name:
            file_storage[custom_name.lower()] = {"message_id": forwarded_msg.message_id, "name": display_name}

        response_text = get_text("file_saved").format(code=code, name=display_name)
        await message.reply_markdown(response_text)

    except Exception as e:
        logger.error(f"Error handling media: {e}")
        await message.reply_text(get_text("error"))

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query_code = update.message.text.strip().lower()
    
    if query_code in file_storage:
        file_info = file_storage[query_code]
        await update.message.reply_text(get_text("retrieving"))
        try:
            await context.bot.copy_message(
                chat_id=update.effective_chat.id,
                from_chat_id=CHANNEL_ID,
                message_id=file_info["message_id"]
            )
        except Exception as e:
            logger.error(f"Error copying message: {e}")
            await update.message.reply_text("⚠️ Error retrieving file from channel.")
    else:
        await update.message.reply_text(get_text("file_not_found"))

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Đăng ký handler cho lệnh /start
    app.add_handler(CommandHandler("start", start_command))
    
    # Bắt tất cả các loại media (Hình ảnh, Video, Document, Voice, Audio, Sticker, Animation)
    app.add_handler(MessageHandler(filters.ALL & ~filters.TEXT & ~filters.COMMAND, handle_media))
    
    # Bắt tin nhắn chữ (để nhập mã nhận tệp)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    logger.info("Bot is starting polling...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
    
