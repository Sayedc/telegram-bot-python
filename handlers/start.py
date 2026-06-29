
async def start(update, context):
    u = update.effective_user
    
    if is_blocked(u.id):
        await update.message.reply_text("🚫 *لقد تم حظرك*", parse_mode='Markdown')
        return
    
    await save_user(u.id, u.username, context)
    text = f"""
🖤 *أهلاً {u.first_name}!* 🖤

✨ {SIGNATURE} ✨

🌍 *البوت بينزل أي حاجة من أي موقع*

📌 *المنصات المدعومة:*
• TikTok • YouTube • Instagram
• Facebook • Twitter • SoundCloud
• Spotify • Deezer • وأي موقع

🔥 *أرسل أي رابط وسأقوم بتحميله*

{get_response(WELCOME_RESPONSES, u.first_name)}
"""
    kb = admin_keyboard() if is_admin(u.id) else main_keyboard()
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=kb)

async def handle_message(update, context):
    u = update.effective_user
    start_time = datetime.now()
