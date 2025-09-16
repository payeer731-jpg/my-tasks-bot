# Admin/PinSettings.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from Data import db
from Decorators import admin_only
import logging

logger = logging.getLogger(__name__)

@admin_only
async def pin_settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج إعدادات التثبيت"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "pin_settings_menu":
        await pin_settings_menu(update, context)
    elif data == "set_pin_price":
        await set_pin_price_prompt(update, context)
    elif data == "set_pin_duration":
        await set_pin_duration_prompt(update, context)
    elif data == "set_max_pins":
        await set_max_pins_prompt(update, context)

@admin_only
async def pin_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """قائمة إعدادات التثبيت"""
    try:
        pin_settings = db.data.get("pin_settings", {})
        pin_price = pin_settings.get("pin_price", 10)
        pin_duration = pin_settings.get("pin_duration", 24)
        max_pins = pin_settings.get("max_pins", 5)
        
        # إحصائيات التثبيت
        pinned_tasks = db.get_pinned_tasks()
        active_pins = len(pinned_tasks)
        
        message = f"""
📌 **إعدادات تثبيت المهام**

💰 سعر التثبيت: {pin_price} نقطة
⏰ مدة التثبيت: {pin_duration} ساعة
📊 الحد الأقصى: {max_pins} مهمة لكل مستخدم

📈 الإحصائيات:
• المهام المثبتة النشطة: {active_pins}
"""
        
        keyboard = [
            [InlineKeyboardButton("💰 تعيين سعر التثبيت", callback_data="set_pin_price")],
            [InlineKeyboardButton("⏰ تعيين مدة التثبيت", callback_data="set_pin_duration")],
            [InlineKeyboardButton("📊 تعيين الحد الأقصى", callback_data="set_max_pins")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"خطأ في pin_settings_menu: {e}")
        await update.callback_query.answer("❌ حدث خطأ في عرض القائمة")

@admin_only
async def set_pin_price_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مطالبة بتعيين سعر التثبيت"""
    try:
        pin_settings = db.data.get("pin_settings", {})
        current_price = pin_settings.get("pin_price", 10)
        
        await update.callback_query.edit_message_text(
            f"💰 **تعيين سعر التثبيت**\n\n"
            f"السعر الحالي: {current_price} نقطة\n\n"
            f"📝 أدخل السعر الجديد:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="pin_settings_menu")]]),
            parse_mode='Markdown'
        )
        context.user_data['awaiting_pin_price'] = True
        
    except Exception as e:
        logger.error(f"خطأ في set_pin_price_prompt: {e}")
        await update.callback_query.answer("❌ حدث خطأ في المعالجة")

@admin_only
async def set_pin_duration_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مطالبة بتعيين مدة التثبيت"""
    try:
        pin_settings = db.data.get("pin_settings", {})
        current_duration = pin_settings.get("pin_duration", 24)
        
        await update.callback_query.edit_message_text(
            f"⏰ **تعيين مدة التثبيت**\n\n"
            f"المدة الحالية: {current_duration} ساعة\n\n"
            f"📝 أدخل المدة الجديدة (بالساعات):",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="pin_settings_menu")]]),
            parse_mode='Markdown'
        )
        context.user_data['awaiting_pin_duration'] = True
        
    except Exception as e:
        logger.error(f"خطأ في set_pin_duration_prompt: {e}")
        await update.callback_query.answer("❌ حدث خطأ في المعالجة")

@admin_only
async def set_max_pins_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مطالبة بتعيين الحد الأقصى للمهام المثبتة"""
    try:
        pin_settings = db.data.get("pin_settings", {})
        current_max = pin_settings.get("max_pins", 5)
        
        await update.callback_query.edit_message_text(
            f"📊 **تعيين الحد الأقصى للمهام المثبتة**\n\n"
            f"الحد الحالي: {current_max} مهمة لكل مستخدم\n\n"
            f"📝 أدخل الحد الجديد:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="pin_settings_menu")]]),
            parse_mode='Markdown'
        )
        context.user_data['awaiting_max_pins'] = True
        
    except Exception as e:
        logger.error(f"خطأ في set_max_pins_prompt: {e}")
        await update.callback_query.answer("❌ حدث خطأ في المعالجة")

@admin_only
async def handle_pin_settings_messages(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """معالجة رسائل إعدادات التثبيت"""
    try:
        if context.user_data.get('awaiting_pin_price'):
            try:
                price = int(text)
                if price < 0:
                    await update.message.reply_text("❌ السعر يجب أن يكون أكبر من الصفر")
                    return
                    
                if "pin_settings" not in db.data:
                    db.data["pin_settings"] = {}
                
                db.data["pin_settings"]["pin_price"] = price
                db.save_data()
                
                await update.message.reply_text(
                    f"✅ تم تعيين سعر التثبيت إلى {price} نقطة",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📋 العودة", callback_data="pin_settings_menu")]])
                )
                
            except ValueError:
                await update.message.reply_text("❌ يجب إدخال رقم صحيح")
            finally:
                context.user_data.pop('awaiting_pin_price', None)
            return
            
        elif context.user_data.get('awaiting_pin_duration'):
            try:
                duration = int(text)
                if duration < 1:
                    await update.message.reply_text("❌ المدة يجب أن تكون ساعة على الأقل")
                    return
                    
                if "pin_settings" not in db.data:
                    db.data["pin_settings"] = {}
                
                db.data["pin_settings"]["pin_duration"] = duration
                db.save_data()
                
                await update.message.reply_text(
                    f"✅ تم تعيين مدة التثبيت إلى {duration} ساعة",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📋 العودة", callback_data="pin_settings_menu")]])
                )
                
            except ValueError:
                await update.message.reply_text("❌ يجب إدخال رقم صحيح")
            finally:
                context.user_data.pop('awaiting_pin_duration', None)
            return
            
        elif context.user_data.get('awaiting_max_pins'):
            try:
                max_pins = int(text)
                if max_pins < 1:
                    await update.message.reply_text("❌ الحد يجب أن يكون 1 على الأقل")
                    return
                    
                if "pin_settings" not in db.data:
                    db.data["pin_settings"] = {}
                
                db.data["pin_settings"]["max_pins"] = max_pins
                db.save_data()
                
                await update.message.reply_text(
                    f"✅ تم تعيين الحد الأقصى إلى {max_pins} مهمة",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📋 العودة", callback_data="pin_settings_menu")]])
                )
                
            except ValueError:
                await update.message.reply_text("❌ يجب إدخال رقم صحيح")
            finally:
                context.user_data.pop('awaiting_max_pins', None)
            return
            
    except Exception as e:
        logger.error(f"خطأ في handle_pin_settings_messages: {e}")
        await update.message.reply_text("❌ حدث خطأ في المعالجة")