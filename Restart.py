from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import os
import sys
from Decorators import owner_only

@owner_only
async def restart_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if data == "admin_restart":
        await restart_bot(update, context)

@owner_only
async def restart_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text("🔄 جاري إعادة تشغيل البوت...")
    
    # إعادة تشغيل البوت
    os.execl(sys.executable, sys.executable, *sys.argv)