# Alhawy Downloader — Telegram video/audio downloader bot

بوت تيليجرام بيحمّل فيديو وصوت من يوتيوب، تيك توك، انستجرام، فيسبوك، تويتر وأي موقع يدعمه `yt-dlp`.

## التشغيل المحلي

```bash
pip install -r requirements.txt
cp .env.example .env      # وعدّل BOT_TOKEN و ADMIN_IDS
python main.py
```

محتاج على الجهاز: **FFmpeg** و **Node.js (أو Deno)**. يوتيوب بيطلب JavaScript runtime
عشان يحل التحدي بتاعه؛ من غيره التحميل بيفشل برسالة `No video formats found`.

## المتغيرات (Environment Variables)

| المتغير | مطلوب | الوصف |
|---|---|---|
| `BOT_TOKEN` | ✅ | توكن البوت من @BotFather |
| `ADMIN_IDS` | ✅ | IDs الأدمن مفصولة بفاصلة |
| `DATABASE_PATH` | ❌ | مسار ملف المستخدمين. على Railway/Docker حطه على Volume (مثلاً `/data/database.json`) وإلا بيتمسح مع كل نشر |
| `YOUTUBE_COOKIES` / `INSTAGRAM_COOKIES` / `FACEBOOK_COOKIES` / `TIKTOK_COOKIES` | ❌ | محتوى ملف cookies.txt (Netscape) كامل |
| `PROXY` | ❌ | بروكسي لو الـ IP بتاع السيرفر محظور |
| `DOWNLOAD_TIMEOUT` | ❌ | أقصى وقت لتحميل واحد بالثواني (الافتراضي 900) |

> **الكوكيز والتوكن مبيتحطوش في الريبو أبداً.** استخدم متغيرات البيئة. الملفات `cookies*.txt` و `.env` متجاهلة في `.gitignore`.

## النشر على Railway

استخدم الـ `Dockerfile` (فيه FFmpeg و Node). أضف المتغيرات من تبويب Variables، وأضف Volume لو عايز المستخدمين يفضلوا بعد كل نشر.

يوتيوب بيغيّر حماية كل كام أسبوع، فلو بدأ التحميل يفشل: اعمل Redeploy عشان يتثبّت أحدث `yt-dlp`.

## أوامر الأدمن

`/stats` `/top` `/users` `/broadcast <نص>` `/block <id>` `/unblock <id>` `/clear` `/backup` `/metrics`
