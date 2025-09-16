from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from Data import db
from Config import OWNER_ID
from Decorators import owner_only

def get_admins():
    return db.get_admins()

@owner_only
async def admins_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if data == "admins_list":
        await list_admins(update, context)
    elif data == "admins_add":
        await add_admin_prompt(update, context)
    elif data == "admins_remove":
        await remove_admin_prompt(update, context)
    elif data.startswith("remove_admin_"):
        admin_id = data.split("_")[2]
        await remove_admin(update, context, admin_id)

@owner_only
async def list_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    admins_list = db.get_admins()
    message = "👥 قائمة المشرفين:\n\n"
    
    for admin_id in admins_list:
        try:
            user = await context.bot.get_chat(int(admin_id))
            status = "👑 المالك" if int(admin_id) == OWNER_ID else "👤 مدير"
            message += f"• {status}: {user.first_name} (ID: {admin_id})\n"
        except:
            status = "👑 المالك" if int(admin_id) == OWNER_ID else "👤 مدير"
            message += f"• {status}: (ID: {admin_id})\n"
    
    keyboard = [
        [InlineKeyboardButton("➕ إضافة مدير", callback_data="admins_add")],
        [InlineKeyboardButton("➖ حذف مدير", callback_data="admins_remove")],
        [InlineKeyboardButton("رجوع", callback_data="admin_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(message, reply_markup=reply_markup)

@owner_only
async def add_admin_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text(
        "📝 أرسل ايدي المستخدم لإضافته كمدير:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="admins_list")]])
    )
    context.user_data['awaiting_admin_id'] = True

@owner_only
async def remove_admin_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admins_list = db.get_admins()
    if not admins_list:
        await update.callback_query.edit_message_text(
            "❌ لا يوجد مشرفين حالياً",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="admins_list")]])
        )
        return
    
    keyboard = []
    for admin_id in admins_list:
        # استبعاد المالك من قائمة الحذف
        if int(admin_id) == OWNER_ID:
            continue
            
        try:
            user = await context.bot.get_chat(int(admin_id))
            keyboard.append([InlineKeyboardButton(f"حذف {user.first_name}", callback_data=f"remove_admin_{admin_id}")])
        except:
            keyboard.append([InlineKeyboardButton(f"حذف {admin_id}", callback_data=f"remove_admin_{admin_id}")])
    
    if not keyboard:
        await update.callback_query.edit_message_text(
            "❌ لا يوجد مديرين يمكن حذفهم",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="admins_list")]])
        )
        return
    
    keyboard.append([InlineKeyboardButton("رجوع", callback_data="admins_list")])
    
    await update.callback_query.edit_message_text(
        "👥 اختر المدير الذي تريد حذفه:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

@owner_only
async def remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, admin_id):
    # منع حذف المالك
    if int(admin_id) == OWNER_ID:
        await update.callback_query.answer("❌ لا يمكن حذف المالك")
        return
    
    if db.remove_admin(admin_id):
        await update.callback_query.answer("✅ تم حذف المدير")
    else:
        await update.callback_query.answer("❌ خطأ في حذف المدير")
    
    await list_admins(update, context)