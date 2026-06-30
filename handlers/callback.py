async def callback_handler(update, context):
    q = update.callback_query
    await q.answer()

    data = q.data

    # ========= QUALITY =========
    if data.startswith("q_"):
        value = data[2:]

        if value == "audio":
            context.user_data["audio"] = True
            context.user_data["quality"] = None
            await q.edit_message_text("🎵 تم تفعيل الصوت")
            return

        context.user_data["audio"] = False
        context.user_data["quality"] = value
        await q.edit_message_text(f"⚡ الجودة: {value}p")
        return

    # ========= ADMIN PANEL =========
    if data == "admin_panel":
        from keyboards.main_keyboard import admin_panel
        await q.edit_message_text("👑 لوحة الأدمن", reply_markup=admin_panel())
        return

    if data == "admin_stats":
        await q.edit_message_text("📊 stats ...")
        return

    if data == "admin_top":
        await q.edit_message_text("🏆 top ...")
        return

    if data == "admin_users":
        await q.edit_message_text("👥 users ...")
        return

    if data == "admin_clear":
        await q.edit_message_text("🧹 cleared")
        return

    if data == "back":
        from keyboards.main_keyboard import main_keyboard
        await q.edit_message_text("🏠 Main Menu", reply_markup=main_keyboard())
        return

    # ========= USER BUTTONS =========
    if data == "help_video":
        await q.edit_message_text("🎬 أرسل رابط الفيديو")
        return

    if data == "help_audio":
        await q.edit_message_text("🎵 أرسل رابط لاستخراج الصوت")
        return

    if data == "share_bot":
        await q.edit_message_text("🎁 شارك البوت: ...")
        return

    if data == "my_stats":
        await q.edit_message_text("📊 إحصائياتك")
        return

    if data == "help":
        await q.edit_message_text("❓ المساعدة ...")
        return

    # fallback
    await q.edit_message_text("⚠️ زر غير معروف")
