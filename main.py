# main.py - البوت الفاخر النهائي (النسخة المتطورة)
import os
import re
import json
import asyncio
import random
import shutil
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp
from handlers.start import start
from handlers.message import handle_message
from keyboards.main_keyboard import *
from handlers.admin import *
from config import BOT_TOKEN, ADMIN_IDS, MAX_FILE_SIZE_MB, DOWNLOADS_PATH

# ==========post_init==========
async def post_init(app):
    await downloader.start()

# ========== استيراد الملفات الجديدة ==========
from downloader import Downloader
from metrics import Metrics
from security import is_safe_url, record_failed_attempt, is_user_blocked, get_failed_stats
from rate_limiter import RateLimiter

# ========== إعداد مجلد التحميلات (عشان Railway) ==========
if os.path.isfile(DOWNLOADS_PATH):
    os.remove(DOWNLOADS_PATH)
os.makedirs(DOWNLOADS_PATH, exist_ok=True)
START_TIME = datetime.now()

# ========== قاعدة بيانات ==========
from database.user_repository import *

# ========== معلومات الفيديو ==========
async def get_video_info(url):
    opts = {'quiet': True, 'no_warnings': True}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            duration = info.get('duration', 0)
            if duration:
                minutes = duration // 60
                seconds = duration % 60
                duration_str = f"{minutes}:{seconds:02d}"
            else:
                duration_str = "غير معروف"
            
            filesize = info.get('filesize_approx', 0)
            if filesize:
                size_mb = filesize / 1048576
                size_str = f"{size_mb:.1f} MB"
            else:
                size_str = "غير معروف"
            
            return {
                'title': info.get('title', 'غير معروف'),
                'duration': duration_str,
                'size': size_str,
            }
    except:
        return None

# ========== استخراج الرابط ==========
def extract_link(text):
    patterns = [
        r'(https?://(?:www\.)?tiktok\.com/[^\s]+)',
        r'(https?://vt\.tiktok\.com/[^\s]+)',
        r'(https?://(?:www\.)?youtube\.com/watch\?v=[^\s&]+)',
        r'(https?://youtu\.be/[^\s]+)',
        r'(https?://(?:www\.)?youtube\.com/shorts/[^\s]+)',
        r'(https?://(?:www\.)?instagram\.com/(?:p|reel|stories)/[^\s/?]+)',
        r'(https?://(?:www\.)?facebook\.com/(?:watch|reel|share|share/r)/[^\s]+)',
        r'(https?://fb\.watch/[^\s]+)',
        r'(https?://(?:www\.)?twitter\.com/[\w]+/status/[\d]+)',
        r'(https?://(?:www\.)?x\.com/[\w]+/status/[\d]+)',
        r'(https?://(?:www\.)?soundcloud\.com/[\w]+/[\w-]+)',
        r'(https?://(?:www\.)?spotify\.com/[\w]+/[\w-]+)',
        r'(https?://(?:www\.)?deezer\.com/[\w]+/[\w-]+)',
        r'(https?://[^\s]+)',
    ]
    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            return m.group(0)
    return None

def get_platform(url):
    if 'tiktok' in url:
        return 'TikTok'
    elif 'youtube' in url or 'youtu.be' in url:
        return 'YouTube'
    elif 'instagram' in url:
        return 'Instagram'
    elif 'facebook.com' in url or 'fb.watch' in url:
        return 'Facebook'
    elif 'twitter.com' in url or 'x.com' in url:
        return 'Twitter'
    elif 'soundcloud' in url:
        return 'SoundCloud'
    elif 'spotify' in url:
        return 'Spotify'
    elif 'deezer' in url:
        return 'Deezer'
    else:
        return 'Website'

# ========== دوال التحميل ==========
async def download_tiktok(url):
    opts = {
        'outtmpl': f'{DOWNLOADS_PATH}/tiktok_%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {'tiktok': {'without_watermark': ['true']}},
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info), info.get('title', 'TikTok')
    except:
        opts['impersonate'] = 'chrome-120'
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info), info.get('title', 'TikTok')

async def download_facebook(url):
    opts = {
        'outtmpl': f'{DOWNLOADS_PATH}/facebook_%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'format': 'best',
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info), info.get('title', 'Facebook')

async def download_other(url, quality='720', audio=False):
    quality_map = {
        '144': 'worst[height<=144]',
        '240': 'best[height<=240]',
        '360': 'best[height<=360]',
        '480': 'best[height<=480]',
        '720': 'best[height<=720]',
        '1080': 'best[height<=1080]',
    }
    
    if audio:
        opts = {
            'outtmpl': f'{DOWNLOADS_PATH}/%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}],
        }
    else:
        fmt = quality_map.get(quality, 'best[height<=720]')
        opts = {
            'outtmpl': f'{DOWNLOADS_PATH}/%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'format': fmt,
            'merge_output_format': 'mp4',
        }
    
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        path = ydl.prepare_filename(info)
        if audio:
            path = path.rsplit('.', 1)[0] + '.mp3'
        return path, info.get('title', 'Media')

async def download_media(url, quality='720', audio=False):
    if 'tiktok.com' in url or 'vt.tiktok.com' in url:
        return await download_tiktok(url)
    elif 'facebook.com' in url or 'fb.watch' in url:
        return await download_facebook(url)
    else:
        return await download_other(url, quality, audio)

# ========== معالجة الأزرار ==========
async def callback(update, context):
    q = update.callback_query
    await q.answer()
    u = update.effective_user.id
    
    if q.data.startswith('q_'):
        val = q.data[2:]
        if val == 'audio':
            context.user_data['audio'] = True
            await q.edit_message_text("🎵 وضع الصوت مفعل", parse_mode='Markdown')
        else:
            context.user_data['quality'] = val
            context.user_data['audio'] = False
            await q.edit_message_text(f"⚡ الجودة {val}p", parse_mode='Markdown')
    
    elif q.data == 'quality_menu':
        await q.edit_message_text("⚡ *اختر الجودة:*", parse_mode='Markdown', reply_markup=quality_keyboard())
    
    elif q.data == 'share_bot':
        bot = await context.bot.get_me()
        await q.edit_message_text(f"🎁 `https://t.me/{bot.username}`\n\n{SIGNATURE}", parse_mode='Markdown')
    
    elif q.data == 'my_stats':
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
        user_data = data['users'].get(str(u), {})
        remaining = rate_limiter.get_remaining(u)
        await q.edit_message_text(f"📥 {user_data.get('downloads', 0)}\n🌍 {data['total']}\n📊 طلبات متبقية: {remaining}", parse_mode='Markdown')
    
    elif q.data == 'admin_panel':
        if is_admin(u):
            await q.edit_message_text("👑 *لوحة الأدمن*", parse_mode='Markdown', reply_markup=admin_panel())
        else:
            await q.edit_message_text("⛔ غير مصرح")
    
    elif q.data == 'admin_stats':
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
        await q.edit_message_text(f"👥 {len(data['users'])}\n📥 {data['total']}\n📈 {data['daily']}", reply_markup=admin_panel())
    
    elif q.data == 'admin_top':
        top_users = get_top_users(10)
        if not top_users:
            await q.edit_message_text("🏆 لا يوجد", reply_markup=admin_panel())
            return
        text = "👑 *الترتيب*\n"
        for i, (uid, info) in enumerate(top_users, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}️⃣"
            text += f"{medal} {info.get('name', 'Unknown')}\n   📥 {info.get('downloads', 0)}\n"
        await q.edit_message_text(text, parse_mode='Markdown', reply_markup=admin_panel())
    
    elif q.data == 'admin_broadcast':
        await q.edit_message_text("📢 /broadcast رسالة")
    
    elif q.data == 'admin_users':
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
        txt = "👥 *المستخدمين*\n"
        for uid, info in list(data['users'].items())[:20]:
            status = "🚫" if info.get("blocked", False) else "✅"
            txt += f"• {info.get('name', 'Unknown')} {status}\n   📥 {info.get('downloads', 0)}\n"
        await q.edit_message_text(txt, parse_mode='Markdown')
    
    elif q.data == 'admin_block':
        await q.edit_message_text("🚫 /block <user_id>")
    
    elif q.data == 'admin_unblock':
        await q.edit_message_text("🔓 /unblock <user_id>")
    
    elif q.data == 'admin_clear':
        c = 0
        for f in os.listdir(DOWNLOADS_PATH):
            try:
                os.remove(os.path.join(DOWNLOADS_PATH, f))
                c += 1
            except:
                pass
        await q.edit_message_text(f"🗑️ {c} ملف", reply_markup=admin_panel())
    
    elif q.data == 'admin_delete_all':
        await delete_all_users_cmd(update, context)
    
    elif q.data == 'admin_uptime':
        await q.edit_message_text(f"⏱️ {get_uptime()}", reply_markup=admin_panel())
    
    elif q.data == 'admin_backup':
        await backup_cmd(update, context)
    
    elif q.data == 'admin_metrics':
        await admin_metrics_cmd(update, context)
    
    elif q.data == 'help_video':
        await q.edit_message_text("🎬 أرسل رابط الفيديو", parse_mode='Markdown')
    
    elif q.data == 'help_audio':
        await q.edit_message_text("🎵 /audio ثم الرابط", parse_mode='Markdown')
    
    elif q.data == 'help':
        await q.edit_message_text(
            "📌 *المساعدة*\n━━━━━━━━━━━━━━━━━━━\n🎬 تحميل: أرسل الرابط\n🎵 صوت: /audio ثم الرابط\n⚡ جودة: اختر من القائمة\n📊 إحصائيات: /stats\n🎁 مشاركة: /share\n🔒 خصوصية: /privacy\n🗑️ مسح بياناتي: /delete_my_data",
            parse_mode='Markdown'
        )
    
    elif q.data == 'back':
        kb = admin_keyboard() if is_admin(u) else main_keyboard()
        await q.edit_message_text("🖤 *القائمة الرئيسية*", reply_markup=kb, parse_mode='Markdown')

# ========== التشغيل ==========
async def start_downloader():
    await downloader.start()

def main():
    init_db()
    
    # تشغيل downloader في حدث asyncio منفصل
    
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("=" * 60)
    print(f"✨ {SIGNATURE} ✨")
    print("🔥 البوت المتطور شغال يا باشا!")
    print(f"👑 الأدمن: {ADMIN_IDS}")
    print("🌍 بينزل أي حاجة من أي موقع")
    print("📊 نظام Queue و Rate Limiting مفعل")
    print("🔒 نظام أمان متقدم مفعل")
    print("=" * 60)
    app.run_polling()

if __name__ == "__main__":
    main()
