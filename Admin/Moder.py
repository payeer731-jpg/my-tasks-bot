from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from Data import db
from Decorators import admin_only

@admin_only
async def moder_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if data == "moder_menu":
        await moder_menu(update, context)
    elif data == "moder_broadcast":
        await broadcast_prompt(update, context)
    elif data == "moder_stats":
        await stats(update, context)
    elif data == "moder_back":
        from Member.Menu import show_member_menu
        await show_member_menu(update, context)

@admin_only
async def moder_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = "📢 الإذاعة والإحصائيات:\n\n"
    message += "اختر الإجراء المطلوب:"
    
    keyboard = [
        [InlineKeyboardButton("📢 إذاعة للجميع", callback_data="moder_broadcast")],
        [InlineKeyboardButton("رجوع", callback_data="admin_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup)

@admin_only
async def broadcast_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text(
        "📢 أرسل الرسالة التي تريد إذاعتها للجميع:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="moder_menu")]])
    )
    context.user_data['awaiting_broadcast'] = True

# في Admin/Moder.py - إصلاح دالة stats
@admin_only
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        
        # إحصائيات المستخدمين
        users_count = len(db.data.get("users", {}))
        admins_count = len(db.data.get("admins", []))
        blocked_count = len(db.data.get("blocked_users", []))
        
        # إحصائيات المهام
        all_tasks = db.data.get("tasks_new", [])
        tasks_count = len(all_tasks)
        
        # حساب المهام النشطة والمكتملة
        active_tasks = len([t for t in all_tasks if t.get('status') == 'active'])
        completed_tasks = len([t for t in all_tasks if t.get('status') == 'completed'])
        
        # إحصائيات النقاط
        total_points = sum(user.get("points", 0) for user in db.data.get("users", {}).values())
        
        # إحصائيات الإثباتات
        proofs_count = len(db.data.get("proofs", []))
        pending_proofs = len([p for p in db.data.get("proofs", []) if p.get('status') == 'pending'])
        
        message = f"""
📊 **الإحصائيات العامة للبوت**

👥 **المستخدمون:**
• 👤 إجمالي المستخدمين: {users_count}
• 👑 عدد المشرفين: {admins_count}
• 🚫 المحظورين: {blocked_count}

📋 **المهام:**
• 📦 إجمالي المهام: {tasks_count}
• 🟢 نشطة: {active_tasks}
• ✅ مكتملة: {completed_tasks}

💰 **النقاط:**
• 💎 الإجمالي: {total_points} نقطة
• 🎯 نقاط الدعوة: {db.get_invite_points()} لكل دعوة

📨 **الإثباتات:**
• 📩 الإجمالي: {proofs_count}
• ⏳ قيد المراجعة: {pending_proofs}

⚙️ **حالة النظام:**
• 📊 نظام الدعوة: {'✅ مفعل' if db.is_invite_system_enabled() else '❌ معطل'}
"""
        
        keyboard = [
            [InlineKeyboardButton("🔄 تحديث الإحصائيات", callback_data="moder_stats")],
            [InlineKeyboardButton("📊 إحصائيات الدعوة", callback_data="invite_stats")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"خطأ في عرض الإحصائيات: {e}")
        await update.callback_query.answer("❌ حدث خطأ في عرض الإحصائيات")