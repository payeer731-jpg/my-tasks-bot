# Member/Complaint.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from Config import OWNER_ID
from Decorators import user_only

@user_only
async def complaint_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if data == "complaint_send":
        await send_complaint_prompt(update, context)
    elif data == "complaint_policy":
        await show_policy(update, context)

@user_only
async def send_complaint_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text(
        "📞 أرسل شكواك أو اقتراحك وسيتم الرد عليك قريباً:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="member_menu")]])
    )
    context.user_data['awaiting_complaint'] = True  # تمت إضافة هذا السطر

@user_only
async def show_policy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    policy_text = """
📜 **سياسة الاستخدام:**

1. **الالتزام بالأدب** في التعامل مع البوت والأعضاء الآخرين
2. **ممنوع نشر** محتوى غير أخلاقي أو مسيء
3. **يحق للإدارة** حظر أي مستخدم يخالف الشروط بدون سابق إنذار
4. **النقاط غير قابلة** للاسترداد أو التحويل بين الحسابات
5. **المهام المرسلة** تخضع للمراجعة وقد يتم رفضها

🔒 **الإدارة تحتفظ بالحق** في تعديل الشروط في أي وقت

📞 **للتواصل:** @E8EOE
    """
    
    keyboard = [
        [InlineKeyboardButton("📞 إرسال شكوى", callback_data="complaint_send")],
        [InlineKeyboardButton("رجوع", callback_data="member_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(policy_text, reply_markup=reply_markup, parse_mode='Markdown') ون