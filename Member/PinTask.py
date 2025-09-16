# Member/PinTask.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from Data import db
from Decorators import user_only
import logging

logger = logging.getLogger(__name__)

# PinTask.py - الإصلاح النهائي
# في PinTask.py - تحديث معالجة التثبيت
@user_only
async def pin_task_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, task_id: str):
    """معالجة تثبيت المهمة مع تطبيق مزايا المستوى - الإصدار المصحح"""
    try:
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        task = db.get_task(task_id)
        
        if not task:
            await query.edit_message_text("❌ المهمة غير موجودة")
            return
        
        # ✅ التحقق من ملكية المهمة
        if str(task.get('owner_id')) != str(user_id):
            await query.edit_message_text("❌ ليس لديك صلاحية تثبيت هذه المهمة")
            return
        
        # ✅ التحقق من التثبيت المجاني لمستوى الأسطورة
        if db.can_user_pin_free(user_id):
            # تثبيت مجاني لمدة 24 ساعة
            success, result = db.pin_task(user_id, task_id, 24)
            
            if success:
                level_name = db.get_user_level_name(user_id)
                message = f"""
🎯 **تثبيت مجاني - ميزانية {level_name}**

🏆 مستواك: {level_name}
📌 المهمة: {task.get('name', 'بدون اسم')}
💰 السعر: مجاني (ميزانية {level_name})
⏰ المدة: 24 ساعة

✅ تم تثبيت المهمة بنجاح!
"""
            else:
                message = f"❌ {result}"
            
            await query.edit_message_text(message, parse_mode='Markdown')
            return
        
        # ✅ التثبيت العادي للمستخدمين الآخرين
        user_data = db.get_user(user_id)
        pin_settings = db.data.get("pin_settings", {})
        pin_price = pin_settings.get("pin_price", 10)
        pin_duration = pin_settings.get("pin_duration", 24)
        max_pins = pin_settings.get("max_pins", 5)
        
        # التحقق من الحد الأقصى للمهام المثبتة
        user_pinned_tasks = [p for p in db.get_pinned_tasks().values() if str(p['user_id']) == str(user_id)]
        if len(user_pinned_tasks) >= max_pins:
            await query.edit_message_text(f"❌ وصلت للحد الأقصى للمهام المثبتة ({max_pins})")
            return
        
        # التحقق من رصيد النقاط
        if user_data["points"] < pin_price:
            await query.edit_message_text(f"❌ نقاطك غير كافية. تحتاج {pin_price} نقاط")
            return
        
        message = f"""
📌 **تثبيت المهمة:** {task.get('name', 'بدون اسم')}

💰 السعر: {pin_price} نقاط
⏰ المدة: {pin_duration} ساعة
📊 المثبتة: {len(user_pinned_tasks)}/{max_pins}
🎯 مستواك: {db.get_level_info(db.get_user_level(user_id)).get('name')}

✅ تأكيد التثبيت؟
"""
        
        keyboard = [
            [InlineKeyboardButton("✅ نعم، تأكيد التثبيت", callback_data=f"confirm_pin_{task_id}")],
            [InlineKeyboardButton("❌ إلغاء", callback_data=f"view_task_{task_id}")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة التثبيت: {e}")
        await update.callback_query.answer("❌ حدث خطأ في المعالجة")

@user_only
async def handle_confirm_pin(update: Update, context: ContextTypes.DEFAULT_TYPE, task_id):
    """معالج تأكيد التثبيت"""
    try:
        query = update.callback_query
        user_id = update.effective_user.id
        
        # تثبيت المهمة
        pin_duration = db.data.get("pin_settings", {}).get("pin_duration", 24)
        success, message = db.pin_task(user_id, task_id, pin_duration)
        
        if success:
            await query.edit_message_text(
                f"✅ {message}\n\n"
                f"📌 المهمة مثبتة الآن في الصفحة الأولى\n"
                f"⏰ تنتهي بعد {pin_duration} ساعة",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                f"❌ {message}",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"خطأ في handle_confirm_pin: {e}")
        await update.callback_query.answer("❌ حدث خطأ في التثبيت")

@user_only
async def confirm_pin_task(update: Update, context: ContextTypes.DEFAULT_TYPE, task_id):
    """تأكيد تثبيت المهمة"""
    try:
        query = update.callback_query
        user_id = update.effective_user.id
        
        # تثبيت المهمة
        pin_duration = db.data.get("pin_settings", {}).get("pin_duration", 24)
        success, message = db.pin_task(user_id, task_id, pin_duration)
        
        if success:
            await query.edit_message_text(
                f"✅ {message}\n\n"
                f"📌 المهمة مثبتة الآن في الصفحة الأولى\n"
                f"⏰ تنتهي بعد {pin_duration} ساعة",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                f"❌ {message}",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"خطأ في confirm_pin_task: {e}")
        await update.callback_query.answer("❌ حدث خطأ في التثبيت")

@user_only
async def unpin_task_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, task_id):
    """إلغاء تثبيت المهمة"""
    try:
        query = update.callback_query
        user_id = update.effective_user.id
        
        success = db.unpin_task(task_id)
        
        if success:
            await query.answer("✅ تم إلغاء تثبيت المهمة")
            # العودة لتفاصيل المهمة
            from Member.Tasks_View import show_task_details
            await show_task_details(update, context, task_id)
        else:
            await query.answer("❌ لم يتم العثور على تثبيت للمهمة")
            
    except Exception as e:
        logger.error(f"خطأ في unpin_task_handler: {e}")
        await update.callback_query.answer("❌ حدث خطأ في الإلغاء")

# إضافة معالج التأكيد
@user_only
async def handle_confirm_pin(update: Update, context: ContextTypes.DEFAULT_TYPE, task_id):
    """معالج تأكيد التثبيت"""
    try:
        query = update.callback_query
        await confirm_pin_task(update, context, task_id)
        return True
    except Exception as e:
        logger.error(f"خطأ في handle_confirm_pin: {e}")
        return False