# Admin/TasksChannels.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from Data import db
from Decorators import owner_only
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# قنوات المهام الافتراضية
TASKS_CHANNEL = "@AvailableTasksChannel"
COMPLETED_TASKS_CHANNEL = "@CompletedTasksChannel"

async def send_task_to_channel(task_data, context: ContextTypes.DEFAULT_TYPE):
    """
    إرسال مهمة جديدة إلى قناة المهام المتاحة
    """
    try:
        # الحصول على إعدادات القنوات من قاعدة البيانات
        tasks_channel = db.data.get("tasks_channel", TASKS_CHANNEL)
        
        # تنسيق رسالة المهمة بشكل مختصر
        message = format_task_message(task_data)
        
        # إرسال الرسالة إلى القناة
        sent_message = await context.bot.send_message(
            chat_id=tasks_channel,
            text=message,
            parse_mode='HTML'
        )
        
        # حفظ معرف الرسالة في بيانات المهمة
        task_id = task_data['id']
        for task in db.data["tasks_new"]:
            if task['id'] == task_id:
                task['channel_message_id'] = sent_message.message_id
                break
        
        db.save_data()
        logger.info(f"✅ تم إرسال المهمة {task_id} إلى القناة المتاحة")
        return True
        
    except Exception as e:
        logger.error(f"❌ خطأ في إرسال المهمة إلى القناة: {e}")
        return False

async def move_task_to_completed(task_id, context: ContextTypes.DEFAULT_TYPE):
    """
    نقل المهمة من قناة المهام المتاحة إلى قناة المهام المنتهية
    """
    try:
        logger.info(f"🔍 بدء نقل المهمة {task_id} إلى القناة المنتهية")
        
        task = db.get_task(task_id)
        if not task:
            logger.error(f"❌ المهمة غير موجودة: {task_id}")
            return False
        
        tasks_channel = db.data.get("tasks_channel", TASKS_CHANNEL)
        completed_channel = db.data.get("completed_tasks_channel", COMPLETED_TASKS_CHANNEL)
        
        logger.info(f"📋 القناة المتاحة: {tasks_channel}")
        logger.info(f"✅ القناة المنتهية: {completed_channel}")
        logger.info(f"📝 معرف رسالة القناة: {task.get('channel_message_id')}")
        
        # حذف الرسالة من قناة المهام المتاحة
        if task.get('channel_message_id'):
            try:
                logger.info(f"🗑️ جاري حذف الرسالة من القناة المتاحة...")
                await context.bot.delete_message(
                    chat_id=tasks_channel,
                    message_id=task['channel_message_id']
                )
                logger.info(f"✅ تم حذف الرسالة من القناة المتاحة")
            except Exception as e:
                logger.error(f"⚠️ خطأ في حذف الرسالة: {e}")
                # نستمر حتى لو فشل الحذف
        
        # إرسال المهمة إلى قناة المهام المنتهية
        message = format_completed_task_message(task)
        
        try:
            logger.info(f"📤 جاري إرسال المهمة إلى القناة المنتهية...")
            await context.bot.send_message(
                chat_id=completed_channel,
                text=message,
                parse_mode='HTML'
            )
            logger.info(f"✅ تم إرسال المهمة إلى القناة المنتهية")
            
            # تنظيف بيانات المهمة
            task['channel_message_id'] = None
            db.save_data()
            
            logger.info(f"🎉 تم نقل المهمة {task_id} بنجاح!")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في إرسال المهمة للقناة المنتهية: {e}")
            return False
        
    except Exception as e:
        logger.error(f"❌ خطأ في move_task_to_completed: {e}")
        return False

def format_task_message(task_data):
    """
    تنسيق رسالة المهمة للعرض في القناة بشكل مختصر
    """
    return f"""
🎯 <b>تم إضافة مهمة جديدة</b>

┌────────────────────────────
│ <b>🏷️ الاسم:</b> {task_data.get('name', 'غير معروف')}
│ <b>📊 النوع:</b> {task_data.get('type', 'غير معروف')}
│ <b>💰 السعر:</b> {task_data.get('price', 0)} نقطة
│ <b>👥 العدد المطلوب:</b> {task_data.get('count', 0)}
│ <b>🆔 كود المهمة:</b> <code>{task_data.get('code', 'غير معروف')}</code>
│ <b>⏰ تاريخ الإنشاء:</b> {task_data.get('created_at', 'غير معروف')}
└────────────────────────────
    """

def format_completed_task_message(task_data):
    """
    تنسيق رسالة المهمة المنتهية بشكل مختصر
    """
    completion_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return f"""
✅ <b>مهمة منتهية</b>

┌────────────────────────────
│ <b>🏷️ الاسم:</b> {task_data.get('name', 'غير معروف')}
│ <b>📊 النوع:</b> {task_data.get('type', 'غير معروف')}
│ <b>💰 السعر:</b> {task_data.get('price', 0)} نقطة
│ <b>👥 العدد المطلوب:</b> {task_data.get('count', 0)}
│ <b>✅ تم إكمال:</b> {task_data.get('completed_count', 0)}/{task_data.get('count', 0)}
│ <b>🆔 كود المهمة:</b> <code>{task_data.get('code', 'غير معروف')}</code>
│ <b>⏰ تاريخ الإنشاء:</b> {task_data.get('created_at', 'غير معروف')}
│ <b>⏱️ تاريخ الانتهاء:</b> {completion_time}
└────────────────────────────
    """

# دوال الإعدادات
@owner_only
async def tasks_channels_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    معالج أوامر قنوات المهام
    """
    try:
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "tasks_channels_menu":
            await show_tasks_channels_menu(update, context)
        elif data == "set_tasks_channel":
            await set_tasks_channel_prompt(update, context)
        elif data == "set_completed_channel":
            await set_completed_channel_prompt(update, context)
        elif data == "test_channels":
            await test_channels(update, context)
        else:
            await query.answer("❌ أمر غير معروف")
            
    except Exception as e:
        logger.error(f"❌ خطأ في tasks_channels_handler: {e}")
        await update.callback_query.answer("❌ حدث خطأ في المعالجة")

@owner_only
async def show_tasks_channels_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    عرض قائمة إعدادات قنوات المهام
    """
    try:
        tasks_channel = db.data.get("tasks_channel", TASKS_CHANNEL)
        completed_channel = db.data.get("completed_tasks_channel", COMPLETED_TASKS_CHANNEL)
        
        # اختبار صلاحية القنوات
        tasks_valid = await check_channel_validity(tasks_channel, context)
        completed_valid = await check_channel_validity(completed_channel, context)
        
        tasks_status = "✅ صالحة" if tasks_valid else "❌ غير صالحة"
        completed_status = "✅ صالحة" if completed_valid else "❌ غير صالحة"
        
        message = f"""
📊 <b>إعدادات قنوات المهام</b>

┌────────────────────────────
│ <b>📋 قناة المهام المتاحة:</b> {tasks_channel}
│ <b>الحالة:</b> {tasks_status}
│ 
│ <b>✅ قناة المهام المنتهية:</b> {completed_channel}
│ <b>الحالة:</b> {completed_status}
└────────────────────────────

⚙️ <i>يمكنك تغيير القنوات من خلال الأزرار أدناه</i>
        """
        
        keyboard = [
            [InlineKeyboardButton("📋 تعيين قناة المهام", callback_data="set_tasks_channel")],
            [InlineKeyboardButton("✅ تعيين قناة المنتهية", callback_data="set_completed_channel")],
            [InlineKeyboardButton("🧪 اختبار القنوات", callback_data="test_channels")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"❌ خطأ في show_tasks_channels_menu: {e}")
        await update.callback_query.answer("❌ حدث خطأ في عرض القائمة")

async def check_channel_validity(channel_username, context: ContextTypes.DEFAULT_TYPE):
    """
    التحقق من صلاحية القناة
    """
    try:
        chat = await context.bot.get_chat(channel_username)
        # التحقق من أن البوت يمكنه إرسال الرسائل
        try:
            await context.bot.send_message(
                chat_id=channel_username,
                text="🔍 اختبار صلاحية القناة...",
                parse_mode='HTML'
            )
            return True
        except:
            return False
            
    except Exception as e:
        logger.error(f"❌ خطأ في التحقق من القناة {channel_username}: {e}")
        return False

@owner_only
async def test_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    اختبار صلاحية القنوات
    """
    try:
        query = update.callback_query
        await query.answer()
        
        tasks_channel = db.data.get("tasks_channel", TASKS_CHANNEL)
        completed_channel = db.data.get("completed_tasks_channel", COMPLETED_TASKS_CHANNEL)
        
        tasks_valid = await check_channel_validity(tasks_channel, context)
        completed_valid = await check_channel_validity(completed_channel, context)
        
        if tasks_valid and completed_valid:
            await query.answer("✅ جميع القنوات صالحة وتعامل بنجاح", show_alert=True)
        else:
            message = "❌ هناك مشاكل في القنوات:\n"
            if not tasks_valid:
                message += f"• قناة المهام {tasks_channel} غير صالحة\n"
            if not completed_valid:
                message += f"• قناة المنتهية {completed_channel} غير صالحة\n"
            message += "\n📝 تأكد من:\n• إضافة البوت كمدير\n• منح البوت صلاحية إرسال الرسائل\n• منح البوت صلاحية حذف الرسائل"
            
            await query.answer(message, show_alert=True)
            
    except Exception as e:
        logger.error(f"❌ خطأ في اختبار القنوات: {e}")
        await query.answer("❌ حدث خطأ في اختبار القنوات")

@owner_only
async def set_tasks_channel_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    مطالبة بإدخال قناة المهام الجديدة
    """
    try:
        await update.callback_query.edit_message_text(
            "📋 أرسل معرف قناة المهام المتاحة (مثال: @AvailableTasks):\n\n"
            "📝 تأكد من:\n"
            "• إضافة البوت كمدير في القناة\n"
            "• منح البوت صلاحية إرسال الرسائل\n"
            "• منح البوت صلاحية حذف الرسائل",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="tasks_channels_menu")]])
        )
        context.user_data['awaiting_tasks_channel'] = True
        
    except Exception as e:
        logger.error(f"❌ خطأ في set_tasks_channel_prompt: {e}")
        await update.callback_query.answer("❌ حدث خطأ في المعالجة")

@owner_only
async def set_completed_channel_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    مطالبة بإدخال قناة المهام المنتهية الجديدة
    """
    try:
        await update.callback_query.edit_message_text(
            "✅ أرسل معرف قناة المهام المنتهية (مثال: @CompletedTasks):\n\n"
            "📝 تأكد من:\n"
            "• إضافة البوت كمدير في القناة\n"
            "• منح البوت صلاحية إرسال الرسائل",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="tasks_channels_menu")]])
        )
        context.user_data['awaiting_completed_channel'] = True
        
    except Exception as e:
        logger.error(f"❌ خطأ في set_completed_channel_prompt: {e}")
        await update.callback_query.answer("❌ حدث خطأ في المعالجة")

async def handle_tasks_channels_settings(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """
    معالجة إعدادات قنوات المهام من الرسائل النصية
    """
    try:
        if context.user_data.get('awaiting_tasks_channel'):
            # تعيين قناة المهام المتاحة
            channel_username = text.strip()
            if not channel_username.startswith('@'):
                channel_username = '@' + channel_username
                
            # التحقق من صلاحية القناة
            valid = await check_channel_validity(channel_username, context)
            if not valid:
                await update.message.reply_text(
                    f"❌ القناة {channel_username} غير صالحة\n"
                    "📝 تأكد من إضافة البوت كمدير ومنحه الصلاحيات اللازمة",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="tasks_channels_menu")]])
                )
                return
                
            db.data["tasks_channel"] = channel_username
            db.save_data()
            
            await update.message.reply_text(
                f"✅ تم تعيين قناة المهام المتاحة: {channel_username}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="tasks_channels_menu")]])
            )
            context.user_data.pop('awaiting_tasks_channel', None)
            
        elif context.user_data.get('awaiting_completed_channel'):
            # تعيين قناة المهام المنتهية
            channel_username = text.strip()
            if not channel_username.startswith('@'):
                channel_username = '@' + channel_username
                
            # التحقق من صلاحية القناة
            valid = await check_channel_validity(channel_username, context)
            if not valid:
                await update.message.reply_text(
                    f"❌ القناة {channel_username} غير صالحة\n"
                    "📝 تأكد من إadding البوت كمدير ومنحه صلاحية إرسال الرسائل",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="tasks_channels_menu")]])
                )
                return
                
            db.data["completed_tasks_channel"] = channel_username
            db.save_data()
            
            await update.message.reply_text(
                f"✅ تم تعيين قناة المهام المنتهية: {channel_username}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="tasks_channels_menu")]])
            )
            context.user_data.pop('awaiting_completed_channel', None)
            
    except Exception as e:
        logger.error(f"❌ خطأ في handle_tasks_channels_settings: {e}")
        await update.message.reply_text(
            "❌ حدث خطأ في تعيين القناة",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="tasks_channels_menu")]])
        )