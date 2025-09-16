# Admin/ProfitSettings.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from Data import db
from Decorators import admin_only
import logging

logger = logging.getLogger(__name__)

@admin_only
async def profit_settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج إعدادات الأرباح والحدود"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "profit_settings_menu":
        await profit_settings_menu(update, context)
    elif data == "set_profit_percentage":
        await set_profit_percentage_prompt(update, context)
    elif data == "set_task_limits":
        await task_limits_menu(update, context)
    elif data.startswith("limit_"):
        task_type = data.split("_")[1]
        await set_task_limit_prompt(update, context, task_type)

@admin_only
async def profit_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """قائمة إعدادات الأرباح والحدود"""
    try:
        profit_percentage = db.data.get("profit_percentage", 15)
        task_limits = db.data.get("task_limits", {})
        
        message = f"""
💰 **إعدادات الأرباح والحدود**

📊 **النسبة الحالية:** {profit_percentage}%
        
📋 **الحدود الحالية للمهام:**
"""
        
        for task_type, limits in task_limits.items():
            message += f"• {task_type}: {limits['min']} - {limits['max']} نقطة\n"
        
        message += "\n🎯 اختر الإعداد الذي تريد تعديله:"
        
        keyboard = [
            [InlineKeyboardButton("📊 تعيين نسبة الأرباح", callback_data="set_profit_percentage")],
            [InlineKeyboardButton("📋 تعيين حدود المهام", callback_data="set_task_limits")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"خطأ في profit_settings_menu: {e}")
        await update.callback_query.answer("❌ حدث خطأ في عرض القائمة")

@admin_only
async def set_profit_percentage_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مطالبة بتعيين نسبة الأرباح"""
    try:
        current_percentage = db.data.get("profit_percentage", 15)
        
        await update.callback_query.edit_message_text(
            f"💰 **تعيين نسبة الأرباح**\n\n"
            f"📊 النسبة الحالية: {current_percentage}%\n\n"
            f"📝 أدخل النسبة الجديدة (0-50):",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="profit_settings_menu")]]),
            parse_mode='Markdown'
        )
        context.user_data['awaiting_profit_percentage'] = True
        
    except Exception as e:
        logger.error(f"خطأ في set_profit_percentage_prompt: {e}")
        await update.callback_query.answer("❌ حدث خطأ في المعالجة")

@admin_only
async def task_limits_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """قائمة تعيين حدود المهام"""
    try:
        task_limits = db.data.get("task_limits", {})
        
        message = "📋 **تعيين حدود المهام**\n\nاختر نوع المهمة:\n"
        
        keyboard = []
        for task_type in task_limits.keys():
            limits = task_limits[task_type]
            keyboard.append([
                InlineKeyboardButton(
                    f"📱 {task_type} ({limits['min']}-{limits['max']})", 
                    callback_data=f"limit_{task_type}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="profit_settings_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"خطأ في task_limits_menu: {e}")
        await update.callback_query.answer("❌ حدث خطأ في عرض القائمة")

@admin_only
async def set_task_limit_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE, task_type):
    """مطالبة بتعيين حدود مهمة محددة"""
    try:
        task_limits = db.data.get("task_limits", {})
        limits = task_limits.get(task_type, {"min": 1, "max": 10})
        
        await update.callback_query.edit_message_text(
            f"📊 **تعيين حدود مهمة {task_type}**\n\n"
            f"📋 الحدود الحالية: {limits['min']} - {limits['max']} نقطة\n\n"
            f"📝 أدخل الحد الأدنى والحد الأقصى (مثال: 2 10):",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="set_task_limits")]]),
            parse_mode='Markdown'
        )
        context.user_data['awaiting_task_limits'] = task_type
        
    except Exception as e:
        logger.error(f"خطأ في set_task_limit_prompt: {e}")
        await update.callback_query.answer("❌ حدث خطأ في المعالجة")

@admin_only
async def handle_profit_settings_messages(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """معالجة رسائل إعدادات الأرباح"""
    try:
        if context.user_data.get('awaiting_profit_percentage'):
            try:
                percentage = int(text)
                if 0 <= percentage <= 50:
                    db.data["profit_percentage"] = percentage
                    db.save_data()
                    await update.message.reply_text(
                        f"✅ تم تعيين نسبة الأرباح إلى {percentage}%",
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📋 العودة", callback_data="profit_settings_menu")]])
                    )
                else:
                    await update.message.reply_text("❌ النسبة يجب أن تكون بين 0 و 50")
            except ValueError:
                await update.message.reply_text("❌ يجب إدخال رقم صحيح")
            finally:
                context.user_data.pop('awaiting_profit_percentage', None)
            return
            
        elif context.user_data.get('awaiting_task_limits'):
            task_type = context.user_data['awaiting_task_limits']
            try:
                parts = text.split()
                if len(parts) == 2:
                    min_price = int(parts[0])
                    max_price = int(parts[1])
                    
                    if min_price <= max_price and min_price >= 0:
                        if "task_limits" not in db.data:
                            db.data["task_limits"] = {}
                        
                        db.data["task_limits"][task_type] = {
                            "min": min_price,
                            "max": max_price
                        }
                        db.save_data()
                        
                        await update.message.reply_text(
                            f"✅ تم تعيين حدود مهمة {task_type} إلى {min_price} - {max_price} نقطة",
                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📋 العودة", callback_data="set_task_limits")]])
                        )
                    else:
                        await update.message.reply_text("❌ الحد الأدنى يجب أن يكون أقل أو يساوي الحد الأقصى")
                else:
                    await update.message.reply_text("❌ تنسيق غير صحيح. استخدم: الحد_الأدنى الحد_الأقصى")
            except ValueError:
                await update.message.reply_text("❌ يجب إدخال أرقام صحيحة")
            finally:
                context.user_data.pop('awaiting_task_limits', None)
            return
            
    except Exception as e:
        logger.error(f"خطأ في handle_profit_settings_messages: {e}")
        await update.message.reply_text("❌ حدث خطأ في المعالجة")