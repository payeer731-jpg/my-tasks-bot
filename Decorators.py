from telegram import Update
from telegram.ext import ContextTypes
from Data import db
from Config import OWNER_ID

async def check_blocked_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """وسيط للتحقق من إذا كان المستخدم محظوراً"""
    user_id = update.effective_user.id
    
    if str(user_id) in db.get_blocked_users():
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.answer("❌ تم حظرك من استخدام هذا البوت.", show_alert=True)
        elif hasattr(update, 'message') and update.message:
            await update.message.reply_text("❌ تم حظرك من استخدام هذا البوت.")
        return False
    return True

def user_only(handler):
    """ديكوراتور للتحقق من الحظر فقط"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not await check_blocked_middleware(update, context):
            return
        return await handler(update, context, *args, **kwargs)
    return wrapper

def admin_only(handler):
    """ديكوراتور للتحقق من الحظر وصلاحية الأدمن"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not await check_blocked_middleware(update, context):
            return
        
        user_id = update.effective_user.id
        if str(user_id) not in db.get_admins() and user_id != OWNER_ID:
            if hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.answer("❌ فقط المديرين يمكنهم الوصول إلى هذه الصفحة", show_alert=True)
            return
        
        return await handler(update, context, *args, **kwargs)
    return wrapper

def owner_only(handler):
    """ديكوراتور للتحقق من الحظر وصلاحية المالك"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not await check_blocked_middleware(update, context):
            return
        
        user_id = update.effective_user.id
        if user_id != OWNER_ID:
            if hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.answer("❌ فقط المالك يمكنه الوصول إلى هذه الصفحة", show_alert=True)
            return
        
        return await handler(update, context, *args, **kwargs)
    return wrapper