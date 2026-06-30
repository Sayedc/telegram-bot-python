# ==========================
# CALLBACK HANDLER (FULL FIX)
# ==========================
async def callback(update, context):
    q = update.callback_query
    await q.answer()

    data = q.data

    # =========================
    # QUALITY SYSTEM
    # =========================
    if data.startswith("q_"):
        value = data.replace("q_", "")

        if value == "audio":
            context.user_data["audio"] = True
            context.user_data["quality"] = None
            await q.edit_message_text("🎵 تم تفعيل وضع الصوت")
        else:
            context.user_data["audio"] = False
            context.user_data["quality"] = value
            await q.edit_message_text(f"⚡ الجودة: {value}p")

    # =========================
    # MAIN BUTTONS
    # =========================
    elif data == "help_video":
        await q.edit_message_text("🎬 ابعت اللينك وهحمل الفيديو")

    elif data == "help_audio":
        await q.edit_message_text("🎵 ابعت اللينك وهحولك لصوت")

    elif data == "share_bot":
        await q.edit_message_text("🎁 شارك البوت مع صحابك ❤️")

    elif data == "my_stats":
        await q.edit_message_text("📊 جاري عرض إحصائياتك...")

    elif data == "help":
        await q.edit_message_text("❓ المساعدة: ابعت أي لينك")

    # =========================
    # ADMIN PANEL
    # =========================
    elif data == "admin_panel":
        from keyboards.main_keyboard import admin_panel
        await q.edit_message_text(
            "👑 لوحة الأدمن",
            reply_markup=admin_panel()
        )

    # =========================
    # BACK BUTTON
    # =========================
    elif data == "back":
        await q.edit_message_text("🏠 Main Menu")

    # =========================
    # SAFETY
    # =========================
    else:
        await q.edit_message_text("⚠️ زرار غير معروف")
