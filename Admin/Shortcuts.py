from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from Data import db
from Config import OWNER_ID  # إضافة استيراد OWNER_ID
from Middleware import check_blocked_middleware  # إضافة استيراد الوسيط

async def shortcuts_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # التحقق من الحظر أولاً
    if not await check_blocked_middleware(update, context):
        return
    
    # التحقق من أن المستخدم أدمن
    user_id = update.effective_user.id
    if str(user_id) not in db.get_admins() and user_id != OWNER_ID:
        await update.callback_query.answer("❌ فقط المديرين يمكنهم الوصول إلى هذه الصفحة", show_alert=True)
        return
    
    # التحقق من أن المستخدم غير محظور
    if str(user_id) in db.get_blocked_users():
        await update.callback_query.answer("❌ لا يمكنك الوصول إلى هذه الصفحة وأنت محظور", show_alert=True)
        return
    
    query = update.callback_query
    data = query.data
    
    if data == "admin_shortcuts":
        await show_shortcuts(update, context)

async def show_shortcuts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # التحقق من أن المستخدم أدمن
    user_id = update.effective_user.id
    if str(user_id) not in db.get_admins() and user_id != OWNER_ID:
        await update.callback_query.answer("❌ فقط المديرين يمكنهم الوصول إلى هذه الصفحة", show_alert=True)
        return
    
    # التحقق من أن المستخدم غير محظور
    if str(user_id) in db.get_blocked_users():
        await update.callback_query.answer("❌ لا يمكنك الوصول إلى هذه الصفحة وأنت محظور", show_alert=True)
        return
    
    shortcuts_text = """
⚡ **اختصارات الأدمن السريعة:**

• /stats - عرض الإحصائيات
• /broadcast - إذاعة للجميع
• /addadmin [ايدي] - إضافة مدير
• /block [ايدي] - حظر مستخدم
• /unblock [ايدي] - فك حظر مستخدم
• /points [ايدي] [عدد] - إضافة نقاط
• /addtask [المهمة] - إضافة مهمة
• /restart - إعادة تشغيل البوت (للمالك فقط)

🔍 **للعودة للوحة التحكم اضغط رجوع**
    """
    
    keyboard = [[InlineKeyboardButton("رجوع", callback_data="admin_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(shortcuts_text, reply_markup=reply_markup, parse_mode='Markdown')