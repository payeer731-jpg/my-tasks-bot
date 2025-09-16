# Member/Invite.py - محدث بنظام الأسهم
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from Data import db
from Config import BOT_USERNAME, OWNER_ID
from Decorators import user_only
import logging
import requests
from datetime import datetime


logger = logging.getLogger(__name__)

@user_only
async def invite_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if data == "member_invite_link":
        await invite_link(update, context)
    elif data == "member_invite_points":
        await my_points(update, context)
    elif data == "member_invite_stats":
        await invite_stats(update, context)

@user_only
async def invite_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض رابط الدعوة الخاص بالمستخدم مع مكافآت الأسهم"""
    try:
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name
        
        # التحقق من إذا كان نظام الدعوة مفعلاً
        if not db.is_invite_system_enabled():
            await update.callback_query.answer(
                "❌ نظام الدعوة معطل حالياً من قبل الإدارة", 
                show_alert=True
            )
            return
        
        invite_points = db.get_invite_points()
        luck_settings = db.get_luck_arrow_settings()
        invite_bonus_points = luck_settings.get("invite_points", 1)
        invite_arrows = luck_settings.get("invite_arrows", 1)
        
        total_points = invite_points + invite_bonus_points
        
        invite_link, error = db.get_invite_link(user_id, BOT_USERNAME)
        
        if error:
            await update.callback_query.answer(error, show_alert=True)
            return
        
        # الحصول على إحصائيات الدعوة
        user_data = db.get_user(user_id)
        invited_count = len(user_data.get('invited_users', []))
        earned_points = invited_count * total_points
        earned_arrows = invited_count * invite_arrows
        
        message = f"""
📨 **رابط الدعوة الخاص بـ {user_name}:**

`{invite_link}`

🎯 **مكافآت الدعوة:**
• لكل صديق تدعوه: {total_points} نقطة 🎁
• بالإضافة إلى: {invite_arrows} سهم 🏹

📊 **إحصائياتك:**
• عدد المدعوين: {invited_count} شخص
• النقاط المكتسبة: {earned_points} نقطة
• الأسهم المكتسبة: {earned_arrows} سهم
• الحد الأقصى اليومي: لا يوجد حد 🎉

🎰 **استخدم الأسهم في لعبة سهم الحظ لكسب جوائز أكثر!**
        """
        
        keyboard = [
            [InlineKeyboardButton("📤 مشاركة الرابط", 
                url=f"https://t.me/share/url?url={invite_link}&text=انضم%20إلى%20بوت%20المهام%20الحصري%20واكسب%20النقاط%20والأسهم!%20{invite_link}")],
            [
                InlineKeyboardButton("💰 نقاطي", callback_data="member_invite_points"),
                InlineKeyboardButton("📊 إحصائياتي", callback_data="member_invite_stats")
            ],
            [InlineKeyboardButton("🎯 سهم الحظ", callback_data="luck_arrow_menu")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="member_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            message, 
            reply_markup=reply_markup, 
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"خطأ في invite_link: {e}")
        await update.callback_query.answer("❌ حدث خطأ في عرض رابط الدعوة")

@user_only
async def my_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض نقاط المستخدم وإحصائيات الدعوة مع الأسهم"""
    try:
        user_id = update.effective_user.id
        user_data = db.get_user(user_id)
        points = user_data["points"]
        
        # الحصول على معلومات الأسهم
        arrow_info = db.get_user_arrow_info(user_id)
        total_arrows = arrow_info["total_arrows"]
        
        invite_points = db.get_invite_points()
        luck_settings = db.get_luck_arrow_settings()
        invite_bonus_points = luck_settings.get("invite_points", 1)
        invite_arrows = luck_settings.get("invite_arrows", 1)
        
        total_reward_points = invite_points + invite_bonus_points
        
        invite_enabled = db.is_invite_system_enabled()
        status = "✅ مفعل" if invite_enabled else "❌ معطل"
        
        # إحصائيات الدعوة
        invited_users = user_data.get('invited_users', [])
        invited_count = len(invited_users)
        earned_from_invites = invited_count * total_reward_points
        earned_arrows = invited_count * invite_arrows
        
        daily_invites = user_data.get('daily_invites', {})
        today = datetime.now().strftime("%Y-%m-%d")
        today_invites = daily_invites.get(today, 0)
        
        message = f"""
💰 **نقاطك: {points} نقطة**
🏹 **أسهمك: {total_arrows} سهم**

📊 **معلومات الدعوة:**
• حالة النظام: {status}
• قيمة الدعوة: {total_reward_points} نقطة + {invite_arrows} سهم
• عدد المدعوين: {invited_count} شخص
• النقاط من الدعوة: {earned_from_invites} نقطة
• الأسهم من الدعوة: {earned_arrows} سهم
• الدعوات اليوم: {today_invites} دعوة

🎯 **المزيد من الدعوات = المزيد من النقاط والأسهم!**
        """
        
        keyboard = [
            [InlineKeyboardButton("📨 رابط الدعوة", callback_data="member_invite_link")],
            [InlineKeyboardButton("📊 إحصائياتي", callback_data="member_invite_stats")],
            [InlineKeyboardButton("🎯 سهم الحظ", callback_data="luck_arrow_menu")],
            [InlineKeyboardButton("📋 المهام", callback_data="member_tasks_view")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="member_menu")]
        ]
        
        # إذا كان نظام الدعوة معطلاً، نخفي زر رابط الدعوة
        if not invite_enabled:
            keyboard[0].pop(0)  # إزالة زر رابط الدعوة
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            message, 
            reply_markup=reply_markup, 
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"خطأ في my_points: {e}")
        await update.callback_query.answer("❌ حدث خطأ في عرض النقاط")

@user_only
async def invite_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض إحصائيات الدعوة المفصلة مع الأسهم"""
    try:
        user_id = update.effective_user.id
        user_data = db.get_user(user_id)
        
        invite_points = db.get_invite_points()
        luck_settings = db.get_luck_arrow_settings()
        invite_bonus_points = luck_settings.get("invite_points", 1)
        invite_arrows = luck_settings.get("invite_arrows", 1)
        
        total_reward_points = invite_points + invite_bonus_points
        
        invited_users = user_data.get('invited_users', [])
        invited_count = len(invited_users)
        earned_points = invited_count * total_reward_points
        earned_arrows = invited_count * invite_arrows
        
        # الحصول على إحصائيات يومية
        daily_invites = user_data.get('daily_invites', {})
        today = datetime.now().strftime("%Y-%m-%d")
        today_count = daily_invites.get(today, 0)
        
        # ترتيب الأيام من الأحدث
        sorted_days = sorted(daily_invites.keys(), reverse=True)[:7]  # آخر 7 أيام
        
        message = f"""
📊 **إحصائيات الدعوة المفصلة**

• إجمالي المدعوين: {invited_count} شخص
• النقاط من الدعوة: {earned_points} نقطة
• الأسهم من الدعوة: {earned_arrows} سهم
• الدعوات اليوم: {today_count} دعوة

🎯 **مكافأة لكل دعوة:**
• {total_reward_points} نقطة 💰
• {invite_arrows} سهم 🏹

📅 **آخر 7 أيام:**
"""
        
        for day in sorted_days:
            count = daily_invites[day]
            message += f"• {day}: {count} دعوة\n"
        
        if not sorted_days:
            message += "📭 لا توجد دعوات سابقة\n"
        
        message += f"\n🚀 استمر في الدعوة لكسب المزيد!"
        
        keyboard = [
            [InlineKeyboardButton("📨 رابط الدعوة", callback_data="member_invite_link")],
            [InlineKeyboardButton("💰 نقاطي", callback_data="member_invite_points")],
            [InlineKeyboardButton("🎯 سهم الحظ", callback_data="luck_arrow_menu")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="member_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            message, 
            reply_markup=reply_markup, 
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"خطأ في invite_stats: {e}")
        await update.callback_query.answer("❌ حدث خطأ في عرض الإحصائيات")

# في Invite.py - تعديل دالة send_invite_notification
async def send_invite_notification(context, referrer_id, invited_id, invited_name):
    """إرسال إشعار الدعوة للمدعي مع الأسهم"""
    try:
        invite_points = db.get_invite_points()
        luck_settings = db.get_luck_arrow_settings()
        invite_bonus_points = luck_settings.get("invite_points", 1)
        invite_arrows = luck_settings.get("invite_arrows", 1)
        
        total_points = invite_points + invite_bonus_points
        
        message = f"""
🎯 **إشعار دعوة جديدة!**

👤 قام {invited_name} بدخول البوت عبر رابط دعوتك
💰 حصلت على {total_points} نقطة
🏹 حصلت على {invite_arrows} سهم حظ

📊 يمكنك متابعة إحصائياتك من خلال:
• /invite - لعرض رابط الدعوة
• /points - لعرض نقاطك وأسهمك
• 🎯 سهم الحظ - لاستخدام الأسهم
"""
        
        await context.bot.send_message(
            chat_id=referrer_id,
            text=message,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"خطأ في send_invite_notification: {e}")

async def send_welcome_to_invited(context, invited_id, referrer_name):
    """إرسال رسالة ترحيب للمدعو"""
    try:
        message = f"""
🎉 **مرحباً بك!**

شكراً لدخولك عبر دعوة من {referrer_name}
✅ يمكنك الآن البدء في كسب النقاط عبر:

• 📋 تنفيذ المهام المتاحة
• ➕ إنشاء مهام جديدة  
• 📨 دعوة الأصدقاء
• 🎯 لعب سهم الحظ

🚀 ابدأ رحلتك الآن وكُن الأكثر نقاطاً!
"""
        
        await context.bot.send_message(
            chat_id=invited_id,
            text=message,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"خطأ في send_welcome_to_invited: {e}")

# دالة مساعدة للتحقق من صحة الدعوة
def is_valid_invite(referrer_id, invited_id):
    """التحقق من صحة الدعوة"""
    if referrer_id == invited_id:
        return False, "لا يمكن دعوة نفسك"
    
    if not db.is_invite_system_enabled():
        return False, "نظام الدعوة معطل حالياً"
    
    return True, ""


