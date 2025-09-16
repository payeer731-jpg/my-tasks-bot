from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from Data import db
from Decorators import user_only
import logging

logger = logging.getLogger(__name__)

@user_only
async def gift_code_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🎁 **أدخل كود الهدية:**\n\n"
        "📝 اكتب الكود الذي حصلت عليه لاستلام نقاط مجانية!",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="member_menu")]]),
        parse_mode='Markdown'
    )
    context.user_data['awaiting_gift_code'] = True

@user_only
async def handle_gift_code_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة إدخال كود الهدية"""
    try:
        code = update.message.text.strip().upper()
        user_id = update.effective_user.id
        
        success, message = db.use_gift_code(code, user_id)
        
        if success:
            await update.message.reply_text(
                f"✅ {message}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📋 العودة للقائمة", callback_data="member_menu")]])
            )
        else:
            await update.message.reply_text(
                f"❌ {message}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 المحاولة مرة أخرى", callback_data="member_gift_code")]])
            )
        
        context.user_data.pop('awaiting_gift_code', None)
        
    except Exception as e:
        logger.error(f"Error handling gift code: {e}")
        await update.message.reply_text("❌ حدث خطأ في معالجة الكود")