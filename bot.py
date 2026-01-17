import os
import subprocess
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputFile,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ======================
# CONFIG
# ======================
import os

BOT_TOKEN = os.environ.get("8032087011:AAEdbFLiIf8UcEwDuhycy6Cql4f6rJJFLsk")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")


DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ======================
# TEXTS (UZ default)
# ======================
TEXT = {
    "start": (
        "📥 *Media yuklab oluvchi bot*\n\n"
        "Quyidagi saytlardan *ochiq link* yuboring:\n"
        "YouTube / Instagram / Facebook / TikTok\n\n"
        "Keyin formatni tanlang."
    ),
    "choose": "Yuklab olish formatini tanlang:",
    "downloading": "⏳ Yuklab olinmoqda, iltimos kuting...",
    "failed": "❌ Yuklab olishda xatolik yuz berdi.",
}

# ======================
# HELPERS
# ======================
def is_supported_link(text: str) -> bool:
    sites = (
        "youtube.com",
        "youtu.be",
        "instagram.com",
        "facebook.com",
        "fb.watch",
        "tiktok.com",
    )
    return any(site in text for site in sites)


def download_media(url: str, mode: str) -> str | None:
    output_template = os.path.join(DOWNLOAD_DIR, "%(title).80s.%(ext)s")

    base_cmd = [
        "yt-dlp",
        "-o",
        output_template,
        "--no-playlist",
    ]

    if mode == "audio":
        cmd = base_cmd + [
            "-x",
            "--audio-format",
            "mp3",
            url,
        ]
    else:
        cmd = base_cmd + [
            "-f",
            "mp4",
            url,
        ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if result.returncode != 0:
        return None

    files = sorted(
        os.listdir(DOWNLOAD_DIR),
        key=lambda f: os.path.getmtime(os.path.join(DOWNLOAD_DIR, f)),
        reverse=True,
    )

    if not files:
        return None

    return os.path.join(DOWNLOAD_DIR, files[0])


# ======================
# HANDLERS
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        TEXT["start"],
        parse_mode="Markdown",
    )


async def link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if not is_supported_link(text):
        return

    context.user_data["link"] = text

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🎵 Audio (MP3)", callback_data="audio"),
                InlineKeyboardButton("🎥 Video (MP4)", callback_data="video"),
            ]
        ]
    )

    await update.message.reply_text(
        TEXT["choose"],
        reply_markup=keyboard,
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    link = context.user_data.get("link")
    if not link:
        await query.message.reply_text(TEXT["failed"])
        return

    mode = query.data
    await query.message.reply_text(TEXT["downloading"])

    file_path = download_media(link, mode)

    if not file_path or not os.path.exists(file_path):
        await query.message.reply_text(TEXT["failed"])
        return

    if mode == "audio":
        await query.message.reply_audio(InputFile(file_path))
    else:
        await query.message.reply_video(InputFile(file_path))

    os.remove(file_path)


# ======================
# MAIN
# ======================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, link_handler))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("✅ Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
