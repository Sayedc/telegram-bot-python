from utils.keyboards import admin_panel


async def callback_handler(update, context):
    q = update.callback_query
    await q.answer()

    data = q.data

    # ========================
    # ADMIN PANEL
    # ========================
    if data == "admin_panel":
        await q.edit_message_text(
            "👑 لوحة الأدمن",
            reply_markup=admin_panel()
        )
        return

    # ========================
    # QUALITY / AUDIO (لو موجود عندك)
    # ========================
    if data.startswith("q_"):
        value = data.replace("q_", "")

        context.user_data["audio"] = (value == "audio")
        context.user_data["quality"] = None if value == "audio" else value

        await q.edit_message_text(f"⚡ تم اختيار: {value}")
        return

    # ========================
    # MAIN ACTIONS
    # ========================
    elif data == "help_video":
        await q.edit_message_text("🎬 أرسل رابط الفيديو")

    elif data == "help_audio":
        await q.edit_message_text("🎵 استخراج الصوت")

    elif data == "share_bot":
        await q.edit_message_text("🎁 شارك البوت مع أصدقائك")

    elif data == "my_stats":
        await q.edit_message_text("📊 إحصائياتك")

    elif data == "help":
        await q.edit_message_text("❓ المساعدة")

    elif data == "back":
        await q.edit_message_text("🏠 الرئيسية")

    # ========================
    # ADMIN ACTIONS
    # ========================
    elif data == "admin_stats":
        await q.edit_message_text("📊 Stats")

    elif data == "admin_top":
        await q.edit_message_text("🏆 Top Users")

    elif data == "admin_users":
        await q.edit_message_text("👥 Users")

    elif data == "admin_broadcast":
        await q.edit_message_text("📢 Broadcast")

    elif data == "admin_clear":
        await q.edit_message_text("🧹 Clear Done")

    else:
        await q.edit_message_text("⚠️ Invalid action")
