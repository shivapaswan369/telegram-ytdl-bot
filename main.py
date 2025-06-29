import os, logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")                   # Render → Environment
ALLOWED_CHANNELS = os.getenv("ALLOWED_CHANNELS", "1002566377076").split(",")

MAX_SIZE_MB = 1900
QUALITY_MAP = {"360p":360,"480p":480,"720p":720,"1080p":1080,"2k":1440,"4k":2160}

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("ShivaBot")

def yt_cmd(url:str,h:int)->str:
    fmt=f"bestvideo[height<={h}]+bestaudio/best[height<={h}]"
    return (f'yt-dlp --geo-bypass --geo-bypass-country US '
            f'--cookies cookies.txt -f "{fmt}" -o "%(title)s.%(ext)s" "{url}"')

def allowed(chat_id): return (not ALLOWED_CHANNELS) or str(chat_id) in ALLOWED_CHANNELS

async def start(update:Update,ctx:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Use /add <URL> <quality> e.g. 480p")

async def add(update:Update,ctx:ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if not allowed(cid):
        return await update.message.reply_text("⛔ Not allowed.")
    if len(ctx.args)<2:
        return await update.message.reply_text("⚠️ /add <url> <quality>")
    url,q = ctx.args[0],ctx.args[1].lower()
    h = QUALITY_MAP.get(q.rstrip("p"))
    if not h:
        return await update.message.reply_text("❌ Bad quality.")
    await update.message.reply_text("📥 Downloading…")
    if os.system(yt_cmd(url,h)): return await update.message.reply_text("❌ DL failed.")
    vid = next((f for f in os.listdir(".") if f.endswith((".mp4",".mkv",".webm"))),None)
    if not vid: return await update.message.reply_text("❌ File missing.")
    if os.path.getsize(vid) > MAX_SIZE_MB*1024*1024:
        os.remove(vid); return await update.message.reply_text("❌ Too large.")
    await update.message.reply_text("📤 Uploading…")
    try:
        with open(vid,"rb") as v: await ctx.bot.send_video(chat_id=cid,video=v)
        await update.message.reply_text("✅ Done!")
    finally:
        if os.path.exists(vid): os.remove(vid)

def main():
    port = int(os.getenv("PORT","10000"))
    host = os.getenv("RENDER_EXTERNAL_HOSTNAME","localhost")
    pub  = f"https://{host}/{BOT_TOKEN}"
    app  = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",start))
    app.add_handler(CommandHandler("add",add))
    log.info("Bot webhook on %s",port)
    app.run_webhook(listen="0.0.0.0",port=port,url_path=BOT_TOKEN,webhook_url=pub)

if __name__=="__main__": main()
