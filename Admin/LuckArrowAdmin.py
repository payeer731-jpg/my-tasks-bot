# Admin/LuckArrowAdmin.py - نظام إدارة سهم الحظ الكامل - الجزء 1/3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from Data import db
from Decorators import admin_only
import logging
import random

logger = logging.getLogger(__name__)

@admin_only
async def luck_arrow_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """قائمة إدارة سهم الحظ - إصدار فارغ"""
    try:
        settings = db.get_luck_arrow_settings()
        box_status = db.get_box_status()
        
        message = f"""
🎯 **إدارة سهم الحظ**

📦 **حالة الصندوق:** {'✅ مفتوح' if box_status['is_open'] else '❌ مغلق'}
🔢 **السعة:** {box_status['total']} سهم (صندوق فارغ)
🎯 **المستخدم:** {box_status['used']} سهم
🏹 **المتبقي:** {box_status['remaining']} سهم

⚙️ **الإعدادات الحالية:**
• الحد اليومي: {settings.get('daily_spin_limit', 10)} رمية
• الأسهم في الدعوة: {settings.get('invite_arrows', 1)} سهم
• النقاط في الدعوة: {settings.get('invite_points', 1)} نقطة
• عدد الجوائز المضافة: {len(settings.get('prizes', []))} جائزة

🎰 **اختر الإجراء:**
"""
        
        keyboard = [
            [InlineKeyboardButton("📦 إدارة الصندوق", callback_data="manage_arrow_box")],
            [InlineKeyboardButton("⚙️ الإعدادات", callback_data="arrow_settings")],
            [InlineKeyboardButton("🎯 منح أسهم", callback_data="give_arrows")],
            [InlineKeyboardButton("🎰 إدارة الجوائز", callback_data="manage_prizes")],
            [InlineKeyboardButton("📊 الإحصائيات", callback_data="arrow_stats")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"خطأ في luck_arrow_admin_menu: {e}")
        await update.callback_query.answer("❌ حدث خطأ في تحميل القائمة")

@admin_only
async def manage_arrow_box(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إدارة صندوق الأسهم - إصدار فارغ"""
    try:
        box_status = db.get_box_status()
        
        message = f"""
📦 **إدارة صندوق الأسهم**

🔢 السعة الحالية: {box_status['total']} سهم (صندوق فارغ)
🎯 المستخدم: {box_status['used']} سهم
🏹 المتبقي: {box_status['remaining']} سهم
🚪 الحالة: {'✅ مفتوح' if box_status['is_open'] else '❌ مغلق'}

💡 **ملاحظة:** الصندوق فارغ، الجوائز تُضاف يدوياً فقط

🎯 **اختر الإجراء:**
"""
        
        keyboard = [
            [InlineKeyboardButton("🔢 تعيين السعة", callback_data="set_box_capacity")],
            [InlineKeyboardButton("🔄 إعادة تعيين", callback_data="reset_box")],
            [InlineKeyboardButton(f"🚪 {'إغلاق' if box_status['is_open'] else 'فتح'} الصندوق", 
                                 callback_data="toggle_box")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="luck_arrow_admin")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"خطأ في manage_arrow_box: {e}")
        await update.callback_query.answer("❌ حدث خطأ في المعالجة")

@admin_only
async def arrow_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إعدادات سهم الحظ"""
    try:
        settings = db.get_luck_arrow_settings()
        
        message = f"""
⚙️ **إعدادات سهم الحظ**

📊 الإعدادات الحالية:
• الحد اليومي: {settings.get('daily_spin_limit', 10)} رمية
• الأسهم في الدعوة: {settings.get('invite_arrows', 1)} سهم
• النقاط في الدعوة: {settings.get('invite_points', 1)} نقطة

🎯 **اختر الإعداد لتعديله:**
"""
        
        keyboard = [
            [InlineKeyboardButton("📊 الحد اليومي", callback_data="set_daily_limit")],
            [InlineKeyboardButton("🏹 أسهم الدعوة", callback_data="set_invite_arrows")],
            [InlineKeyboardButton("💰 نقاط الدعوة", callback_data="set_invite_points")],
            [InlineKeyboardButton("🎰 إدارة الجوائز", callback_data="manage_prizes")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="luck_arrow_admin")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"خطأ في arrow_settings_menu: {e}")
        await update.callback_query.answer("❌ حدث خطأ في المعالجة")

@admin_only
async def give_arrows_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مطالبة بمنح أسهم"""
    try:
        await update.callback_query.edit_message_text(
            "🎯 أرسل ايدي المستخدم وعدد الأسهم (مثال: 123456789 5):\n\n"
            "📝 يمكنك إرسال:\n"
            "• ايدي مستخدم + عدد الأسهم\n"
            "• 'all' + عدد الأسهم لمنح الجميع",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="luck_arrow_admin")]])
        )
        context.user_data['awaiting_give_arrows'] = True
        
    except Exception as e:
        logger.error(f"خطأ في give_arrows_prompt: {e}")
        await update.callback_query.answer("❌ حدث خطأ في المعالجة")

@admin_only
async def manage_prizes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إدارة الجوائز"""
    try:
        prizes = db.get_arrow_prize_distribution()
        
        message = "🎰 **إدارة جوائز سهم الحظ**\n\n"
        
        if prizes:
            message += "📊 **توزيع الجوائز الحالي:**\n"
            for i, prize in enumerate(prizes, 1):
                remaining = prize.get('remaining', prize.get('quantity', '∞'))
                message += f"{i}. {prize['text']} - {prize['probability']}% (المتبقي: {remaining})\n"
        else:
            message += "📭 **لا توجد جوائز مضافة حالياً**\n\n"
            message += "💡 استخدم '➕ إضافة جائزة' لإضافة جوائز جديدة"
        
        message += "\n🎯 **اختر الإجراء:**"
        
        keyboard = [
            [InlineKeyboardButton("➕ إضافة جائزة", callback_data="add_prize")],
            [InlineKeyboardButton("✏️ تعديل الجوائز", callback_data="edit_prizes")],
            [InlineKeyboardButton("🔄 الإعدادات الافتراضية", callback_data="reset_prizes")],
            [InlineKeyboardButton("📋 عرض التفاصيل", callback_data="view_prizes")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="luck_arrow_admin")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # محاولة التعديل مع معالجة الخطأ
        try:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        except Exception as e:
            if "Message is not modified" in str(e):
                await update.callback_query.answer("✅ لا يوجد تغيير")
            else:
                logger.error(f"خطأ في تعديل الرسالة: {e}")
                await update.callback_query.answer("❌ حدث خطأ في التحميل")
                
    except Exception as e:
        logger.error(f"خطأ في manage_prizes: {e}")
        await update.callback_query.answer("❌ حدث خطأ في تحميل القائمة")

@admin_only
async def add_prize_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """قائمة إضافة جائزة جديدة"""
    try:
        message = """
🎁 **إضافة جائزة جديدة**

📝 **اختر نوع الجائزة:**
"""
        
        keyboard = [
            [InlineKeyboardButton("💰 نقاط", callback_data="add_prize_points")],
            [InlineKeyboardButton("🏹 أسهم", callback_data="add_prize_arrows")],
            [InlineKeyboardButton("🎁 كود هدية", callback_data="add_prize_gift_code")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="manage_prizes")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"خطأ في add_prize_menu: {e}")
        await update.callback_query.answer("❌ حدث خطأ في تحميل القائمة")

@admin_only
async def add_prize_points_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مطالبة بإضافة جائزة نقاط"""
    try:
        await update.callback_query.edit_message_text(
            "💰 **إضافة جائزة نقاط**\n\n"
            "📝 أرسل القيمة وعدد الجوائز (مثال: 10 100):\n"
            "• القيمة: عدد النقاط\n"
            "• العدد: عدد الجوائز المتاحة\n\n"
            "💡 مثال: لإضافة 100 جائزة بقيمة 10 نقاط لكل منها، أرسل: 10 100",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="add_prize")]])
        )
        context.user_data['awaiting_prize_points'] = True
        context.user_data['prize_type'] = 'points'
        
    except Exception as e:
        logger.error(f"خطأ في add_prize_points_prompt: {e}")
        await update.callback_query.answer("❌ حدث خطأ في المعالجة")

@admin_only
async def add_prize_arrows_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مطالبة بإضافة جائزة أسهم"""
    try:
        await update.callback_query.edit_message_text(
            "🏹 **إضافة جائزة أسهم**\n\n"
            "📝 أرسل القيمة وعدد الجوائز (مثال: 5 50):\n"
            "• القيمة: عدد الأسهم\n"
            "• العدد: عدد الجوائز المتاحة\n\n"
            "💡 مثال: لإضافة 50 جائزة بقيمة 5 أسهم لكل منها، أرسل: 5 50",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="add_prize")]])
        )
        context.user_data['awaiting_prize_arrows'] = True
        context.user_data['prize_type'] = 'arrow'
        
    except Exception as e:
        logger.error(f"خطأ في add_prize_arrows_prompt: {e}")
        await update.callback_query.answer("❌ حدث خطأ في المعالجة")

@admin_only
async def add_prize_gift_code_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مطالبة بإضافة جائزة كود هدية"""
    try:
        await update.callback_query.edit_message_text(
            "🎁 **إضافة جائزة كود هدية**\n\n"
            "📝 أرسل القيمة وعدد الجوائز (مثال: 100 20):\n"
            "• القيمة: عدد النقاط في الكود\n"
            "• العدد: عدد الجوائز المتاحة\n\n"
            "💡 مثال: لإضافة 20 كود هدية بقيمة 100 نقطة لكل منها، أرسل: 100 20",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="add_prize")]])
        )
        context.user_data['awaiting_prize_gift_code'] = True
        context.user_data['prize_type'] = 'gift_code'
        
    except Exception as e:
        logger.error(f"خطأ في add_prize_gift_code_prompt: {e}")
        await update.callback_query.answer("❌ حدث خطأ في المعالجة")

# Admin/LuckArrowAdmin.py - نظام إدارة سهم الحظ الكامل - الجزء 2/3
@admin_only
async def arrow_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض إحصائيات سهم الحظ"""
    try:
        stats = db.get_arrow_stats()
        box_status = db.get_box_status()
        daily_stats = db.get_arrow_daily_stats()
        
        message = f"""
📈 **إحصائيات سهم الحظ**

👥 **المستخدمون:**
• الإجمالي: {stats['total_users']} مستخدم
• النشطون: {stats['active_users']} مستخدم
• الأسهم الموزعة: {stats['total_arrows']} سهم
• الرميات الإجمالية: {stats['total_spins']} رمية

📦 **حالة الصندوق:**
• السعة: {box_status['total']} سهم
• المستخدم: {box_status['used']} سهم
• المتبقي: {box_status['remaining']} سهم
• الحالة: {'✅ مفتوح' if box_status['is_open'] else '❌ مغلق'}

📅 **إحصائيات اليوم:**
• الرميات: {daily_stats['total_spins']}
• الفوز: {daily_stats['successful_spins']}
• النقاط: {daily_stats['points_won']}
• الأسهم: {daily_stats['arrows_won']}
"""
        
        keyboard = [
            [InlineKeyboardButton("🔄 تحديث", callback_data="arrow_stats")],
            [InlineKeyboardButton("📊 التقرير الأسبوعي", callback_data="weekly_report")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="luck_arrow_admin")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"خطأ في arrow_stats: {e}")
        await update.callback_query.answer("❌ حدث خطأ في عرض الإحصائيات")

@admin_only
async def weekly_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض التقرير الأسبوعي"""
    try:
        report = db.get_arrow_weekly_report()
        
        message = f"""
📊 **التقرير الأسبوعي - سهم الحظ**

📅 الفترة: {report['start_date']} إلى {report['end_date']}

📈 **الإحصائيات:**
• الرميات الإجمالية: {report['total_spins']}
• الرميات الناجحة: {report['successful_spins']}
• المستخدمون الفريدون: {report['unique_users']}
• المتوسط اليومي: {report['daily_average']:.1f} رمية

🎁 **الجوائز الموزعة:**
• النقاط: {report['points_distributed']} نقطة
• الأسهم: {report['arrows_distributed']} سهم
• أكواد الهدايا: {report['gift_codes_distributed']} كود
"""
        
        keyboard = [
            [InlineKeyboardButton("📈 الإحصائيات العامة", callback_data="arrow_stats")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="luck_arrow_admin")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"خطأ في weekly_report: {e}")
        await update.callback_query.answer("❌ حدث خطأ في عرض التقرير")

@admin_only
async def view_prizes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض تفاصيل الجوائز"""
    try:
        prizes = db.get_arrow_prize_distribution()
        total_prob = sum(prize['probability'] for prize in prizes)
        
        message = "🎁 **تفاصيل جوائز سهم الحظ**\n\n"
        
        for i, prize in enumerate(prizes, 1):
            message += f"**{i}. {prize['text']}**\n"
            message += f"   - النوع: {prize['type']}\n"
            message += f"   - القيمة: {prize['value']}\n"
            message += f"   - الاحتمال: {prize['probability']}%\n\n"
        
        message += f"📊 مجموع الاحتمالات: {total_prob}%"
        
        if total_prob != 100:
            message += f" ⚠️ (يجب أن يكون 100%)"
        
        keyboard = [
            [InlineKeyboardButton("✏️ تعديل الجوائز", callback_data="edit_prizes")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="manage_prizes")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"خطأ في view_prizes: {e}")
        await update.callback_query.answer("❌ حدث خطأ في عرض الجوائز")

@admin_only
async def set_daily_limit_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مطالبة بتعيين الحد اليومي"""
    try:
        settings = db.get_luck_arrow_settings()
        current_limit = settings.get('daily_spin_limit', 10)
        
        await update.callback_query.edit_message_text(
            f"📊 أرسل الحد اليومي الجديد للرميات:\n\n"
            f"📈 الحد الحالي: {current_limit} رمية يومياً\n"
            f"💡 القيمة الموصى بها: بين 5 و 50 رمية",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="arrow_settings")]])
        )
        context.user_data['awaiting_daily_limit'] = True
        
    except Exception as e:
        logger.error(f"خطأ في set_daily_limit_prompt: {e}")
        await update.callback_query.answer("❌ حدث خطأ في المعالجة")

@admin_only
async def set_invite_arrows_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مطالبة بتعيين أسهم الدعوة"""
    try:
        settings = db.get_luck_arrow_settings()
        current_arrows = settings.get('invite_arrows', 1)
        
        await update.callback_query.edit_message_text(
            f"🏹 أرسل عدد الأسهم الجديد لمكافأة الدعوة:\n\n"
            f"📦 العدد الحالي: {current_arrows} سهم لكل دعوة\n"
            f"💡 القيمة الموصى بها: بين 1 و 10 أسهم",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="arrow_settings")]])
        )
        context.user_data['awaiting_invite_arrows'] = True
        
    except Exception as e:
        logger.error(f"خطأ في set_invite_arrows_prompt: {e}")
        await update.callback_query.answer("❌ حدث خطأ في المعالجة")

@admin_only
async def set_invite_points_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مطالبة بتعيين نقاط الدعوة"""
    try:
        settings = db.get_luck_arrow_settings()
        current_points = settings.get('invite_points', 1)
        
        await update.callback_query.edit_message_text(
            f"💰 أرسل عدد النقاط الإضافية الجديد لمكافأة الدعوة:\n\n"
            f"🎯 العدد الحالي: {current_points} نقطة لكل دعوة\n"
            f"💡 سيتم إضافتها إلى نقاط الدعوة الأساسية",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="arrow_settings")]])
        )
        context.user_data['awaiting_invite_points'] = True
        
    except Exception as e:
        logger.error(f"خطأ في set_invite_points_prompt: {e}")
        await update.callback_query.answer("❌ حدث خطأ في المعالجة")

@admin_only
async def set_box_capacity_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مطالبة بتعيين سعة الصندوق"""
    try:
        box_status = db.get_box_status()
        
        await update.callback_query.edit_message_text(
            f"🔢 أرسل السعة الجديدة للصندوق:\n\n"
            f"📦 السعة الحالية: {box_status['total']} سهم\n"
            f"🎯 المستخدم: {box_status['used']} سهم\n"
            f"💡 عند تعيين سعة أقل من المستخدم، سيتم ضبط المستخدم تلقائياً",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="manage_arrow_box")]])
        )
        context.user_data['awaiting_box_capacity'] = True
        
    except Exception as e:
        logger.error(f"خطأ في set_box_capacity_prompt: {e}")
        await update.callback_query.answer("❌ حدث خطأ في المعالجة")

@admin_only
async def handle_arrow_admin_messages(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """معالجة رسائل إدارة سهم الحظ"""
    try:
        if context.user_data.get('awaiting_daily_limit'):
            try:
                limit = int(text)
                if 1 <= limit <= 100:
                    settings = db.get_luck_arrow_settings()
                    settings['daily_spin_limit'] = limit
                    if db.update_luck_arrow_settings(settings):
                        await update.message.reply_text(f"✅ تم تعيين الحد اليومي إلى {limit} رمية")
                    else:
                        await update.message.reply_text("❌ حدث خطأ في حفظ الإعدادات")
                else:
                    await update.message.reply_text("❌ يجب أن يكون الحد بين 1 و 100")
            except ValueError:
                await update.message.reply_text("❌ يجب إدخال رقم صحيح")
            finally:
                context.user_data.pop('awaiting_daily_limit', None)
            return
            
        elif context.user_data.get('awaiting_invite_arrows'):
            try:
                arrows = int(text)
                if arrows >= 0:
                    settings = db.get_luck_arrow_settings()
                    settings['invite_arrows'] = arrows
                    if db.update_luck_arrow_settings(settings):
                        await update.message.reply_text(f"✅ تم تعيين أسهم الدعوة إلى {arrows} سهم")
                    else:
                        await update.message.reply_text("❌ حدث خطأ في حفظ الإعدادات")
                else:
                    await update.message.reply_text("❌ يجب أن يكون العدد أكبر أو يساوي 0")
            except ValueError:
                await update.message.reply_text("❌ يجب إدخال رقم صحيح")
            finally:
                context.user_data.pop('awaiting_invite_arrows', None)
            return
            
        elif context.user_data.get('awaiting_invite_points'):
            try:
                points = int(text)
                if points >= 0:
                    settings = db.get_luck_arrow_settings()
                    settings['invite_points'] = points
                    if db.update_luck_arrow_settings(settings):
                        await update.message.reply_text(f"✅ تم تعيين نقاط الدعوة إلى {points} نقطة")
                    else:
                        await update.message.reply_text("❌ حدث خطأ في حفظ الإعدادات")
                else:
                    await update.message.reply_text("❌ يجب أن يكون العدد أكبر أو يساوي 0")
            except ValueError:
                await update.message.reply_text("❌ يجب إدخال رقم صحيح")
            finally:
                context.user_data.pop('awaiting_invite_points', None)
            return
            
        elif context.user_data.get('awaiting_box_capacity'):
            try:
                capacity = int(text)
                if capacity > 0:
                    if db.set_box_capacity(capacity):
                        await update.message.reply_text(f"✅ تم تعيين سعة الصندوق إلى {capacity} سهم")
                    else:
                        await update.message.reply_text("❌ حدث خطأ في تعيين السعة")
                else:
                    await update.message.reply_text("❌ يجب أن تكون السعة أكبر من 0")
            except ValueError:
                await update.message.reply_text("❌ يجب إدخال رقم صحيح")
            finally:
                context.user_data.pop('awaiting_box_capacity', None)
            return
            
        elif context.user_data.get('awaiting_give_arrows'):
            try:
                parts = text.split()
                if len(parts) == 2:
                    user_id = parts[0].strip()
                    arrows = int(parts[1])
                    
                    if user_id.lower() == 'all':
                        success_count = db.give_arrows_to_all(arrows)
                        await update.message.reply_text(f"✅ تم منح {arrows} سهم لـ {success_count} مستخدم")
                    else:
                        if db.give_arrows_to_user(user_id, arrows):
                            await update.message.reply_text(f"✅ تم منح {arrows} سهم للمستخدم {user_id}")
                        else:
                            await update.message.reply_text("❌ خطأ في منح الأسهم. تأكد من صحة ID المستخدم")
                else:
                    await update.message.reply_text("❌ تنسيق غير صحيح. استخدم: ايدي عدد_الأسهم أو all عدد_الأسهم")
            except ValueError:
                await update.message.reply_text("❌ يجب إدخال رقم صحيح للأسهم")
            except Exception as e:
                logger.error(f"خطأ في منح الأسهم: {e}")
                await update.message.reply_text("❌ حدث خطأ غير متوقع")
            finally:
                context.user_data.pop('awaiting_give_arrows', None)
            return
            
        # معالجة إضافة الجوائز الجديدة
        elif context.user_data.get('awaiting_prize_points'):
            await handle_prize_addition(update, context, text)
            return
            
        elif context.user_data.get('awaiting_prize_arrows'):
            await handle_prize_addition(update, context, text)
            return
            
        elif context.user_data.get('awaiting_prize_gift_code'):
            await handle_prize_addition(update, context, text)
            return
            
    except Exception as e:
        logger.error(f"خطأ في handle_arrow_admin_messages: {e}")
        await update.message.reply_text("❌ حدث خطأ في المعالجة")

# Admin/LuckArrowAdmin.py - نظام إدارة سهم الحظ الكامل - الجزء 3/3
@admin_only
async def handle_prize_addition(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """معالجة إضافة الجوائز"""
    try:
        if context.user_data.get('awaiting_prize_points'):
            try:
                parts = text.split()
                if len(parts) == 2:
                    value = int(parts[0])
                    quantity = int(parts[1])
                    
                    if db.add_prize_with_quantity("points", value, quantity):
                        await update.message.reply_text(
                            f"✅ تم إضافة {quantity} جائزة نقاط بقيمة {value} نقطة لكل منها"
                        )
                    else:
                        await update.message.reply_text("❌ حدث خطأ في إضافة الجائزة")
                else:
                    await update.message.reply_text("❌ تنسيق غير صحيح. استخدم: القيمة العدد")
            except ValueError:
                await update.message.reply_text("❌ يجب إدخال أرقام صحيحة")
            finally:
                context.user_data.pop('awaiting_prize_points', None)
            return
            
        elif context.user_data.get('awaiting_prize_arrows'):
            try:
                parts = text.split()
                if len(parts) == 2:
                    value = int(parts[0])
                    quantity = int(parts[1])
                    
                    if db.add_prize_with_quantity("arrow", value, quantity):
                        await update.message.reply_text(
                            f"✅ تم إضافة {quantity} جائزة أسهم بقيمة {value} سهم لكل منها"
                        )
                    else:
                        await update.message.reply_text("❌ حدث خطأ في إضافة الجائزة")
                else:
                    await update.message.reply_text("❌ تنسيق غير صحيح. استخدم: القيمة العدد")
            except ValueError:
                await update.message.reply_text("❌ يجب إدخال أرقام صحيحة")
            finally:
                context.user_data.pop('awaiting_prize_arrows', None)
            return
            
        elif context.user_data.get('awaiting_prize_gift_code'):
            try:
                parts = text.split()
                if len(parts) == 2:
                    value = int(parts[0])
                    quantity = int(parts[1])
                    
                    # إنشاء أكواد الهدايا أولاً
                    created_codes = db.create_gift_code_prizes(value, quantity)
                    
                    if created_codes and db.add_prize_with_quantity("gift_code", value, quantity):
                        codes_message = "\n".join([f"`{code}`" for code in created_codes[:5]])
                        if len(created_codes) > 5:
                            codes_message += f"\n... و {len(created_codes) - 5} كود آخر"
                            
                        await update.message.reply_text(
                            f"✅ تم إضافة {quantity} جائزة كود هدية بقيمة {value} نقطة\n\n"
                            f"🎁 الأكواد المنشأة:\n{codes_message}",
                            parse_mode='Markdown'
                        )
                    else:
                        await update.message.reply_text("❌ حدث خطأ في إضافة الجوائز")
                else:
                    await update.message.reply_text("❌ تنسيق غير صحيح. استخدم: القيمة العدد")
            except ValueError:
                await update.message.reply_text("❌ يجب إدخال أرقام صحيحة")
            finally:
                context.user_data.pop('awaiting_prize_gift_code', None)
            return
            
    except Exception as e:
        logger.error(f"Error in handle_prize_addition: {e}")
        await update.message.reply_text("❌ حدث خطأ في المعالجة")

@admin_only
async def handle_arrow_admin_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة استدعاءات إدارة سهم الحظ"""
    query = update.callback_query
    data = query.data
    
    try:
        if data == "luck_arrow_admin":
            await luck_arrow_admin_menu(update, context)
        elif data == "manage_arrow_box":
            await manage_arrow_box(update, context)
        elif data == "arrow_settings":
            await arrow_settings_menu(update, context)
        elif data == "give_arrows":
            await give_arrows_prompt(update, context)
        elif data == "arrow_stats":
            await arrow_stats(update, context)
        elif data == "manage_prizes":
            await manage_prizes(update, context)
        elif data == "view_prizes":
            await view_prizes(update, context)
        elif data == "weekly_report":
            await weekly_report(update, context)
        elif data == "set_daily_limit":
            await set_daily_limit_prompt(update, context)
        elif data == "set_invite_arrows":
            await set_invite_arrows_prompt(update, context)
        elif data == "set_invite_points":
            await set_invite_points_prompt(update, context)
        elif data == "set_box_capacity":
            await set_box_capacity_prompt(update, context)
        elif data == "reset_box":
            if db.reset_arrow_box():
                await query.answer("✅ تم إعادة تعيين الصندوق")
            else:
                await query.answer("❌ حدث خطأ في الإعادة")
            await manage_arrow_box(update, context)
        elif data == "toggle_box":
            if db.toggle_box_status():
                box_status = db.get_box_status()
                status = "مفتوح" if box_status['is_open'] else "مغلق"
                await query.answer(f"✅ تم {status} الصندوق")
            else:
                await query.answer("❌ حدث خطأ في تغيير الحالة")
            await manage_arrow_box(update, context)

        elif data == "reset_prizes":
            # إعادة تعيين الجوائز إلى 0 والاسهم إلى 0
            try:
                settings = db.get_luck_arrow_settings()
        
                # جعل الجوائز فارغة
                settings['prizes'] = []
        
                # جعل الصندوق فارغ (0 سهم)
                settings['total_arrows'] = 0
                settings['used_arrows'] = 0
                settings['box_open'] = True  # الصندوق مفتوح لكن فارغ
        
                if db.update_luck_arrow_settings(settings):
                    await query.answer("✅ تم إعادة التعيين بنجاح\n\n• الجوائز: 0\n• الأسهم المتاحة: 0", show_alert=True)
                    # إعادة تحميل القائمة
                    await manage_prizes(update, context)
                else:
                    await query.answer("❌ حدث خطأ في إعادة التعيين", show_alert=True)
            
            except Exception as e:
                logger.error(f"خطأ في reset_prizes: {e}")
                await query.answer("❌ حدث خطأ في الإعادة", show_alert=True)
            await manage_prizes(update, context)
        elif data == "add_prize":
            await add_prize_menu(update, context)
        elif data == "add_prize_points":
            await add_prize_points_prompt(update, context)
        elif data == "add_prize_arrows":
            await add_prize_arrows_prompt(update, context)
        elif data == "add_prize_gift_code":
            await add_prize_gift_code_prompt(update, context)
        elif data == "edit_prizes":
            await query.answer("⏳ هذه الميزة قيد التطوير", show_alert=True)
            await manage_prizes(update, context)
        else:
            await query.answer("❌ الأمر غير معروف")
            
    except Exception as e:
        logger.error(f"خطأ في handle_arrow_admin_callbacks: {e}")
        await query.answer("❌ حدث خطأ في المعالجة")

# دوال مساعدة لدمج النظام الجديد
def add_prize_with_quantity(prize_type, value, quantity, probability=None):
    """إضافة جائزة بكمية محددة - دالة مساعدة"""
    return db.add_prize_with_quantity(prize_type, value, quantity, probability)

def create_gift_code_prizes(points_value, count):
    """إنشاء أكواد هدايا للجوائز - دالة مساعدة"""
    return db.create_gift_code_prizes(points_value, count)

def get_arrow_prize_distribution():
    """الحصول على توزيع الجوائز - دالة مساعدة"""
    return db.get_arrow_prize_distribution()

def update_prize_distribution(new_prizes):
    """تحديث توزيع الجوائز - دالة مساعدة"""
    return db.update_prize_distribution(new_prizes)
