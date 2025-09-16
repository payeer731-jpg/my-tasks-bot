from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from Data import db
from Decorators import admin_only
import logging

logger = logging.getLogger(__name__)

@admin_only
async def tasks_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if data == "tasks_menu":
        await tasks_menu(update, context)
    elif data == "tasks_search":
        await search_task_prompt(update, context)
    elif data.startswith("delete_task_"):
        task_id = data.split("_")[2]
        await delete_task(update, context, task_id)

@admin_only
async def tasks_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض قائمة إدارة المهام المختصرة"""
    try:
        message = """
🔍 **إدارة المهام - البحث بالكود**

🎯 يمكنك البحث عن أي مهمة باستخدام كودها الخاص
"""
        
        keyboard = [
            [InlineKeyboardButton("🔍 بحث عن مهمة", callback_data="tasks_search")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"خطأ في tasks_menu: {e}")
        await update.callback_query.answer("❌ حدث خطأ في عرض القائمة")

@admin_only
async def search_task_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مطالبة بإدخال كود المهمة للبحث"""
    try:
        await update.callback_query.edit_message_text(
            "🔍 **أدخل كود المهمة للبحث:**\n\n"
            "📝 مثال: TSK-1234\n\n"
            "💡 يمكنك الحصول على الأكواد من قنوات المهام",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="tasks_menu")]]),
            parse_mode='Markdown'
        )
        context.user_data['awaiting_task_search'] = True
        
    except Exception as e:
        logger.error(f"خطأ في search_task_prompt: {e}")
        await update.callback_query.answer("❌ حدث خطأ في المعالجة")

@admin_only
async def handle_task_search(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """معالجة البحث عن المهمة بالكود"""
    try:
        if context.user_data.get('awaiting_task_search'):
            search_code = text.strip().upper()
            
            # البحث عن المهمة بالكود
            found_task = None
            for task in db.data.get("tasks_new", []):
                if task.get('code') == search_code:
                    found_task = task
                    break
            
            if not found_task:
                await update.message.reply_text(
                    f"❌ **لم يتم العثور على المهمة**\n\n"
                    f"الكود: `{search_code}` غير موجود في النظام",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="tasks_menu")]]),
                    parse_mode='Markdown'
                )
                return
            
            # عرض تفاصيل المهمة
            await show_task_details_admin(update, context, found_task)
            
            context.user_data.pop('awaiting_task_search', None)
            
    except Exception as e:
        logger.error(f"خطأ في handle_task_search: {e}")
        await update.message.reply_text("❌ حدث خطأ في البحث")

@admin_only
async def show_task_details_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, task):
    """عرض تفاصيل المهمة للإدارة مع معلومات المالك"""
    try:
        task_id = task.get('id')
        task_code = task.get('code', 'غير متوفر')
        task_name = task.get('name', 'بدون اسم')
        task_type = task.get('type', 'غير معروف')
        task_price = task.get('price', 0)
        task_count = task.get('count', 0)
        completed_count = task.get('completed_count', 0)
        remaining = task_count - completed_count
        owner_id = task.get('owner_id', 'غير معروف')
        
        # الحصول على معلومات المالك
        owner_info = await get_owner_info(context, owner_id)
        
        message = f"""
🎯 **تفاصيل المهمة - لوحة التحكم**

┌────────────────────────────
│ 🏷️ **الاسم:** {task_name}
│ 📊 **النوع:** {task_type}
│ 💰 **السعر:** {task_price} نقطة
│ 👥 **المطلوب:** {task_count} منفذ
│ ✅ **المكتمل:** {completed_count}
│ 🔄 **المتبقي:** {remaining}
│ 🆔 **الكود:** `{task_code}`
└────────────────────────────

👤 **معلومات صاحب المهمة:**
• **ايدي المستخدم:** `{owner_id}`
• **المعرف:** {owner_info['username']}
• **الاسم:** {owner_info['name']}

🔗 **الرابط:** {task.get('link', 'بدون رابط')}
📝 **الوصف:** {task.get('description', 'بدون وصف')}
🎯 **متطلبات الإثبات:** {task.get('proof', 'بدون متطلبات')}

⏰ **تاريخ النشر:** {task.get('created_at', 'غير معروف')}
"""
        
        keyboard = [
            [InlineKeyboardButton("🗑️ حذف هذه المهمة", callback_data=f"delete_task_{task_id}")],
            [InlineKeyboardButton("🔍 بحث عن مهمة أخرى", callback_data="tasks_search")],
            [InlineKeyboardButton("🔙 رجوع للإدارة", callback_data="tasks_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"خطأ في show_task_details_admin: {e}")
        await update.callback_query.answer("❌ حدث خطأ في عرض التفاصيل")

async def get_owner_info(context: ContextTypes.DEFAULT_TYPE, owner_id):
    """الحصول على معلومات المالك"""
    try:
        if owner_id and owner_id != 'غير معروف':
            user = await context.bot.get_chat(owner_id)
            return {
                'name': user.first_name or 'بدون اسم',
                'username': f"@{user.username}" if user.username else "بدون معرف"
            }
    except:
        pass
    
    return {'name': 'غير معروف', 'username': 'بدون معرف'}

@admin_only
async def delete_task(update: Update, context: ContextTypes.DEFAULT_TYPE, task_id):
    """حذف المهمة"""
    try:
        task = db.get_task(task_id)
        
        if not task:
            await update.callback_query.answer("❌ المهمة غير موجودة")
            return
        
        task_name = task.get('name', 'غير معروف')
        task_owner = task.get('owner_id')
        
        # حذف المهمة من قاعدة البيانات
        for i, t in enumerate(db.data["tasks_new"]):
            if str(t.get("id")) == str(task_id):
                db.data["tasks_new"].pop(i)
                break
        
        # حذف جميع الإثباتات المرتبطة بهذه المهمة
        db.data["proofs"] = [proof for proof in db.data["proofs"] if proof.get("task_id") != task_id]
        
        # حفظ التغييرات
        db.save_data()
        
        # إرسال إشعار للمالك
        try:
            if task_owner:
                await context.bot.send_message(
                    chat_id=task_owner,
                    text=f"❌ **تم حذف مهمتك من قبل الإدارة**\n\n"
                         f"🏷️ المهمة: {task_name}\n"
                         f"📝 السبب: مخالفة شروط الاستخدام\n\n"
                         f"📞 للاستفسار: @E8EOE",
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"⚠️ خطأ في إرسال إشعار للمالك: {e}")
        
        await update.callback_query.answer(f"✅ تم حذف المهمة: {task_name}")
        
        # العودة إلى قائمة البحث
        await search_task_prompt(update, context)
            
    except Exception as e:
        logger.error(f"❌ خطأ في delete_task: {e}")
