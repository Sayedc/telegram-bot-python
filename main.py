# main.py - أضخم بوت في الشرق الأوسط والعالم
import os
import re
import json
import asyncio
import shutil
import subprocess
from datetime import datetime, timedelta
from threading import Thread
from queue import Queue
import hashlib
import zipfile
from PIL import Image
import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

from config import BOT_TOKEN, ADMIN_IDS, MAX_FILE_SIZE_MB, DOWNLOADS_PATH

# ========== إعدادات أولية ==========
os.makedirs(DOWNLOADS_PATH, exist_ok=True)

SIGNATURE = "✨ 𝓐𝓵𝓱𝓪𝔀𝔂 ✨"
VERSION = "ULTIMATE_10.0"
BOT_NAME = "𝐀𝐋𝐇𝐀𝐖𝐘 𝐀𝐈 𝐁𝐎𝐓"

# ========== ردود مصرية متنوعة ==========
WELCOME_RESPONSES = [
    "🎬 اهلاً بيك يا باشا {name}! نورت البوت الفاخر 🤍",
    "💫 أهلاً وسهلاً يا فنان {name}! ده البوت اللي ملهوش حل 🌟",
    "🔥 يا مرحبا بيك يا كبير {name}! البوت تحت أمرك 24 ساعة 😎",
]

PROCESSING_RESPONSES = [
    "⚡ شوية صبر يا حبيب قلبى، البوت بيشتغل بسرعه الضوء... 🎬",
    "🔥 على توكل على الله، احنا بنحمل الفيديو بأعلى جودة... 💫",
]

def get_response(responses, name=None):
    text = responses[datetime.now().second % len(responses)]
    return text.format(name=name) if name else text

# ========== قاعدة بيانات متقدمة ==========
DB_FILE = "bot_database.json"

def init_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f:
            json.dump({
                "users": {},
                "stats": {"total_downloads": 0, "today": 0, "last_date": str(datetime.now().date())},
                "platforms": {},
                "recent": []
            }, f, indent=2)

def save_user(user_id, username):
    with open(DB_FILE, 'r+') as f:
        data = json.load(f)
        if str(user_id) not in data["users"]:
            data["users"][str(user_id)] = {
                "name": username,
                "first": str(datetime.now()),
                "downloads": 0,
                "history": [],
                "fav_quality": "720",
                "invited": 0,
                "invited_by": None
            }
            f.seek(0)
            json.dump(data, f, indent=2)

def update_user(user_id, platform="unknown"):
    with open(DB_FILE, 'r+') as f:
        data = json.load(f)
        if str(user_id) in data["users"]:
            data["users"][str(user_id)]["downloads"] += 1
            data["stats"]["total_downloads"] += 1
            data["stats"]["today"] += 1
            data["platforms"][platform] = data["platforms"].get(platform, 0) + 1
            data["recent"].insert(0, {"user": user_id, "time": str(datetime.now()), "platform": platform})
            data["recent"] = data["recent"][:50]
            f.seek(0)
            json.dump(data, f, indent=2)

def get_all_users():
    with open(DB_FILE, 'r') as f:
        return list(json.load(f)["users"].keys())

def is_admin(user_id):
    return user_id in ADMIN_IDS

# ========== أزرار فخمة جداً ==========
def main_keyboard():
    keyboard = [
        [InlineKeyboardButton("🎬 ✦ تحميل فيديو ✦", callback_data="help_video"),
         InlineKeyboardButton("🎵 ✦ استخراج صوت ✦", callback_data="help_audio")],
        [InlineKeyboardButton("⚡ ✦ اختيار الجودة ✦", callback_data="quality_menu"),
         InlineKeyboardButton("🎁 ✦ مشاركة البوت ✦", callback_data="share_bot")],
        [InlineKeyboardButton("📊 ✦ إحصائياتي ✦", callback_data="my_stats"),
         InlineKeyboardButton("🌍 ✦ منصات متعددة ✦", callback_data="platforms_menu")],
        [InlineKeyboardButton("📥 ✦ تحميل جماعي ✦", callback_data="batch_download"),
         InlineKeyboardButton("⏰ ✦ تحميل مجدول ✦", callback_data="schedule_menu")],
        [InlineKeyboardButton("🖼️ ✦ استخراج صور ✦", callback_data="extract_frames"),
         InlineKeyboardButton("🎞️ ✦ تحويل GIF ✦", callback_data="to_gif")],
        [InlineKeyboardButton("📜 ✦ ترجمة نصية ✦", callback_data="get_subs"),
         InlineKeyboardButton("ℹ️ ✦ معلومات الفيديو ✦", callback_data="video_info")],
        [InlineKeyboardButton("🔗 ✦ روابط مختصرة ✦", callback_data="shorten_url"),
         InlineKeyboardButton("💾 ✦ حفظ في السحابة ✦", callback_data="save_cloud")],
        [InlineKeyboardButton("📤 ✦ تحميل من رابط ✦", callback_data="custom_url"),
         InlineKeyboardButton("🔄 ✦ تحويل صيغة ✦", callback_data="convert_format")],
        [InlineKeyboardButton("❓ ✦ المساعدة ✦", callback_data="help"),
         InlineKeyboardButton("📢 ✦ أخبار البوت ✦", callback_data="news")],
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("👑 ✦ لوحة التحكم الشاملة ✦", callback_data="admin_panel")],
        [InlineKeyboardButton("🎬 ✦ تحميل فيديو ✦", callback_data="help_video")],
        [InlineKeyboardButton("🎵 ✦ استخراج صوت ✦", callback_data="help_audio")],
        [InlineKeyboardButton("⚡ ✦ اختيار الجودة ✦", callback_data="quality_menu")],
        [InlineKeyboardButton("🎁 ✦ مشاركة البوت ✦", callback_data="share_bot")],
        [InlineKeyboardButton("📊 ✦ إحصائياتي ✦", callback_data="my_stats")],
        [InlineKeyboardButton("🌍 ✦ منصات متعددة ✦", callback_data="platforms_menu")],
        [InlineKeyboardButton("📥 ✦ تحميل جماعي ✦", callback_data="batch_download")],
        [InlineKeyboardButton("⏰ ✦ تحميل مجدول ✦", callback_data="schedule_menu")],
        [InlineKeyboardButton("❓ ✦ المساعدة ✦", callback_data="help")],
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_panel_full():
    keyboard = [
        [InlineKeyboardButton("📊 ✦ إحصائيات شاملة ✦", callback_data="admin_full_stats")],
        [InlineKeyboardButton("📢 ✦ إعلان للجميع ✦", callback_data="admin_broadcast")],
        [InlineKeyboardButton("👥 ✦ قائمة المستخدمين ✦", callback_data="admin_users_list")],
        [InlineKeyboardButton("🗑️ ✦ تنظيف الكاش ✦", callback_data="admin_clear_cache")],
        [InlineKeyboardButton("📈 ✦ تقرير يومي ✦", callback_data="admin_daily_report")],
        [InlineKeyboardButton("🔄 ✦ إعادة تشغيل البوت ✦", callback_data="admin_restart")],
        [InlineKeyboardButton("📤 ✦ نسخ احتياطي ✦", callback_data="admin_backup")],
        [InlineKeyboardButton("🚫 ✦ حظر مستخدم ✦", callback_data="admin_block_user")],
        [InlineKeyboardButton("🔙 ✦ رجوع ✦", callback_data="back")],
    ]
    return InlineKeyboardMarkup(keyboard)

def quality_keyboard_full():
    keyboard = [
        [InlineKeyboardButton("📱 144p", callback_data="q_144"),
         InlineKeyboardButton("📱 240p", callback_data="q_240"),
         InlineKeyboardButton("📱 360p", callback_data="q_360")],
        [InlineKeyboardButton("📺 480p", callback_data="q_480"),
         InlineKeyboardButton("📺 720p 🔥", callback_data="q_720"),
         InlineKeyboardButton("📺 1080p 👑", callback_data="q_1080")],
        [InlineKeyboardButton("🎬 4K (إن وجدت)", callback_data="q_2160"),
         InlineKeyboardButton("🎵 صوت MP3 (320kbps)", callback_data="q_audio")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back")],
    ]
    return InlineKeyboardMarkup(keyboard)

def platforms_keyboard():
    keyboard = [
        [InlineKeyboardButton("🎵 TikTok", callback_data="platform_tiktok"),
         InlineKeyboardButton("🎬 YouTube", callback_data="platform_youtube")],
        [InlineKeyboardButton("📸 Instagram", callback_data="platform_instagram"),
         InlineKeyboardButton("📘 Facebook", callback_data="platform_facebook")],
        [InlineKeyboardButton("🐦 Twitter/X", callback_data="platform_twitter"),
         InlineKeyboardButton("🔴 Reddit", callback_data="platform_reddit")],
        [InlineKeyboardButton("🎶 SoundCloud", callback_data="platform_soundcloud"),
         InlineKeyboardButton("📹 Vimeo", callback_data="platform_vimeo")],
        [InlineKeyboardButton("🎮 Twitch", callback_data="platform_twitch"),
         InlineKeyboardButton("📌 Pinterest", callback_data="platform_pinterest")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== استخراج الرابط بذكاء ==========
def extract_link(text):
    patterns = [
        r'(https?://(?:www\.)?tiktok\.com/[^\s]+)',
        r'(https?://vt\.tiktok\.com/[^\s]+)',
        r'(https?://(?:www\.)?youtube\.com/watch\?v=[^\s&]+)',
        r'(https?://youtu\.be/[^\s]+)',
        r'(https?://(?:www\.)?youtube\.com/shorts/[^\s]+)',
        r'(https?://(?:www\.)?instagram\.com/(?:p|reel|stories)/[^\s/?]+)',
        r'(https?://(?:www\.)?facebook\.com/(?:watch|reel|share)/[^\s]+)',
        r'(https?://(?:www\.)?fb\.watch/[^\s]+)',
        r'(https?://(?:www\.)?twitter\.com/[\w]+/status/[\d]+)',
        r'(https?://(?:www\.)?x\.com/[\w]+/status/[\d]+)',
        r'(https?://(?:www\.)?reddit\.com/r/[\w]+/comments/[\w]+)',
        r'(https?://(?:www\.)?soundcloud\.com/[\w]+/[\w-]+)',
        r'(https?://(?:www\.)?vimeo\.com/[\d]+)',
        r'(https?://(?:www\.)?twitch\.tv/[\w]+/clip/[\w]+)',
        r'(https?://(?:www\.)?pinterest\.com/pin/[\d]+)',
        r'(https?://(?:bit\.ly|tinyurl\.com|short\.link)/[\w]+)',
        r'(https?://[^\s]+)',
    ]
    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            url = m.group(0)
            if 'bit.ly' in url or 'tinyurl' in url:
                try:
                    r = requests.head(url, allow_redirects=True, timeout=5)
                    url = r.url
                except:
                    pass
            return url
    return None

def get_platform(url):
    if 'tiktok' in url:
        return 'TikTok'
    elif 'youtube' in url or 'youtu.be' in url:
        return 'YouTube'
    elif 'instagram' in url:
        return 'Instagram'
    elif 'facebook' in url or 'fb.watch' in url:
        return 'Facebook'
    elif 'twitter' in url or 'x.com' in url:
        return 'Twitter'
    elif 'reddit' in url:
        return 'Reddit'
    elif 'soundcloud' in url:
        return 'SoundCloud'
    elif 'vimeo' in url:
        return 'Vimeo'
    elif 'twitch' in url:
        return 'Twitch'
    elif 'pinterest' in url:
        return 'Pinterest'
    else:
        return 'Website'

# ========== تحميل تيك توك بدون علامة مائية ==========
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
            return ydl.prepare_filename(info), info.get('title', 'TikTok Video')
    except:
        opts['impersonate'] = 'chrome-120'
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info), info.get('title', 'TikTok Video')
        except:
            import requests
            vid_match = re.search(r'/video/(\d+)', url)
            if not vid_match:
                vid_match = re.search(r'/(\d+)', url)
            if vid_match:
                vid = vid_match.group(1)
                try:
                    r = requests.get(f'https://tiksave.io/api/action?url=https://www.tiktok.com/@user/video/{vid}', timeout=10)
                    if r.status_code == 200:
                        data = r.json()
                        if data.get('video_url'):
                            path = f'{DOWNLOADS_PATH}/tiktok_{vid}.mp4'
                            vr = requests.get(data['video_url'], stream=True)
                            with open(path, 'wb') as f:
                                for chunk in vr.iter_content(8192):
                                    f.write(chunk)
                            return path, f'TikTok Video {vid}'
                except:
                    pass
            raise Exception("TikTok download failed")

# ========== تحميل عام متطور ==========
async def download_media(url, quality=None, audio=False):
    if 'tiktok' in url:
        return await download_tiktok(url)
    
    quality_map = {
        '144': 'worstvideo[height<=144]+worstaudio/best[height<=144]',
        '240': 'best[height<=240]',
        '360': 'best[height<=360]',
        '480': 'best[height<=480]',
        '720': 'best[height<=720]',
        '1080': 'best[height<=1080]',
        '2160': 'best[height<=2160]',
    }
    
    if audio:
        opts = {
            'outtmpl': f'{DOWNLOADS_PATH}/%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '320'}],
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

# ========== الحصول على معلومات الفيديو ==========
async def get_video_info(url):
    opts = {'quiet': True, 'extract_flat': False}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            'title': info.get('title', 'N/A'),
            'duration': info.get('duration', 0),
            'views': info.get('view_count', 0),
            'likes': info.get('like_count', 0),
            'uploader': info.get('uploader', 'N/A'),
            'formats': len(info.get('formats', [])),
        }

# ========== تحميل الصور من الفيديو ==========
async def extract_frames(video_path, num_frames=5):
    frames = []
    try:
        from moviepy.editor import VideoFileClip
        clip = VideoFileClip(video_path)
        duration = clip.duration
        for i in range(num_frames):
            t = (i / num_frames) * duration
            frame_path = f"{DOWNLOADS_PATH}/frame_{i}.jpg"
            clip.save_frame(frame_path, t)
            frames.append(frame_path)
        clip.close()
    except:
        pass
    return frames

# ========== تحويل فيديو لـ GIF ==========
async def video_to_gif(video_path):
    gif_path = video_path.replace('.mp4', '.gif')
    try:
        from moviepy.editor import VideoFileClip
        clip = VideoFileClip(video_path)
        clip = clip.subclip(0, min(10, clip.duration))
        clip.write_gif(gif_path, fps=10)
        clip.close()
        return gif_path
    except:
        return None

# ========== تحميل الترجمة ==========
async def get_subtitles(url):
    opts = {'quiet': True, 'writesubtitles': True, 'writeautomaticsub': True, 'subtitlesformat': 'srt', 'outtmpl': f'{DOWNLOADS_PATH}/sub_%(id)s'}
    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            if info.get('subtitles') or info.get('automatic_captions'):
                ydl.download([url])
                for f in os.listdir(DOWNLOADS_PATH):
                    if f.endswith('.srt') and f.startswith('sub_'):
                        return os.path.join(DOWNLOADS_PATH, f)
        except:
            pass
    return None

# ========== تقصير الروابط ==========
def shorten_url(url):
    try:
        r = requests.get(f'https://tinyurl.com/api-create.php?url={url}', timeout=5)
        if r.status_code == 200:
            return r.text
    except:
        pass
    return url

# ========== تحميل جماعي ==========
batch_queue = {}

async def process_batch(user_id, urls, quality, context):
    results = []
    for i, url in enumerate(urls[:10]):
        try:
            path, title = await download_media(url, quality)
            results.append((path, title))
        except Exception as e:
            results.append((None, str(e)))
    batch_queue[user_id] = results

# ========== أوامر البوت الرئيسية ==========
async def start(update, context):
    u = update.effective_user
    save_user(u.id, u.username)
    
    text = f"""
🖤 *{BOT_NAME}* 🖤
✨ *أضخم بوت تحميل في الشرق الأوسط* ✨

🔥 *أهلاً بيك يا باشا* {u.first_name}!

📥 *المنصات المدعومة:* 15+ منصة
🎬 *الجودات:* 144p → 4K
🎵 *صوت:* MP3 320kbps
⚡ *سرعة:* فائقة
🎁 *مميزات:* تحميل جماعي، مجدول، استخراج صور، GIF، ترجمة، وأكثر

{get_response(WELCOME_RESPONSES, u.first_name)}
"""
    kb = admin_keyboard() if is_admin(u.id) else main_keyboard()
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=kb)

async def handle_message(update, context):
    u = update.effective_user
    url = extract_link(update.message.text)
    quality = context.user_data.get('quality', '720')
    audio = context.user_data.get('audio', False)
    
    if not url:
        await update.message.reply_text("❌ أرسل رابط صحيح من أي منصة", parse_mode='Markdown')
        return
    
    platform = get_platform(url)
    s = await update.message.reply_text(f"🔄 {get_response(PROCESSING_RESPONSES)}\n📱 المنصة: {platform}", parse_mode='Markdown')
    
    try:
        path, title = await download_media(url, quality, audio)
        size = os.path.getsize(path) / 1048576
        update_user(u.id, platform)
        
        if audio:
            with open(path, 'rb') as f:
                await update.message.reply_audio(f, title=title[:50], caption=f"🎵 {title[:40]}\n\n{SIGNATURE}", parse_mode='Markdown')
        else:
            with open(path, 'rb') as f:
                await update.message.reply_video(f, caption=f"🎬 *{title[:60]}*\n📦 `{size:.1f} MB`\n⚡ `{quality}p`\n📱 `{platform}`\n\n{SIGNATURE}", parse_mode='Markdown', supports_streaming=True)
        
        os.remove(path)
        await s.delete()
    except Exception as e:
        await s.edit_text(f"❌ فشل التحميل\n```{str(e)[:150]}```", parse_mode='Markdown')

async def audio_cmd(update, context):
    context.user_data['audio'] = True
    await update.message.reply_text("🎵 *وضع الصوت مفعل*\nأرسل رابط الفيديو", parse_mode='Markdown')

async def video_info_cmd(update, context):
    url = extract_link(update.message.text or '')
    if not url:
        await update.message.reply_text("أرسل رابط مع الأمر /info", parse_mode='Markdown')
        return
    s = await update.message.reply_text("🔄 جلب المعلومات...")
    try:
        info = await get_video_info(url)
        dur = f"{info['duration']//60}:{info['duration']%60:02d}" if info['duration'] else "N/A"
        text = f"📹 *معلومات الفيديو*\n\n• العنوان: {info['title'][:50]}\n• المدة: {dur}\n• المشاهدات: {info['views']:,}\n• الإعجابات: {info['likes']:,}\n• الناشر: {info['uploader']}"
        await s.edit_text(text, parse_mode='Markdown')
    except Exception as e:
        await s.edit_text(f"❌ {str(e)[:100]}")

async def stats_cmd(update, context):
    with open(DB_FILE, 'r') as f:
        data = json.load(f)
    u = data['users'].get(str(update.effective_user.id), {})
    text = f"📊 *إحصائياتك*\n• تحميلات: {u.get('downloads', 0)}\n• الجودة المفضلة: {context.user_data.get('quality', '720')}p\n\n🌍 *البوت*\n• إجمالي التحميلات: {data['stats']['total_downloads']:,}\n• تحميلات اليوم: {data['stats']['today']}"
    await update.message.reply_text(text, parse_mode='Markdown')

async def share_cmd(update, context):
    bot = await context.bot.get_me()
    link = f"https://t.me/{bot.username}"
    short = shorten_url(link)
    await update.message.reply_text(f"🎁 *شارك البوت مع أصحابك*\n\n`{short}`\n\nكل ما حد يشترك عبر رابطك، هتدعمني 🤍", parse_mode='Markdown')

# ========== أوامر الأدمن الشاملة ==========
async def admin_full_stats(update, context):
    if not is_admin(update.effective_user.id):
        return
    with open(DB_FILE, 'r') as f:
        data = json.load(f)
    users = data['users']
    platforms = data['platforms']
    most_platform = max(platforms.items(), key=lambda x: x[1])[0] if platforms else "N/A"
    text = f"""
👑 *إحصائيات البوت الشاملة* 👑
━━━━━━━━━━━━━━━━━━━
👥 *المستخدمين:* {len(users)}
📥 *إجمالي التحميلات:* {data['stats']['total_downloads']:,}
📈 *تحميلات اليوم:* {data['stats']['today']}

📱 *أكثر منصة:* {most_platform}
🎯 *أكثر مستخدم نشاط:* {max(users.items(), key=lambda x: x[1]['downloads'])[1]['name'] if users else 'N/A'}

✨ {SIGNATURE} ✨
"""
    await update.message.reply_text(text, parse_mode='Markdown')

async def daily_report(update, context):
    if not is_admin(update.effective_user.id):
        return
    with open(DB_FILE, 'r') as f:
        data = json.load(f)
    today = str(datetime.now().date())
    active = sum(1 for u in data['users'].values() if u.get('last_active', '').startswith(today))
    await update.message.reply_text(f"📊 *تقرير يومي {today}*\n• تحميلات: {data['stats']['today']}\n• مستخدمين نشطين: {active}", parse_mode='Markdown')

async def backup_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    backup_file = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    shutil.copy(DB_FILE, backup_file)
    await update.message.reply_document(open(backup_file, 'rb'), caption=f"📦 نسخة احتياطية {datetime.now()}")
    os.remove(backup_file)

async def restart_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text("🔄 جاري إعادة التشغيل...")
    os._exit(0)

async def block_user_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("🚫 /block <user_id>")
        return
    with open(DB_FILE, 'r+') as f:
        data = json.load(f)
        data['users'][context.args[0]]['blocked'] = True
        f.seek(0)
        json.dump(data, f, indent=2)
    await update.message.reply_text(f"✅ تم حظر {context.args[0]}")

# ========== معالجة الأزرار ==========
async def callback(update, context):
    q = update.callback_query
    await q.answer()
    u = update.effective_user.id
    
    # جودة
    if q.data.startswith('q_'):
        val = q.data[2:]
        if val == 'audio':
            context.user_data['audio'] = True
            await q.edit_message_text("🎵 وضع الصوت مفعل", parse_mode='Markdown')
        else:
            context.user_data['quality'] = val
            context.user_data['audio'] = False
            await q.edit_message_text(f"⚡ تم ضبط الجودة {val}p", parse_mode='Markdown')
    
    elif q.data == 'quality_menu':
        await q.edit_message_text("🎬 *اختر الجودة المناسبة*", parse_mode='Markdown', reply_markup=quality_keyboard_full())
    
    elif q.data == 'platforms_menu':
        await q.edit_message_text("🌍 *اختر المنصة*", parse_mode='Markdown', reply_markup=platforms_keyboard())
    
    elif q.data.startswith('platform_'):
        plat = q.data.replace('platform_', '').upper()
        await q.edit_message_text(f"📱 منصة {plat}\nأرسل رابط الفيديو الآن", parse_mode='Markdown')
    
    elif q.data == 'share_bot':
        bot = await context.bot.get_me()
        link = shorten_url(f"https://t.me/{bot.username}")
        await q.edit_message_text(f"🎁 *شارك البوت*\n`{link}`\n\n{SIGNATURE}", parse_mode='Markdown')
    
    elif q.data == 'my_stats':
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
        d = data['users'].get(str(u), {})
        await q.edit_message_text(f"📊 تحميلاتك: {d.get('downloads', 0)}\n🌍 إجمالي: {data['stats']['total_downloads']:,}", parse_mode='Markdown')
    
    elif q.data == 'video_info':
        await q.edit_message_text("ℹ️ استخدم /info مع الرابط", parse_mode='Markdown')
    
    elif q.data == 'batch_download':
        await q.edit_message_text("📥 *تحميل جماعي*\nأرسل الروابط كل في سطر جديد (حد أقصى 10)", parse_mode='Markdown')
    
    elif q.data == 'extract_frames':
        await q.edit_message_text("🖼️ *استخراج صور*\nأرسل رابط الفيديو", parse_mode='Markdown')
    
    elif q.data == 'to_gif':
        await q.edit_message_text("🎞️ *تحويل GIF*\nأرسل رابط الفيديو (أول 10 ثواني)", parse_mode='Markdown')
    
    elif q.data == 'get_subs':
        await q.edit_message_text("📜 *ترجمة نصية*\nأرسل رابط يوتيوب", parse_mode='Markdown')
    
    elif q.data == 'shorten_url':
        await q.edit_message_text("🔗 *تقصير روابط*\nأرسل الرابط الطويل", parse_mode='Markdown')
    
    elif q.data == 'save_cloud':
        await q.edit_message_text("💾 *حفظ سحابي*\nميزة قريباً", parse_mode='Markdown')
    
    elif q.data == 'convert_format':
        await q.edit_message_text("🔄 *تحويل صيغة*\nأرسل الفيديو", parse_mode='Markdown')
    
    elif q.data == 'schedule_menu':
        await q.edit_message_text("⏰ *تحميل مجدول*\nاستخدم /schedule <HH:MM> <الرابط>", parse_mode='Markdown')
    
    elif q.data == 'custom_url':
        await q.edit_message_text("📤 أرسل الرابط مباشرة", parse_mode='Markdown')
    
    elif q.data == 'news':
        await q.edit_message_text(f"📢 *أخبار البوت*\nالإصدار {VERSION}\n{SIGNATURE}", parse_mode='Markdown')
    
    elif q.data == 'help':
        text = "📌 *المساعدة*\n• /start - القائمة\n• /audio - وضع الصوت\n• /stats - إحصائيات\n• /share - مشاركة\n• /info - معلومات الفيديو"
        await q.edit_message_text(text, parse_mode='Markdown')
    
    elif q.data == 'admin_panel':
        if is_admin(u):
            await q.edit_message_text("👑 *لوحة التحكم الشاملة*", parse_mode='Markdown', reply_markup=admin_panel_full())
        else:
            await q.edit_message_text("⛔ غير مصرح")
    
    elif q.data == 'admin_full_stats':
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
        await q.edit_message_text(f"👑 مستخدمين: {len(data['users'])}\n📥 تحميلات: {data['stats']['total_downloads']:,}\n📈 اليوم: {data['stats']['today']}", reply_markup=admin_panel_full())
    
    elif q.data == 'admin_broadcast':
        await q.edit_message_text("📢 استخدم /broadcast الرسالة")
    
    elif q.data == 'admin_users_list':
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
        txt = "👥 *المستخدمين:*\n"
        for uid, info in list(data['users'].items())[:20]:
            txt += f"• `{uid}` - {info['name']} - {info['downloads']}\n"
        await q.edit_message_text(txt, parse_mode='Markdown')
    
    elif q.data == 'admin_clear_cache':
        c = 0
        for f in os.listdir(DOWNLOADS_PATH):
            try:
                os.remove(os.path.join(DOWNLOADS_PATH, f))
                c += 1
            except:
                pass
        await q.edit_message_text(f"🗑️ حذف {c} ملف مؤقت", reply_markup=admin_panel_full())
    
    elif q.data == 'admin_daily_report':
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
        await q.edit_message_text(f"📊 *تقرير اليوم*\nتحميلات: {data['stats']['today']}", parse_mode='Markdown')
    
    elif q.data == 'admin_restart':
        await q.edit_message_text("🔄 إعادة تشغيل...")
        os._exit(0)
    
    elif q.data == 'admin_backup':
        backup_file = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        shutil.copy(DB_FILE, backup_file)
        await q.message.reply_document(open(backup_file, 'rb'))
        os.remove(backup_file)
    
    elif q.data == 'admin_block_user':
        await q.edit_message_text("🚫 /block <user_id>")
    
    elif q.data == 'back':
        kb = admin_keyboard() if is_admin(u) else main_keyboard()
        await q.edit_message_text("🖤 *القائمة الرئيسية*", parse_mode='Markdown', reply_markup=kb)
    
    elif q.data == 'help_video':
        await q.edit_message_text("🎬 أرسل رابط الفيديو وسأقوم بتحميله بأعلى جودة", parse_mode='Markdown')
    
    elif q.data == 'help_audio':
        await q.edit_message_text("🎵 استخدم /audio ثم أرسل الرابط", parse_mode='Markdown')

# ========== التشغيل النهائي ==========
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    
    # أوامر أساسية
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("audio", audio_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("share", share_cmd))
    app.add_handler(CommandHandler("info", video_info_cmd))
    
    # أوامر الأدمن
    app.add_handler(CommandHandler("adminstats", admin_full_stats))
    app.add_handler(CommandHandler("broadcast", lambda u,c: broadcast_cmd(u,c) if 'broadcast_cmd' in dir() else None))
    app.add_handler(CommandHandler("users", lambda u,c: admin_users_list(u,c) if 'admin_users_list' in dir() else None))
    app.add_handler(CommandHandler("clear", lambda u,c: admin_clear_cache(u,c) if 'admin_clear_cache' in dir() else None))
    app.add_handler(CommandHandler("daily", daily_report))
    app.add_handler(CommandHandler("backup", backup_cmd))
    app.add_handler(CommandHandler("restart", restart_cmd))
    app.add_handler(CommandHandler("block", block_user_cmd))
    
    # معالجات
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("=" * 60)
    print(f"✨ {SIGNATURE} ✨")
    print(f"🔥 {BOT_NAME} - أضخم بوت في الشرق الأوسط")
    print(f"👑 الأدمن: {ADMIN_IDS}")
    print(f"📦 الإصدار: {VERSION}")
    print("=" * 60)
    app.run_polling()

if __name__ == "__main__":
    main()
