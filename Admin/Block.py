from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from Data import db
from Admin.Db import admin_block_user, admin_unblock_user
from Config import OWNER_ID
from Decorators import admin_only

@admin_only
async def block_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if data == "blocked_list":
        await blocked_list(update, context)
    elif data == "block_user":
        await block_user_prompt(update, context)
    elif data == "unblock_user":
        await unblock_user_prompt(update, context)
    elif data.startswith("block_"):
        user_id_to_block = data.split("_")[1]
        await block_user(update, context, user_id_to_block)
    elif data.startswith("unblock_"):
        user_id_to_unblock = data.split("_")[1]
        await unblock_user(update, context, user_id_to_unblock)

@admin_only
async def blocked_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    blocked_list = db.get_blocked_users()
    message = "🚫 قائمة المستخدمين المحظورين:\n\n"
    
    for user_id in blocked_list:
        try:
            user = await context.bot.get_chat(int(user_id))
            message += f"• {user.first_name} (ID: {user_id})\n"
        except:
            message += f"• (ID: {user_id})\n"
    
    if not blocked_list:
        message = "✅ لا يوجد مستخدمين محظورين"
    
    keyboard = [
        [InlineKeyboardButton("🔒 حظر مستخدم", callback_data="block_user")],
        [InlineKeyboardButton("🔓 فك حظر مستخدم", callback_data="unblock_user")],
        [InlineKeyboardButton("رجوع", callback_data="admin_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup)

@admin_only
async def block_user_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text(
        "🔒 أرسل ايدي المستخدم لحظره:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="blocked_list")]])
    )
    context.user_data['awaiting_block_id'] = True

@admin_only
async def unblock_user_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    blocked_list = db.get_blocked_users()
    if not blocked_list:
        await update.callback_query.edit_message_text(
            "✅ لا يوجد مستخدمين محظورين",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="blocked_list")]])
        )
        return
    
    keyboard = []
    for user_id in blocked_list:
        try:
            user = await context.bot.get_chat(int(user_id))
            keyboard.append([InlineKeyboardButton(f"فك حظر {user.first_name}", callback_data=f"unblock_{user_id}")])
        except:
            keyboard.append([InlineKeyboardButton(f"فك حظر {user_id}", callback_data=f"unblock_{user_id}")])
    
    keyboard.append([InlineKeyboardButton("رجوع", callback_data="blocked_list")])
    
    await update.callback_query.edit_message_text(
        "🔓 اختر المستخدم لفك حظره:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

@admin_only
async def block_user(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id):
    user_id_current = update.effective_user.id
    
    # منع حظر النفس
    if user_id == str(user_id_current):
        await update.callback_query.answer("❌ لا يمكنك حظر نفسك", show_alert=True)
        return
        
    # منع حظر المالك
    if int(user_id) == OWNER_ID:
        await update.callback_query.answer("❌ لا يمكنك حظر المالك", show_alert=True)
        return
        
    # منع حظر أدمن آخر (ما لم يكن المستخدم هو المالك)
    if user_id in db.get_admins() and user_id_current != OWNER_ID:
        await update.callback_query.answer("❌ لا يمكنك حظر مدير آخر", show_alert=True)
        return
    
    if admin_block_user(user_id):
        await update.callback_query.answer("✅ تم حظر المستخدم")
    else:
        await update.callback_query.answer("⚠️ المستخدم محظور بالفعل")
    await blocked_list(update, context)

@admin_only
async def unblock_user(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id):
    if admin_unblock_user(user_id):
        await update.callback_query.answer("✅ تم فك حظر المستخدم")
    else:
        await update.callback_query.answer("⚠️ المستخدم غير محظور")
    await blocked_list(update, context)