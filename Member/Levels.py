# Member/Levels.py - الإصدار المدمج
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from Data import db
from Decorators import user_only
import logging

logger = logging.getLogger(__name__)

@user_only
async def show_levels_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض معلومات المستويات والرتب - الإصدار المصحح"""
    try:
        user_id = update.effective_user.id
        user_data = db.get_user(user_id)
        points = user_data.get("points", 0)
        
        # معلومات المستوى الحالي
        current_level = db.get_user_level(user_id)
        level_info = db.get_level_info(current_level)
        
        # معلومات المستوى التالي
        next_level_info = db.get_next_level_info(user_id)
        
        # إحصائيات المستخدم
        user_stats = db.data.get("user_stats", {}).get(str(user_id), {})
        
        message = f"""
🏆 **نظام المستويات والرتب**

📊 **مستواك الحالي:** {level_info.get('name', 'مبتدئ 🌱')}
💰 **نقاطك:** {points} نقطة
⭐ **المستوى:** {current_level}

🎯 **مميزات مستواك:**
"""
        
        # إضافة مميزات المستوى الحالي
        benefits = level_info.get('benefits', [])
        if benefits:
            for benefit in benefits:
                message += f"• ✅ {benefit}\n"
        else:
            message += "• 📝 لا توجد مميزات خاصة\n"
        
        # معلومات المستوى التالي
        if next_level_info:
            # الحصول على أقل مستوى أعلى من المستوى الحالي
            all_levels = sorted([int(level) for level in db.data.get("level_system", {}).get("levels", {}).keys()])
            next_level_points = next((level for level in all_levels if level > current_level), None)
            
            if next_level_points:
                points_needed = next_level_points - points
                
                message += f"""
📈 **المستوى التالي:** {next_level_info.get('name', '')}
🎯 **النقاط المطلوبة:** {points_needed} نقطة
✨ **مميزات قادمة:**
"""
                next_benefits = next_level_info.get('benefits', [])
                for benefit in next_benefits:
                    message += f"• 🔜 {benefit}\n"
        
        # الإحصائيات المتقدمة
        message += f"""
📊 **إحصائياتك المتقدمة:**
• 🎯 المهام المكتملة: {user_stats.get('completed_tasks', 0)}
• 💰 إجمالي الأرباح: {user_stats.get('total_earned', 0)} نقطة
• ⭐ ترقيات المستوى: {user_stats.get('level_ups', 0)}
• 📨 طلبات ناجحة: {user_stats.get('earning_transactions', 0)}
"""
        
        keyboard = [
            [InlineKeyboardButton("📋 المهام المتاحة", callback_data="member_tasks_view")],
            [InlineKeyboardButton("💰 نقاطي", callback_data="member_invite_points")],
            [InlineKeyboardButton("🔄 تحديث المعلومات", callback_data="member_level_info")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="member_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(
                message, 
                reply_markup=reply_markup, 
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
        else:
            await update.message.reply_text(
                message, 
                reply_markup=reply_markup, 
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            
    except Exception as e:
        logger.error(f"خطأ في عرض معلومات المستويات: {e}")
        error_msg = "❌ حدث خطأ في تحميل معلومات المستوى. يرجى المحاولة مرة أخرى."
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.answer(error_msg)
        else:
            await update.message.reply_text(error_msg)

async def apply_level_benefits(user_id, context=None):
    """تطبيق مزايا المستوى على المستخدم - الإصدار المصحح"""
    try:
        user_level = db.get_user_level(user_id)
        level_info = db.get_level_info(user_level)
        level_name = level_info.get('name', 'مبتدئ 🌱')
        benefits = level_info.get('benefits', [])
        
        benefits_applied = []
        
        # تطبيق المزايا حسب المستوى
        if "خصم 5% على المهام" in benefits:
            benefits_applied.append("💰 خصم 5% على جميع المهام")
        
        if "خصم 10% على المهام" in benefits:
            benefits_applied.append("💎 خصم 10% على جميع المهام")
        
        if "خصم 15% على المهام" in benefits:
            benefits_applied.append("🔥 خصم 15% على جميع المهام")
        
        if "خصم 20% على المهام" in benefits:
            benefits_applied.append("🚀 خصم 20% على جميع المهام")
        
        if "أولوية في الدعم" in benefits:
            benefits_applied.append("⚡ أولوية في الدعم الفني")
        
        if "مهام حصرية" in benefits:
            benefits_applied.append("🎯 مهام حصرية")
        
        if "دعم متميز" in benefits:
            benefits_applied.append("🌟 دعم متميز")
        
        if "ميزانية تثبيت مجانية" in benefits:
            benefits_applied.append("📌 تثبيت مجاني للمهام")
        
        if "مدير فخري" in benefits:
            benefits_applied.append("👑 مدير فخري")
        
        # إرسال إشعار المزايا إذا كان متاحاً
        if context and benefits_applied:
            benefits_text = "\n".join([f"• {benefit}" for benefit in benefits_applied])
            
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"""
🎉 **مزايا مستواك الجديدة!**

🏆 المستوى: {level_name}

✨ **المزايا المفعلة:**
{benefits_text}

🚀 استمتع بمزاياك الجديدة!
""",
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"⚠️ خطأ في إرسال إشعار المزايا: {e}")
        
        return benefits_applied
        
    except Exception as e:
        logger.error(f"❌ خطأ في apply_level_benefits: {e}")
        return []

@user_only
async def show_level_benefits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض مزايا المستوى الحالي للمستخدم"""
    try:
        user_id = update.effective_user.id
        user_level = db.get_user_level(user_id)
        level_info = db.get_level_info(user_level)
        next_level_info = db.get_next_level_info(user_id)
        
        # تطبيق المزايا الحالية
        current_benefits = await apply_level_benefits(user_id)
        
        message = f"""
🏆 **مزايا مستواك الحالي**

📊 المستوى: {level_info.get('name', 'مبتدئ 🌱')}
⭐ نقاط المستوى: {user_level}

✨ **المزايا المفعلة:**
"""
        
        if current_benefits:
            for benefit in current_benefits:
                message += f"• ✅ {benefit}\n"
        else:
            message += "• 📝 لا توجد مزايا خاصة\n"
        
        # معلومات المستوى التالي
        if next_level_info:
            next_level_points = min([p for p in db.data.get("level_system", {}).get("levels", {}).keys() 
                                   if p > user_level])
            points_needed = next_level_points - db.get_user_points(user_id)
            
            message += f"""
📈 **المستوى التالي:** {next_level_info.get('name', '')}
🎯 **النقاط المطلوبة:** {points_needed} نقطة
✨ **مميزات قادمة:**
"""
            next_benefits = next_level_info.get('benefits', [])
            for benefit in next_benefits:
                message += f"• 🔜 {benefit}\n"
        
        keyboard = [
            [InlineKeyboardButton("🔄 تحديث المزايا", callback_data="refresh_benefits")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="member_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(update, 'callback_query'):
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"خطأ في show_level_benefits: {e}")
        await update.callback_query.answer("❌ حدث خطأ في عرض المزايا")

async def refresh_levels_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تحديث معلومات المستويات"""
    await show_levels_info(update, context)

# دالة مساعدة للحصول على الخصم
def get_user_discount(user_id):
    """الحصول على نسبة الخصم حسب مستوى المستخدم"""
    try:
        level_name = db.get_user_level_name(user_id)
        
        # خريطة الخصومات حسب المستوى
        discount_map = {
            "مبتدئ 🌱": 0,
            "نشط ⭐": 5,
            "محترف 🏆": 10, 
            "خبير 👑": 15,
            "أسطورة 🚀": 20
        }
        
        return discount_map.get(level_name, 0)
    except Exception as e:
        logger.error(f"خطأ في get_user_discount: {e}")
        return 0