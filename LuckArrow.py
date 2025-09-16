# LuckArrow.py - نظام سهم الحظ
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from Data import db
from Decorators import user_only, admin_only
import logging
import random
import asyncio
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class LuckArrowSystem:
    def __init__(self):
        self.animations = ["🎯", "🏹", "🎪", "🎡", "🎢", "🎰", "🎳", "⚽", "🏀", "🏈"]
    
    async def spin_animation(self, update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int):
        """عرض رسوم متحركة للرمية"""
        for i in range(8):
            animation = random.choice(self.animations)
            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=f"{animation} جاري رمي السهم... {animation}"
                )
                await asyncio.sleep(0.3)
            except:
                break
    
    def get_user_arrows(self, user_id):
        """الحصول على عدد أسهم المستخدم"""
        user_id = str(user_id)
        if "luck_arrows" not in db.data:
            db.data["luck_arrows"] = {}
        
        if user_id not in db.data["luck_arrows"]:
            db.data["luck_arrows"][user_id] = {
                "total_arrows": 0,
                "used_today": 0,
                "last_used": None,
                "history": []
            }
        
        return db.data["luck_arrows"][user_id]
    
    def add_arrows_to_user(self, user_id, arrows_count):
        """إضافة أسهم للمستخدم"""
        user_data = self.get_user_arrows(user_id)
        user_data["total_arrows"] += arrows_count
        db.save_data()
        return True

    def can_user_spin(self, user_id):
        """التحقق إذا كان يمكن للمستخدم الرمي - إصدار فارغ"""
        try:
            user_id = str(user_id)
            user_data = self.get_user_arrows(user_id)
        
            # التحقق من حالة الصندوق
            box_status = self.get_box_status()
            if not box_status["is_open"]:
                return False
        
            # التحقق من الأسهم
            if user_data["total_arrows"] <= 0:
                return False
        
            # التحقق من الحد اليومي
            daily_limit = db.data.get('luck_arrow_settings', {}).get('daily_spin_limit', 10)
        
            # إعادة تعيين العد اليومي إذا كان تاريخ جديد
            today = datetime.now().strftime("%Y-%m-%d")
            if user_data.get("last_used") != today:
                user_data["used_today"] = 0
                user_data["last_used"] = today
                db.save_data()
        
            return user_data["used_today"] < daily_limit
        
        except Exception as e:
            logger.error(f"Error checking spin ability: {e}")
            return False
    
    def use_arrow(self, user_id):
        """استخدام سهم"""
        user_data = self.get_user_arrows(user_id)
        user_data["total_arrows"] -= 1
        user_data["used_today"] += 1
        user_data["last_used"] = datetime.now().strftime("%Y-%m-%d")
        db.save_data()
        return True

    def get_prize(self):
        """الحصول على جائزة عشوائية - إصدار فارغ"""
        try:
            settings = db.get_luck_arrow_settings()
            prizes = settings.get("prizes", [])
        
            # إذا لم توجد جوائز مضافة، إرجاع لا شيء
            if not prizes:
                return {"type": "nothing", "value": 0, "probability": 100}
        
            # استخدام الدالة الجديدة التي تدعم الكمية
            prize = db.get_available_prize()
        
            # إذا كانت الجائزة من نوع كود هدية، إنشاء كود فعلي
            if prize["type"] == "gift_code":
                # إنشاء كود هدية حقيقي
                code_data = {
                    'code': db.generate_gift_code(),
                    'points': prize["value"],
                    'max_uses': 1,
                    'used_count': 0,
                    'used_by': [],
                    'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'created_by': 'system'
                }
            
                if db.add_gift_code(code_data):
                    prize["gift_code"] = code_data['code']
                else:
                    # إذا فشل إنشاء الكود، إرجاع نقاط بديلة
                    prize = {"type": "points", "value": prize["value"], "probability": 100}
        
            return prize
        
        except Exception as e:
            logger.error(f"Error in get_prize: {e}")
            # جائزة افتراضية في حالة الخطأ
            return {"type": "nothing", "value": 0, "probability": 100}
    
    def add_to_history(self, user_id, prize):
        """إضافة الرمية إلى السجل"""
        user_data = self.get_user_arrows(user_id)
        history_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "prize": prize,
            "won": prize["value"] > 0 if prize["type"] != "nothing" else False
        }
        
        user_data["history"].append(history_entry)
        if len(user_data["history"]) > 10:
            user_data["history"] = user_data["history"][-10:]
        
        db.save_data()
        return history_entry
    
    def get_user_history(self, user_id):
        """الحصول على سجل رميات المستخدم"""
        user_data = self.get_user_arrows(user_id)
        return user_data.get("history", [])
    
    def get_box_status(self):
        """الحصول على حالة الصندوق"""
        settings = db.data.get("luck_arrow_settings", {})
        total_arrows = settings.get("total_arrows", 10000)
        used_arrows = settings.get("used_arrows", 0)
        
        return {
            "total": total_arrows,
            "used": used_arrows,
            "remaining": total_arrows - used_arrows,
            "is_open": (total_arrows - used_arrows) > 0
        }
    
    def update_box_usage(self):
        """تحديث استخدام الصندوق"""
        settings = db.data.get("luck_arrow_settings", {})
        settings["used_arrows"] = settings.get("used_arrows", 0) + 1
        db.save_data()
        
        # التحقق إذا انتهى الصندوق
        box_status = self.get_box_status()
        if not box_status["is_open"]:
            settings["box_open"] = False
            db.save_data()
        
        return box_status["is_open"]

luck_arrow_system = LuckArrowSystem()

@user_only
async def luck_arrow_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """قائمة سهم الحظ"""
    try:
        user_id = update.effective_user.id
        user_data = luck_arrow_system.get_user_arrows(user_id)
        box_status = luck_arrow_system.get_box_status()
        
        message = f"""
🎯 **سهم الحظ**

🏹 **أسهمك:** {user_data['total_arrows']} سهم
🎪 **الرميات اليوم:** {user_data['used_today']}/{db.data.get('luck_arrow_settings', {}).get('daily_spin_limit', 10)}
📦 **حالة الصندوق:** {box_status['remaining']}/{box_status['total']} سهم متبقي

🎰 **اختر الإجراء:**
"""
        
        keyboard = [
            [InlineKeyboardButton("🎯 رمي السهم", callback_data="spin_arrow")],
            [InlineKeyboardButton("📋 سجل الرميات", callback_data="arrow_history")],
            [InlineKeyboardButton("📊 معلومات الصندوق", callback_data="box_info")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="member_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(update, 'callback_query'):
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"خطأ في luck_arrow_menu: {e}")
        await update.callback_query.answer("❌ حدث خطأ في تحميل القائمة")

@user_only
async def spin_arrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رمي السهم مع ملصق متحرك"""
    try:
        query = update.callback_query
        user_id = update.effective_user.id
        user_data = luck_arrow_system.get_user_arrows(user_id)
        settings = db.get_luck_arrow_settings()
        daily_limit = settings.get('daily_spin_limit', 10)
        box_status = luck_arrow_system.get_box_status()
        
        # التحقق من إمكانية الرمي
        if user_data["used_today"] >= daily_limit:
            await query.answer(f"❌ وصلت للحد الأقصى اليومي ({daily_limit} رمية)", show_alert=True)
            return
            
        if user_data["total_arrows"] <= 0:
            await query.answer("❌ ليس لديك أسهم للرمي", show_alert=True)
            return
            
        if not box_status["is_open"] or box_status["remaining"] <= 0:
            await query.answer("📦 الصندوق مغلق حالياً", show_alert=True)
            return
        
        # استخدام سهم
        luck_arrow_system.use_arrow(user_id)
        luck_arrow_system.update_box_usage()
        
        # إرسال رسالة الانتظار أولاً
        wait_message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="🎯 *جاري رمي السهم...*",
            parse_mode='Markdown'
        )
        
        # محاولة إرسال ملصق (إذا كان هناك ملصق متاح)
        try:
            # استخدام ملصق سهم افتراضي إذا لم يتوفر الملصق المطلوب
            sticker_id = "CAACAgIAAxkBAAIBOWgAAbQAAXW0t9K5AAE1W2F4AAH_1oAAAk1AAAKu5-lLAAH2pN8eAAJmNTAE"  # مثال لملصق سهم
            await context.bot.send_sticker(
                chat_id=update.effective_chat.id,
                sticker=sticker_id
            )
        except:
            # إذا فشل إرسال الملصق، نستخدم إيموجي بديل
            animation_emojis = ["🏹", "🎯", "🚀", "⚡", "💫"]
            for emoji in animation_emojis:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=wait_message.message_id,
                    text=f"{emoji} *جاري رمي السهم...* {emoji}",
                    parse_mode='Markdown'
                )
                await asyncio.sleep(0.5)
        
        # الحصول على الجائزة
        prize = luck_arrow_system.get_prize()
        will_win = prize["value"] > 0 if prize["type"] != "nothing" else False
        
        # حفظ الجائزة
        luck_arrow_system.add_to_history(user_id, prize)
        prize_message = await handle_prize(user_id, prize, context)
        
        # حذف رسالة الانتظار
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=wait_message.message_id
            )
        except:
            pass
        
        # الإيموجي النهائي بناءً على النتيجة
        result_emoji = "🎉" if will_win else "💔"
        
        # النتيجة
        result_message = f"""
{result_emoji} *نتيجة الرمية* {result_emoji}

{prize_message}

🏹 *الأسهم المتبقية:* {luck_arrow_system.get_user_arrows(user_id)['total_arrows']}
🎪 *الرميات اليوم:* {user_data['used_today']}/{daily_limit}

💫 *حظاً أوفر في المرة القادمة!*
"""
        
        # الأزرار
        keyboard = [
            [InlineKeyboardButton("🎯 رمي مرة أخرى", callback_data="spin_arrow")],
            [InlineKeyboardButton("📋 سجل الرميات", callback_data="arrow_history")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="luck_arrow_menu")]
        ]
        
        # إرسال رسالة النتيجة
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=result_message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
        await query.answer("✅ تمت الرمية")
        
    except Exception as e:
        logger.error(f"خطأ في spin_arrow: {e}")
        await query.answer("❌ حدث خطأ في الرمية")

async def handle_prize(user_id, prize, context):
    """معالجة الجائزة"""
    try:
        prize_type = prize["type"]
        prize_value = prize["value"]
        
        if prize_type == "points":
            db.add_points_to_user(user_id, prize_value)
            return f"🎊 مبروك! فزت بـ {prize_value} نقطة!"
        
        elif prize_type == "gift_code":
            # إنشاء كود هدية
            code_data = {
                'code': db.generate_gift_code(),
                'points': prize_value,
                'max_uses': 1,
                'used_count': 0,
                'used_by': [],
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'created_by': 'system'
            }
            
            if db.add_gift_code(code_data):
                return f"🎁 مبروك! فزت بكود هدية: `{code_data['code']}`\n\n💰 القيمة: {prize_value} نقطة"
            else:
                return "❌ حدث خطأ في إنشاء كود الهدية"
        
        elif prize_type == "arrow":
            luck_arrow_system.add_arrows_to_user(user_id, prize_value)
            return f"🏹 مبروك! فزت بـ {prize_value} سهم إضافي!"
        
        elif prize_type == "nothing":
            return "😢 للأسف لم تفز بشيء هذه المرة. حاول مرة أخرى!"
        
        else:
            return "🎯 جرب حظك في المرة القادمة!"
            
    except Exception as e:
        logger.error(f"خطأ في handle_prize: {e}")
        return "❌ حدث خطأ في معالجة الجائزة"

@user_only
async def arrow_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض سجل الرميات"""
    try:
        user_id = update.effective_user.id
        history = luck_arrow_system.get_user_history(user_id)
        
        if not history:
            message = "📋 **سجل الرميات**\n\n📭 لم تقم بأي رميات بعد"
        else:
            message = "📋 **سجل الرميات**\n\n"
            for i, entry in enumerate(reversed(history), 1):
                prize_text = get_prize_text(entry["prize"])
                status = "✅" if entry["won"] else "❌"
                message += f"{i}. {status} {entry['timestamp']} - {prize_text}\n"
        
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="luck_arrow_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"خطأ في arrow_history: {e}")
        await update.callback_query.answer("❌ حدث خطأ في عرض السجل")

def get_prize_text(prize):
    """الحصول على نص الجائزة"""
    if prize["type"] == "points":
        return f"{prize['value']} نقطة"
    elif prize["type"] == "gift_code":
        return f"كود هدية {prize['value']} نقطة"
    elif prize["type"] == "arrow":
        return f"{prize['value']} سهم"
    elif prize["type"] == "nothing":
        return "لا شيء"
    return "جائزة"

@user_only
async def box_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معلومات الصندوق - إصدار فارغ"""
    try:
        box_status = db.get_box_status()
        settings = db.data.get("luck_arrow_settings", {})
        
        message = f"""
📦 **معلومات صندوق الأسهم**

🔢 **السعة:** {box_status['total']} سهم (صندوق فارغ)
🎯 **المستخدم:** {box_status['used']} سهم
🏹 **المتبقي:** {box_status['remaining']} سهم
🚪 **الحالة:** {'مفتوح' if box_status['is_open'] else 'مغلق'}

🎰 **الجوائز المتاحة:** {len(settings.get('prizes', []))} نوع

⚙️ **الإعدادات:**
• الحد اليومي: {settings.get('daily_spin_limit', 10)} رمية
• الأسهم في الدعوة: {settings.get('invite_arrows', 1)} سهم
• النقاط في الدعوة: {settings.get('invite_points', 1)} نقطة

💡 **ملاحظة:** الجوائز تُضاف يدوياً من قبل الإدارة
"""
        
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="luck_arrow_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"خطأ في box_info: {e}")
        await update.callback_query.answer("❌ حدث خطأ في عرض المعلومات")

# معالجات Callback Query
async def luck_arrow_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if data == "luck_arrow_menu":
        await luck_arrow_menu(update, context)
    elif data == "spin_arrow":
        await spin_arrow(update, context)
    elif data == "arrow_history":
        await arrow_history(update, context)
    elif data == "box_info":
        await box_info(update, context)