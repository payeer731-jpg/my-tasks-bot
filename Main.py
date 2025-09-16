# Main.py - الجزء 1/7 - الاستيرادات والإعدادات الأساسية
import logging
import asyncio
import sys
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# إصلاح مسارات الاستيراد - إضافة المسار الحالي
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# استيراد الوحدات مع معالجة الأخطاء
try:
    from Data import db
    from Config import BOT_TOKEN, OWNER_ID
    from Decorators import check_blocked_middleware
    logger = logging.getLogger(__name__)
except ImportError as e:
    print(f"❌ خطأ في استيراد الوحدات: {e}")
    print("✅ تأكد من وجود الملفات: Data.py, Config.py, Decorators.py")
    sys.exit(1)

from datetime import datetime

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

application = None

async def handle_slash_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة عندما يكتب المستخدم / فقط - يكمل /start تلقائياً"""
    try:
        if update.message.text.strip() == '/':
            logger.info(f"المستخدم {update.effective_user.id} كتب / فقط")
            
            # إرسال رسالة ترحيبية بدلاً من /start
            try:
                # استيراد ديناميكي لتجنب أخطاء الاستيراد
                sys.path.insert(0, os.path.join(current_dir, 'Member'))
                from Member.Menu import send_welcome_message
                await send_welcome_message(update, context)
                return True
            except Exception as e:
                logger.error(f"خطأ في send_welcome_message: {e}")
                # إذا فشل، نستخدم start العادي
                await start(update, context)
                return True
                
    except Exception as e:
        logger.error(f"خطأ في handle_slash_command: {e}")
    
    return False

# Main.py - الجزء 2/7 - دوال البداية ومعالجة الدعوات
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دالة البداية الرئيسية"""
    # التحقق من الحظر أولاً
    if not await check_blocked_middleware(update, context):
        return
    
    user_id = update.effective_user.id
    logger.info(f"🚀 بدء جلسة للمستخدم: {user_id}")
    
    # ✅ حفظ رابط الدعوة إذا كان موجوداً
    if context.args and hasattr(db, 'is_invite_system_enabled') and db.is_invite_system_enabled():
        referral_id = context.args[0]
        if referral_id.isdigit() and referral_id != str(user_id):
            # حفظ الدعوة مؤقتاً في قاعدة البيانات
            if "pending_invites" not in db.data:
                db.data["pending_invites"] = {}
            
            db.data["pending_invites"][str(user_id)] = {
                "referral_id": referral_id,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "processed": False
            }
            db.save_data()
            logger.info(f"💾 حفظ دعوة معلقة: {referral_id} → {user_id}")
    
    # ✅ التحقق من الاشتراك في القنوات أولاً
    try:
        sys.path.insert(0, os.path.join(current_dir, 'Admin'))
        from Admin.Channel import check_user_subscription
        missing_channels = await check_user_subscription(user_id, context)
        
        if missing_channels:
            logger.info(f"📢 المستخدم {user_id} يحتاج الاشتراك في القنوات")
            from Admin.Channel import send_subscription_required_message
            await send_subscription_required_message(update, context, missing_channels)
            return
    except Exception as e:
        logger.error(f"❌ خطأ في التحقق من الاشتراك: {e}")
    
    # ✅ التحقق من الشروط للمستخدمين الجدد
    try:
        sys.path.insert(0, os.path.join(current_dir, 'Member'))
        from Member.Terms import show_terms
        terms_accepted = await show_terms(update, context)
        
        if not terms_accepted:
            logger.info(f"📝 عرض الشروط للمستخدم: {user_id}")
            return  # انتظار رد المستخدم على الشروط
    except Exception as e:
        logger.error(f"❌ خطأ في عرض الشروط: {e}")
    
    # ✅ عرض القوائم (للمستخدمين أو الأدمن)
    if str(user_id) in db.get_admins() or user_id == OWNER_ID:
        try:
            from Admin.Menu import show_admin_menu
            await show_admin_menu(update, context)
            
            try:
                from Member.Menu import show_member_menu
                await asyncio.sleep(1)
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="👤 **واجهة المستخدم:**",
                    parse_mode='Markdown'
                )
                await show_member_menu(update, context)
            except Exception as e:
                logger.error(f"❌ خطأ في عرض واجهة المستخدم للأدمن: {e}")
                
        except Exception as e:
            logger.error(f"❌ خطأ في عرض قائمة المدير: {e}")
            try:
                from Member.Menu import show_member_menu
                await show_member_menu(update, context)
            except Exception as e:
                logger.error(f"❌ خطأ في تحميل القائمة: {e}")
                await update.message.reply_text("❌ حدث خطأ في تحميل القائمة")
    
    else:
        try:
            from Member.Menu import show_member_menu
            await show_member_menu(update, context)
            
            user_data = db.get_user(user_id)
            if not user_data.get('joined_date'):
                user_data['joined_date'] = datetime.now().strftime("%Y-%m-%d")
                db.save_data()
                
                await context.bot.send_message(
                    chat_id=user_id,
                    text="🎉 **مرحباً بك في بوت المهام!**\n\n"
                         "💰 **لبدء كسب النقاط:**\n"
                         "1. 📋 تنفيذ المهام المتاحة\n"
                         "2. ➕ إنشاء مهام جديدة\n"
                         "3. 📨 دعوة الأصدقاء\n\n"
                         "🚀 ابدأ رحلتك الآن وكُن الأكثر نقاطاً!",
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            logger.error(f"❌ خطأ في عرض قائمة العضو: {e}")
            await update.message.reply_text("❌ حدث خطأ في تحميل القائمة")

    logger.info(f"✅ اكتملت جلسة المستخدم: {user_id}")

async def process_referral_in_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة رابط الدعوة عندما تكون الكابتشا معطلة"""
    user_id = update.effective_user.id
    
    if context.args and hasattr(db, 'is_invite_system_enabled') and db.is_invite_system_enabled() and not context.user_data.get('referral_processed', False):
        referral_id = context.args[0]
        logger.info(f"🎯 معالجة رابط دعوة (كابتشا معطلة): {referral_id} → {user_id}")
        
        if referral_id.isdigit() and referral_id != str(user_id):
            # ✅ استخدام دالة الدعوة المعدلة التي تسمح بالمستخدمين القدامى
            success, message = await process_invite_usage(referral_id, user_id, context)
            
            if success:
                context.user_data['referral_processed'] = True
                await send_referral_notifications(update, context, referral_id, user_id)
            else:
                logger.warning(f"⚠️ فشل في معالجة الدعوة: {message}")

async def process_referral_after_captcha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة رابط الدعوة بعد نجاح الكابتشا"""
    user_id = update.effective_user.id
    
    if context.args and hasattr(db, 'is_invite_system_enabled') and db.is_invite_system_enabled() and not context.user_data.get('referral_processed', False):
        referral_id = context.args[0]
        logger.info(f"🎯 معالجة رابط دعوة (بعد الكابتشا): {referral_id} → {user_id}")
        
        if referral_id.isdigit() and referral_id != str(user_id):
            # ✅ استخدام دالة الدعوة المعدلة التي تسمح بالمستخدمين القدامى
            success, message = await process_invite_usage(referral_id, user_id, context)
            
            if success:
                context.user_data['referral_processed'] = True
                await send_referral_notifications(update, context, referral_id, user_id)
            else:
                logger.warning(f"⚠️ فشل في معالجة الدعوة: {message}")

# Main.py - الجزء 3/7 - دوال معالجة الدعوات والإشعارات
async def process_invite_usage(referrer_id: str, invited_id: int, context: ContextTypes.DEFAULT_TYPE = None):
    """معالجة استخدام الدعوة - تسمح بالمستخدمين القدامى"""
    try:
        logger.info(f"🔍 معالجة دعوة: {referrer_id} دعا {invited_id}")
        
        referrer_id = str(referrer_id)
        invited_id = str(invited_id)
        
        # منع الاحتيال: لا يمكن دعوة النفس
        if referrer_id == invited_id:
            logger.warning(f"❌ محاولة دعوة النفس: {referrer_id}")
            return False, "لا يمكن دعوة نفسك"
        
        # الحصول على بيانات المدعي
        referrer = db.get_user(int(referrer_id))
        if not referrer:
            return False, "المدعي غير موجود"
        
        # ✅ التحقق إذا تم الدعوة مسبقاً
        invited_users = referrer.get('invited_users', [])
        
        if invited_id in invited_users:
            logger.warning(f"❌ تم دعوة هذا المستخدم مسبقاً: {invited_id}")
            return False, "تم دعوة هذا المستخدم مسبقاً"
        
        # ✅ تسجيل الدعوة للمدعي
        if 'invited_users' not in referrer:
            referrer['invited_users'] = []
        referrer['invited_users'].append(invited_id)
        
        # ✅ تحديث الدعوات اليومية
        today = datetime.now().strftime("%Y-%m-%d")
        if 'daily_invites' not in referrer:
            referrer['daily_invites'] = {}
        referrer['daily_invites'][today] = referrer['daily_invites'].get(today, 0) + 1
        
        logger.info(f"📊 عدد دعوات اليوم: {referrer['daily_invites'][today]} (لا يوجد حد أقصى)")
        
        # ✅ منح النقاط والأسهم للمدعي فقط
        invite_points = db.get_invite_points() if hasattr(db, 'get_invite_points') else 10
        
        # ✅ الحصول على إعدادات سهم الحظ
        luck_settings = db.get_luck_arrow_settings() if hasattr(db, 'get_luck_arrow_settings') else {}
        invite_arrows = luck_settings.get("invite_arrows", 1)
        
        logger.info(f"💰 محاولة منح {invite_points} نقطة و{invite_arrows} سهم للمدعي {referrer_id}")
        
        # الحصول على نقاط المدعي الحالية قبل الإضافة
        current_points = referrer.get('points', 0)
        
        # ✅ حفظ المستوى القديم قبل الإضافة
        old_level = db.get_user_level(referrer_id) if hasattr(db, 'get_user_level') else 1
        
        # منح النقاط
        success = db.add_points_to_user(referrer_id, invite_points) if hasattr(db, 'add_points_to_user') else True
        
        # منح الأسهم (سهم الحظ)
        arrow_success = False
        if success and invite_arrows > 0:
            arrow_success = db.add_arrows_to_user(referrer_id, invite_arrows) if hasattr(db, 'add_arrows_to_user') else True
            if not arrow_success:
                logger.error(f"❌ فشل في منح الأسهم للمدعي {referrer_id}")
        
        if success:
            new_points = db.get_user_points(referrer_id) if hasattr(db, 'get_user_points') else current_points + invite_points
            logger.info(f"✅ تم منح النقاط والأسهم بنجاح: {referrer_id} ({current_points} → {new_points}) + {invite_arrows} سهم")
            
            # ✅ التحقق من الترقية
            new_level = db.get_user_level(referrer_id) if hasattr(db, 'get_user_level') else old_level
            if new_level != old_level and context:
                db.add_user_stat(referrer_id, "level_ups", 1) if hasattr(db, 'add_user_stat') else None
                logger.info(f"🎉 المستخدم {referrer_id} ارتقى إلى مستوى جديد بسبب الدعوة")
                
                # إرسال رسالة الترقية إذا كان context متاحاً
                if context:
                    level_info = db.get_level_info(new_level) if hasattr(db, 'get_level_info') else {'name': f'المستوى {new_level}'}
                    benefits = level_info.get('benefits', [])
                    
                    benefits_message = ""
                    if "خصم 5% على المهام" in benefits:
                        benefits_message += "• 💰 خصم 5% على جميع المهام\n"
                    if "أولوية في الدعم" in benefits:
                        benefits_message += "• ⚡ أولوية في الدعم الفني\n"
                    if "خصم 10% على المهام" in benefits:
                        benefits_message += "• 💎 خصم 10% على جميع المهام\n"
                    if "ميزانية تثبيت مجانية" in benefits:
                        benefits_message += "• 🎯 تثبيت مجاني للمهام\n"
                    
                    try:
                        await context.bot.send_message(
                            chat_id=int(referrer_id),
                            text=f"""
🎉 **تهانينا! لقد ارتقت إلى مستوى جديد!**

🏆 المستوى الجديد: {level_info.get('name', '')}

✨ **مزاياك الجديدة:**
{benefits_message}

🚀 استمر في التقدم!
""",
                            parse_mode='Markdown'
                        )
                    except Exception as e:
                        logger.error(f"❌ خطأ في إرسال رسالة الترقية: {e}")
            
            db.save_data()
            return True, f"تم منح {invite_points} نقطة و{invite_arrows} سهم لدعوة مستخدم جديد"
        else:
            logger.error(f"❌ فشل في منح النقاط للمدعي {referrer_id}")
            return False, "حدث خطأ في منح النقاط"
        
    except Exception as e:
        logger.error(f"❌ خطأ في process_invite_usage: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return False, "حدث خطأ في معالجة الدعوة"

async def send_referral_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE, referral_id: str, user_id: int):
    """إرسال إشعارات الدعوة"""
    try:
        # الحصول على اسم المدعي بدلاً من الأيدي
        try:
            referrer_chat = await context.bot.get_chat(int(referral_id))
            referrer_name = referrer_chat.first_name or f"المستخدم {referral_id}"
        except:
            referrer_name = f"المستخدم {referral_id}"
        
        # الحصول على اسم المدعو بدلاً من الأيدي
        try:
            invited_chat = await context.bot.get_chat(user_id)
            invited_name = invited_chat.first_name or f"المستخدم {user_id}"
        except:
            invited_name = f"المستخدم {user_id}"
        
        invite_points = db.get_invite_points() if hasattr(db, 'get_invite_points') else 10
        
        # ✅ الحصول على إعدادات سهم الحظ
        luck_settings = db.get_luck_arrow_settings() if hasattr(db, 'get_luck_arrow_settings') else {}
        invite_arrows = luck_settings.get("invite_arrows", 1)
        
        # رسالة الترحيب للمدعو
        await context.bot.send_message(
            chat_id=user_id,
            text=f"🎉 **مرحباً بك!**\n\n"
                 f"شكراً لدخولك عبر دعوة من {referrer_name}\n"
                 f"✅ يمكنك الآن البدء في كسب النقاط عبر:\n\n"
                 f"• 📋 تنفيذ المهام المتاحة\n"
                 f"• ➕ إنشاء مهام جديدة  \n"
                 f"• 📨 دعوة الأصدقاء\n"
                 f"• 🎯 لعب سهم الحظ\n\n"
                 f"🚀 ابدأ رحلتك الآن وكُن الأكثر نقاطاً!",
            parse_mode='Markdown'
        )
        
        # رسالة الإشعار للمدعي (المعدلة)
        await context.bot.send_message(
            chat_id=int(referral_id),
            text=f"🎉 **تم قبول الدعوة!**\n\n"
                 f"👤 قام {invited_name} بدخول البوت عبر رابط دعوتك!\n"
                 f"💰 حصلت على {invite_points} نقطة\n"
                 f"🏹 حصلت على {invite_arrows} سهم حظ\n\n"
                 f"🎯 تابع دعوة المزيد لزيادة نقاطك وأسهمك!",
            parse_mode='Markdown'
        )
        
        logger.info(f"📨 تم إرسال الإشعارات للطرفين: {referrer_name} ← {invited_name}")
        
    except Exception as e:
        logger.error(f"❌ خطأ في إرسال الإشعارات: {e}")
        # محاولة إرسال رسالة بديلة في حالة الخطأ
        try:
            await context.bot.send_message(
                chat_id=int(referral_id),
                text=f"🎉 تم قبول الدعوة!\n\n"
                     f"👤 قام مستخدم جديد بدخول البوت عبر رابط دعوتك!\n"
                     f"💰 حصلت على {invite_points} نقطة\n"
                     f"🏹 حصلت على {invite_arrows} سهم حظ\n\n"
                     f"🎯 تابع دعوة المزيد!",
            )
        except:
            pass

# Main.py - الجزء 2/3
async def get_referrer_name(user_id, context):
    """دالة مساعدة خارجية للحصول على اسم المستخدم"""
    try:
        user = await context.bot.get_chat(user_id)
        return user.first_name or f"المستخدم {user_id}"
    except:
        return f"المستخدم {user_id}"

# في Main.py - تحديث معالجة الترقية
async def process_level_up(user_id, context, old_level, new_level):
    """معالجة الترقية إلى مستوى جديد - الإصدار المصحح"""
    try:
        sys.path.insert(0, os.path.join(current_dir, 'Member'))
        from Member.LevelBenefits import apply_level_benefits
        
        # تطبيق مزايا المستوى الجديد
        benefits_applied = await apply_level_benefits(user_id, context)
        
        # إرسال رسالة الترقية
        level_info = db.get_level_info(new_level) if hasattr(db, 'get_level_info') else {'name': f'المستوى {new_level}'}
        old_level_info = db.get_level_info(old_level) if hasattr(db, 'get_level_info') else {'name': f'المستوى {old_level}'}
        
        benefits_text = "\n".join([f"• {benefit}" for benefit in benefits_applied]) if benefits_applied else "• 📝 لا توجد مزايا جديدة"
        
        await context.bot.send_message(
            chat_id=user_id,
            text=f"""
🎉 **تهانينا! لقد ارتقت إلى مستوى جديد!**

🏆 المستوى الجديد: {level_info.get('name', '')}
⭐ من: {old_level_info.get('name', '')} → إلى: {level_info.get('name', '')}

✨ **مزاياك الجديدة:**
{benefits_text}

🚀 استمر في التقدم!
""",
            parse_mode='Markdown'
        )
        
        return True
        
    except Exception as e:
        logger.error(f"❌ خطأ في process_level_up: {e}")
        return False

# Main.py - الجزء 4/7 - معالجة الرسائل النصية
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل النصية العامة"""
    # التحقق من الحظر أولاً
    if not await check_blocked_middleware(update, context):
        return
    
    # التحقق من أن الرسالة في محادثة خاصة
    if update.message.chat.type != "private":
        return
    
    user_id = update.effective_user.id
    text = update.message.text
    
    # معالجة عندما يكتب المستخدم / فقط
    if await handle_slash_command(update, context):
        return

    # ✅ ✅ ✅ الإصلاح: معالجة رسائل إدارة المعلومات - أضف هذا الكود هنا
    if context.user_data.get('editing_text_type'):
        try:
            sys.path.insert(0, os.path.join(current_dir, 'Admin'))
            from Admin.InfoManager import handle_info_manager_messages
            await handle_info_manager_messages(update, context, text)
            return
        except Exception as e:
            logger.error(f"خطأ في معالجة رسائل إدارة المعلومات: {e}")
            await update.message.reply_text("❌ حدث خطأ في المعالجة")
        return
    
    # ✅ معالجة البحث عن المهام
    if context.user_data.get('awaiting_task_search'):
        try:
            sys.path.insert(0, os.path.join(current_dir, 'Admin'))
            from Admin.Tasks import handle_task_search
            await handle_task_search(update, context, text)
            return
        except Exception as e:
            logger.error(f"خطأ في معالجة البحث: {e}")
            await update.message.reply_text("❌ حدث خطأ في البحث")
            context.user_data.pop('awaiting_task_search', None)
        return
    
    # إذا كان المستخدم في منتصف محادثة (إثبات مهمة)
    if 'executing_task' in context.user_data and context.user_data.get('execution_step') == 'awaiting_proof':
        try:
            sys.path.insert(0, os.path.join(current_dir, 'Member'))
            from Member.Tasks_Execution import handle_proof_submission
            await handle_proof_submission(update, context)
            return
        except Exception as e:
            logger.error(f"خطأ في معالجة الإثبات: {e}")
    
    # إذا كان المستخدم في وضع انتظار شكوى
    if context.user_data.get('awaiting_complaint'):
        try:
            # إرسال الشكوى للمالك
            await context.bot.send_message(
                chat_id=OWNER_ID,
                text=f"📞 شكوى من المستخدم {user_id}:\n\n{text}"
            )
            await update.message.reply_text("✅ تم إرسال شكواك بنجاح، سيتم الرد عليك قريباً")
            context.user_data.pop('awaiting_complaint', None)
            return
        except Exception as e:
            logger.error(f"خطأ في معالجة الشكوى: {e}")
            await update.message.reply_text("❌ حدث خطأ في إرسال الشكوى")
            context.user_data.pop('awaiting_complaint', None)
            return
    
    # إذا كان المستخدم في وضع انتظار البحث
    if context.user_data.get('awaiting_search'):
        try:
            sys.path.insert(0, os.path.join(current_dir, 'Member'))
            from Member.Tasks_View import search_tasks
            await search_tasks(update, context, text)
            context.user_data.pop('awaiting_search', None)
            return
        except Exception as e:
            logger.error(f"خطأ في معالجة البحث: {e}")
            await update.message.reply_text("❌ حدث خطأ في البحث")
            context.user_data.pop('awaiting_search', None)
            return
    
    # إذا كان المستخدم في وضع انتظار كود الهدية
    if context.user_data.get('awaiting_gift_code'):
        try:
            sys.path.insert(0, os.path.join(current_dir, 'Member'))
            from Member.GiftCode import handle_gift_code_input
            await handle_gift_code_input(update, context)
            return
        except Exception as e:
            logger.error(f"خطأ في معالجة كود الهدية: {e}")
            await update.message.reply_text("❌ حدث خطأ في معالجة الكود")
            context.user_data.pop('awaiting_gift_code', None)
            return
    
    # ✅ معالجة رسائل إنشاء الأزرار
    if 'button_creation' in context.user_data:
        try:
            sys.path.insert(0, os.path.join(current_dir, 'Admin'))
            from Admin.ButtonManager import ButtonManager
            if await ButtonManager.handle_button_creation(update, context):
                return
        except Exception as e:
            logger.error(f"خطأ في معالجة إنشاء الأزرار: {e}")
            await update.message.reply_text("❌ حدث خطأ في إنشاء الزر")
        return

    # ✅ معالجة رسائل إنشاء الأزرار الفرعية
    if 'submenu_button_creation' in context.user_data:
        try:
            sys.path.insert(0, os.path.join(current_dir, 'Admin'))
            from Admin.ButtonManager import ButtonManager
            if await ButtonManager.handle_submenu_button_creation(update, context):
                return
        except Exception as e: 
            logger.error(f"خطأ في معالجة إنشاء الزر الفرعي: {e}")
            # تنظيف البيانات في حالة الخطأ
            context.user_data.pop('submenu_button_creation', None)
            await update.message.reply_text("❌ حدث خطأ في إنشاء الزر الفرعي")
            return

    # ✅ معالجة رسائل إعادة التسمية
    if 'renaming_button' in context.user_data:
        try:
            sys.path.insert(0, os.path.join(current_dir, 'Admin'))
            from Admin.ButtonManager import ButtonManager
            if await ButtonManager.handle_button_rename(update, context):
                return
        except Exception as e:
            logger.error(f"خطأ في معالجة إعادة التسمية: {e}")
            context.user_data.pop('renaming_button', None)
            await update.message.reply_text("❌ حدث خطأ في التسمية")
            return

    # ✅ معالجة رسائل تغيير الإيموجي
    if 'changing_emoji' in context.user_data:
        try:
            sys.path.insert(0, os.path.join(current_dir, 'Admin'))
            from Admin.ButtonManager import ButtonManager
            if await ButtonManager.handle_emoji_change(update, context):
                return
        except Exception as e:
            logger.error(f"خطأ في معالجة تغيير الإيموجي: {e}")
            context.user_data.pop('changing_emoji', None)
            await update.message.reply_text("❌ حدث خطأ في التغيير")
            return

    # ✅ معالجة رسائل تغيير المحتوى
    if 'changing_content' in context.user_data:
        try:
            sys.path.insert(0, os.path.join(current_dir, 'Admin'))
            from Admin.ButtonManager import ButtonManager
            if await ButtonManager.handle_content_change(update, context):
                return
        except Exception as e:
            logger.error(f"خطأ في معالجة تغيير المحتوى: {e}")
            context.user_data.pop('changing_content', None)
            await update.message.reply_text("❌ حدث خطأ في التحديث")
            return

    # في دالة handle_message - أضف هذا الكود بعد معالجة الهدايا
    # ✅ معالجة رسائل إدارة سهم الحظ
    elif (context.user_data.get('awaiting_daily_limit') or 
          context.user_data.get('awaiting_invite_arrows') or 
          context.user_data.get('awaiting_invite_points') or 
          context.user_data.get('awaiting_box_capacity') or 
          context.user_data.get('awaiting_give_arrows') or
          context.user_data.get('awaiting_prize_points') or
          context.user_data.get('awaiting_prize_arrows') or
          context.user_data.get('awaiting_prize_gift_code')):
        try:
            sys.path.insert(0, os.path.join(current_dir, 'Admin'))
            from Admin.LuckArrowAdmin import handle_arrow_admin_messages
            await handle_arrow_admin_messages(update, context, text)
            return
        except Exception as e:
            logger.error(f"خطأ في معالجة رسائل الأسهم: {e}")
            await update.message.reply_text("❌ حدث خطأ في المعالجة")
            # تنظيف حالة الانتظار
            for key in ['awaiting_daily_limit', 'awaiting_invite_arrows', 
                       'awaiting_invite_points', 'awaiting_box_capacity', 
                       'awaiting_give_arrows', 'awaiting_prize_points',
                       'awaiting_prize_arrows', 'awaiting_prize_gift_code']:
                context.user_data.pop(key, None)
            return

    # معالجة الرسائل الإدارية إذا كان المستخدم أدمن
    if str(user_id) in db.get_admins() or user_id == OWNER_ID:
        try:
            sys.path.insert(0, os.path.join(current_dir, 'Admin'))
            from Admin.Menu import handle_admin_messages
            # تمرير الرسالة للمعالج الإداري مع نص الرسالة
            await handle_admin_messages(update, context, text)
            return
        except Exception as e:
            logger.error(f"خطأ في معالجة رسائل المدير: {e}")
    
    # إذا كان المستخدم في منتصف إضافة مهمة
    try:
        sys.path.insert(0, os.path.join(current_dir, 'Member'))
        from Member.AddTask import handle_task_message
        if await handle_task_message(update, context):
            return
    except Exception as e:
        logger.error(f"خطأ في معالجة إضافة المهمة: {e}")
    
    # إذا لم تكن رسالة معروفة، إظهار رسالة المساعدة
    await update.message.reply_text("❌ الأمر غير معروف. استخدم /start للبدء.")

# Main.py - الجزء 5/7 - معالجة استعلامات Callback Query (الجزء الأول)
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة استعلامات الـ Callback Query"""
    try:
        query = update.callback_query
        await query.answer()
        
        data = query.data
        logger.info(f"تم استقبال callback query: {data} من المستخدم: {update.effective_user.id}")
        
        # التحقق من الحظر أولاً
        if not await check_blocked_middleware(update, context):
            return

        # ✅ معالجة قبول/رفض الشروط
        if data in ["accept_terms", "reject_terms"]:
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Member'))
                from Member.Terms import terms_handler
                await terms_handler(update, context)
                return
            except Exception as e:
                logger.error(f"❌ خطأ في معالجة الشروط: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return
        
        elif data == "reset_prizes":
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.LuckArrowAdmin import handle_arrow_admin_callbacks
                await handle_arrow_admin_callbacks(update, context)
                return
            except Exception as e:
                logger.error(f"خطأ في reset_prizes: {e}")
                await query.answer("❌ حدث خطأ في إعادة التعيين")
                return

        # في Main.py أضف هذا المعالج
        elif data == "refresh_benefits":
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Member'))
                from Member.LevelBenefits import show_level_benefits
                await show_level_benefits(update, context)
                return
            except Exception as e:
                logger.error(f"خطأ في refresh_benefits: {e}")
                await query.answer("❌ حدث خطأ في تحديث المزايا")

        # ✅ معالجة إعدادات الأرباح
        elif data in ["profit_settings_menu", "set_profit_percentage", "set_task_limits"] or data.startswith("limit_"):
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.ProfitSettings import profit_settings_handler
                await profit_settings_handler(update, context)
                return
            except Exception as e:
                logger.error(f"❌ خطأ في معالجة إعدادات الأرباح: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return
        
        # ✅ معالجة إعدادات التثبيت
        elif data in ["pin_settings_menu", "set_pin_price", "set_pin_duration", "set_max_pins"]:
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.PinSettings import pin_settings_handler
                await pin_settings_handler(update, context)
                return
            except Exception as e:
                logger.error(f"❌ خطأ في معالجة إعدادات التثبيت: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return
        
        # ✅ معالجة التثبيت
        elif data.startswith("pin_task_"):
            task_id = data.split("_")[2]
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Member'))
                from Member.PinTask import pin_task_handler
                await pin_task_handler(update, context, task_id)
                return
            except Exception as e:
                logger.error(f"❌ خطأ في معالجة التثبيت: {e}")
                await query.answer("❌ حدث خطأ في التثبيت")
                return
        
        # في Main.py - المعالج الصحيح
        elif data.startswith("reset_"):
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.InfoManager import reset_to_default
                text_type_suffix = data.split("_")[1]
        
                # خريطة الربط بين اللاحقة ونوع النص الكامل
                text_type_map = {
                    "welcome": "welcome_message",
                    "invite": "invite_message",
                    "support": "support_info", 
                    "terms": "terms_info",
                    "user_guide": "user_guide_text",
                    "exchange": "exchange_text"
                }
        
                if text_type_suffix in text_type_map:
                    await reset_to_default(update, context, text_type_map[text_type_suffix])
                else:
                    await query.answer("❌ نوع النص غير معروف")
                return
            except Exception as e:
                logger.error(f"❌ خطأ في الإعادة إلى الافتراضي: {e}")
                await query.answer("❌ حدث خطأ في الإعادة")
                return

        # في Main.py - إضافة المعالجات الجديدة
        elif data == "user_guide":
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Member'))
                from Member.Menu import show_user_guide
                await show_user_guide(update, context)
                return
            except Exception as e:
                logger.error(f"خطأ في دليل الاستخدام: {e}")
                await query.answer("❌ نظام دليل الاستخدام غير متوفر")
                return

        elif data == "exchange_points":
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Member'))
                from Member.Menu import show_exchange_points
                await show_exchange_points(update, context)
                return
            except Exception as e:
                logger.error(f"خطأ في استبدال النقاط: {e}")
                await query.answer("❌ نظام استبدال النقاط غير متوفر")
                return

        elif data.startswith("confirm_pin_"):
            task_id = data.split("_")[2]
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Member'))
                from Member.PinTask import handle_confirm_pin
                await handle_confirm_pin(update, context, task_id)
                return
            except Exception as e:
                logger.error(f"❌ خطأ في تأكيد التثبيت: {e}")
                await query.answer("❌ حدث خطأ في التأكيد")
                return
        
        elif data.startswith("unpin_task_"):
            task_id = data.split("_")[2]
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Member'))
                from Member.PinTask import unpin_task_handler
                await unpin_task_handler(update, context, task_id)
                return
            except Exception as e:
                logger.error(f"❌ خطأ في إلغاء التثبيت: {e}")
                await query.answer("❌ حدث خطأ في الإلغاء")
                return
        
        # في Main.py - تحديث معالج callback query
        elif data == "member_level_info":
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Member'))
                from Member.Levels import show_levels_info
                await show_levels_info(update, context)
                return
            except Exception as e:
                logger.error(f"خطأ في نظام المستويات: {e}")
                # محاولة إعادة تحميل الوحدة
                try:
                    import importlib
                    sys.path.insert(0, os.path.join(current_dir, 'Member'))
                    from Member import Levels
                    importlib.reload(Levels)
                    from Member.Levels import show_levels_info
                    await show_levels_info(update, context)
                except Exception as reload_error:
                    logger.error(f"خطأ في إعادة تحميل المستويات: {reload_error}")
                    await query.answer("❌ حدث خطأ في تحميل نظام المستويات")
                return

        # ✅ معالجات إدارة المعلومات
        elif (data in ["info_manager_menu", "add_user_button", "view_user_buttons", "refresh_info_menu"] or 
            data.startswith("delete_user_button_") or data.startswith("edit_user_button_") or 
            data.startswith("user_button_")):
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.InfoManager import info_manager_handler
                await info_manager_handler(update, context)
                return
            except Exception as e:
                logger.error(f"❌ خطأ في معالجة إدارة المعلومات: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return
            
        # ✅ معالجات إدارة المهام
        elif data in ["tasks_menu", "tasks_search"] or data.startswith("delete_task_"):
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.Tasks import tasks_handler
                await tasks_handler(update, context)
                return
            except Exception as e:
                logger.error(f"❌ خطأ في معالجة المهام: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return
        
        # معالجات المدير
        elif data in ["admin_menu", "admin_shortcuts", "moder_back"]:
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.Menu import admin_menu_handler
                await admin_menu_handler(update, context)
                return
            except Exception as e:
                logger.error(f"❌ خطأ في معالجة قائمة المدير: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return

        # في دالة admin_menu_handler - أضف هذا المعالج
        elif data == "luck_arrow_admin":
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.LuckArrowAdmin import luck_arrow_admin_menu
                await luck_arrow_admin_menu(update, context)
                return
            except Exception as e:
                logger.error(f"❌ خطأ في معالجة سهم الحظ: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return
            
        elif data in ["blocked_list", "block_user", "unblock_user"] or data.startswith("block_") or data.startswith("unblock_"):
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.Block import block_handler
                await block_handler(update, context)
                return
            except Exception as e:
                logger.error(f"❌ خطأ في معالجة الحظر: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return
            
        elif data == "admin_restart":
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.Restart import restart_handler
                await restart_handler(update, context)
                return
            except Exception as e:
                logger.error(f"❌ خطأ في معالجة إعادة التشغيل: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return
            
        elif data in ["admins_list", "admins_add", "admins_remove"] or data.startswith("remove_admin_"):
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.Admins import admins_handler
                await admins_handler(update, context)
                return
            except Exception as e:
                logger.error(f"❌ خطأ في معالجة المشرفين: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return

        elif data in ["channel_menu", "channel_add", "channel_remove", "check_channels"] or data.startswith("remove_channel_"):
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.Channel import channel_handler
                await channel_handler(update, context)
                return
            except Exception as e:
                logger.error(f"❌ خطأ في معالجة القنوات: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return

        elif data in ["invite_menu", "invite_add_points", "invite_remove_points", 
                     "invite_set_points", "invite_send_all", "invite_reset_all", "invite_toggle_system", "invite_stats"]:
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.Invite import invite_handler
                handled = await invite_handler(update, context)
                if not handled:
                    await query.answer("❌ حدث خطأ في المعالجة")
                return
            except Exception as e:
                logger.error(f"❌ خطأ في معالجة الدعوات: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return
            
        elif data in ["moder_menu", "moder_broadcast", "moder_stats"]:
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.Moder import moder_handler
                await moder_handler(update, context)
                return
            except Exception as e:
                logger.error(f"❌ خطأ في معالجة المشرفين: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return
            
        elif data in ["tasks_channels_menu", "set_tasks_channel", "set_completed_channel", "test_channels"]:
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.TasksChannels import tasks_channels_handler
                await tasks_channels_handler(update, context)
                return
            except Exception as e:
                logger.error(f"❌ خطأ في معالجة قنوات المهام: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return
        
        # ✅ معالجات أكواد الهدايا للمدير
        elif data in ["gift_codes_menu", "gift_code_create", "gift_code_list"] or data.startswith("view_gift_code_"):
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.GiftCodes import gift_codes_handler
                await gift_codes_handler(update, context)
                return
            except Exception as e:
                logger.error(f"خطأ في معالجة الهدايا: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return
                
        elif data.startswith("use_auto_code_"):
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.GiftCodes import use_auto_code
                code = data.split("_")[3]
                await use_auto_code(update, context, code)
                return
            except Exception as e:
                logger.error(f"خطأ في use_auto_code: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return
                
        elif data == "enter_custom_code":
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.GiftCodes import enter_custom_code
                await enter_custom_code(update, context)
                return
            except Exception as e:
                logger.error(f"خطأ في enter_custom_code: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return

# Main.py - الجزء 6/7 - معالجة استعلامات Callback Query (الجزء الثاني)
        # في Main.py - تحديث معالجات InfoManager
        elif data == "edit_welcome_message":
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.InfoManager import edit_text_prompt
                await edit_text_prompt(update, context, "welcome_message", "رسالة الترحيب")
                return
            except Exception as e:
                logger.error(f"❌ خطأ في تعديل الترحيب: {e}")
                await query.answer("❌ حدث خطأ في التعديل")
                return

        elif data == "edit_invite_message":
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.InfoManager import edit_text_prompt
                await edit_text_prompt(update, context, "invite_message", "رسالة الدعوة")
                return
            except Exception as e:
                logger.error(f"❌ خطأ في تعديل الدعوة: {e}")
                await query.answer("❌ حدث خطأ في التعديل")
                return

        elif data == "edit_support_info":
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.InfoManager import edit_text_prompt
                await edit_text_prompt(update, context, "support_info", "معلومات الدعم")
                return
            except Exception as e:
                 logger.error(f"❌ خطأ في تعديل الدعم: {e}")
                 await query.answer("❌ حدث خطأ في التعديل")
                 return

        elif data == "edit_terms_info":
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.InfoManager import edit_text_prompt
                await edit_text_prompt(update, context, "terms_info", "الشروط والخصوصية")
                return
            except Exception as e:
                logger.error(f"❌ خطأ في تعديل الشروط: {e}")
                await query.answer("❌ حدث خطأ في التعديل")
                return

        elif data == "edit_user_guide":
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.InfoManager import edit_text_prompt
                await edit_text_prompt(update, context, "user_guide_text", "دليل الاستخدام")
                return
            except Exception as e:
                logger.error(f"❌ خطأ في تعديل الدليل: {e}")
                await query.answer("❌ حدث خطأ في التعديل")
                return

        elif data == "edit_exchange_info":
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.InfoManager import edit_text_prompt
                await edit_text_prompt(update, context, "exchange_text", "استبدال النقاط")
                return
            except Exception as e:
                logger.error(f"❌ خطأ في تعديل الاستبدال: {e}")
                await query.answer("❌ حدث خطأ في التعديل")
                return

        # في دالة handle_callback_query - أضف هذه المعالجات
        elif data == "luck_arrow_menu":
            try:
                sys.path.insert(0, current_dir)
                from LuckArrow import luck_arrow_menu
                await luck_arrow_menu(update, context)
                return
            except Exception as e:
                logger.error(f"❌ خطأ في معالجة سهم الحظ: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return

        elif data == "luck_arrow_admin":
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.LuckArrowAdmin import luck_arrow_admin_menu
                await luck_arrow_admin_menu(update, context)
                return
            except Exception as e:
                logger.error(f"❌ خطأ في معالجة إدارة سهم الحظ: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return

        elif data in ["spin_arrow", "arrow_history", "box_info"]:
            try:
                sys.path.insert(0, current_dir)
                from LuckArrow import luck_arrow_handler
                await luck_arrow_handler(update, context)
                return
            except Exception as e:
                logger.error(f"❌ خطأ في معالجة سهم الحظ: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return

        # معالجات إدارة سهم الحظ
        elif data in ["manage_arrow_box", "arrow_settings", "give_arrows", "arrow_stats", 
                     "manage_prizes", "view_prizes", "weekly_report", "set_daily_limit",
                     "set_invite_arrows", "set_invite_points", "set_box_capacity",
                     "reset_box", "toggle_box", "reset_prizes", "add_prize", 
                     "add_prize_points", "add_prize_arrows", "add_prize_gift_code", "edit_prizes"]:
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.LuckArrowAdmin import handle_arrow_admin_callbacks
                await handle_arrow_admin_callbacks(update, context)
                return
            except Exception as e:
                logger.error(f"❌ خطأ في معالجة إدارة سهم الحظ: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return

      # في handle_callback_query - أضف قبل المعالجات الأخرى
      # ✅ معالجة زر سهم الحظ في القائمة الرئيسية
        elif data == "member_luck_arrow":
            try:
                sys.path.insert(0, current_dir)
                from LuckArrow import luck_arrow_menu
                await luck_arrow_menu(update, context)
                return
            except Exception as e:
                logger.error(f"خطأ في تحميل سهم الحظ: {e}")
                await query.answer("❌ نظام سهم الحظ غير متوفر حالياً")
                return

        # معالجات إدارة الأزرار
        elif data == "button_manager_menu":
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.ButtonManager import ButtonManager
                await ButtonManager.main_menu(update, context)
                return
            except Exception as e:
                logger.error(f"خطأ في button_manager_menu: {e}")
                await query.answer("❌ حدث خطأ في إدارة الأزرار")
                return

        elif data == "btn_mgr_main":
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.ButtonManager import ButtonManager
                await ButtonManager.main_menu(update, context)
                return
            except Exception as e:
                logger.error(f"❌ خطأ في معالجة الزر الرئيسي: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return

        elif data == "btn_mgr_main_menu":
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.ButtonManager import ButtonManager
                await ButtonManager.manage_main_buttons(update, context)
                return
            except Exception as e:
                logger.error(f"❌ خطأ في معالجة القائمة الرئيسية: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return

        elif data == "btn_mgr_create":
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.ButtonManager import ButtonManager
                await ButtonManager.create_button_start(update, context)
                return
            except Exception as e:
                logger.error(f"❌ خطأ في إنشاء الزر: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return

        elif data == "btn_mgr_confirm_create":
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.ButtonManager import ButtonManager
                await ButtonManager.confirm_button_creation(update, context)
                return
            except Exception as e:
                logger.error(f"❌ خطأ في تأكيد الإنشاء: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return

        # معالجة الأزرار المخصصة
        elif data.startswith("custom_btn_"):
            try:
                button_id = data.replace("custom_btn_", "")
                logger.info(f"🎯 معالجة زر مخصص: {button_id}")
        
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.ButtonManager import ButtonHandler
                logger.info("✅ تم استيراد ButtonHandler")
        
                result = await ButtonHandler.handle_custom_button(update, context, button_id)
                logger.info(f"✅ تمت معالجة الزر: {result}")
                return
        
            except ImportError as e:
                logger.error(f"❌ خطأ في الاستيراد: {e}")
                await query.answer("❌ النظام غير متوفر")
                return
            except Exception as e:
                logger.error(f"❌ خطأ في معالجة الزر المخصص: {e}", exc_info=True)
                await query.answer("❌ حدث خطأ في المعالجة")
                return

# ✅ معالجة تعديل زر مخصص
        elif data.startswith("btn_mgr_edit_custom:"):
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.ButtonManager import ButtonManager
                button_id = data.split(":")[1]  # استخراج ID الزر
                await ButtonManager.edit_custom_button(update, context, button_id)
                return
            except Exception as e:
                logger.error(f"خطأ في btn_mgr_edit_custom: {e}")
                await query.answer("❌ حدث خطأ في تعديل الزر")
                return

        elif data.startswith("btn_mgr:"):
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.ButtonManager import button_manager_handler
                await button_manager_handler(update, context)
                return
            except Exception as e:
                logger.error(f"خطأ في معالجة إدارة الأزرار: {e}")
                await query.answer("❌ حدث خطأ في الإدارة")
                return

        elif data.startswith("btn_edit:"):
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.ButtonManager import ButtonManager
                parts = data.split(":")
                action = parts[1]
                button_id = parts[2]
        
                if action == "rename":
                    await ButtonManager.rename_button(update, context, button_id)
                elif action == "rename_protected":
                    await ButtonManager.rename_button(update, context, button_id, True)
                elif action == "recontent":
                    await ButtonManager.change_button_content(update, context, button_id)
                elif action == "emoji":
                    await ButtonManager.change_button_emoji(update, context, button_id)
                elif action == "emoji_protected":
                    await ButtonManager.change_button_emoji(update, context, button_id, True)
                elif action == "move_up":
                    await ButtonManager.move_button(update, context, button_id, "up")
                elif action == "move_down":
                    await ButtonManager.move_button(update, context, button_id, "down")
                elif action == "delete":
                    await ButtonManager.delete_button(update, context, button_id)
                elif action == "manage_sub":
                    await ButtonManager.manage_submenu(update, context, button_id)
                return
            except Exception as e:
                logger.error(f"خطأ في معالجة تحرير الزر: {e}")
                await query.answer("❌ حدث خطأ في التحرير")
                return

        elif data.startswith("btn_create:"):
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.ButtonManager import ButtonManager
                action = data.split(":")[1]
        
                if action == "confirm":
                    await ButtonManager.confirm_button_creation(update, context)
                elif action == "skip_emoji":
                    # تخطي الإيموجي والمتابعة للمحتوى
                    if "button_creation" in context.user_data:
                        context.user_data["button_creation"]["step"] = "awaiting_content"
                        await query.edit_message_text(
                            "⏭️ تم تخطي الإيموجي\n\n📝 أرسل محتوى الزر:",
                            reply_markup=InlineKeyboardMarkup([
                                [InlineKeyboardButton("🔙 إلغاء", callback_data="btn_mgr:main_menu")]
                            ])
                        )
                return
            except Exception as e:
                logger.error(f"خطأ في معالجة إنشاء الزر: {e}")
                await query.answer("❌ حدث خطأ في الإنشاء")
                return

        elif data.startswith("btn_reorder:"):
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.ButtonManager import ButtonManager
                parts = data.split(":")
                action = parts[1]
                button_id = parts[2] if len(parts) > 2 else None
        
                if action == "save":
                    await ButtonManager.handle_reorder_action(update, context, "save", button_id)
                elif action in ["move_up", "move_down"] and button_id:
                    await ButtonManager.handle_reorder_action(update, context, action, button_id)
                return
            except Exception as e:
                logger.error(f"خطأ في إعادة الترتيب: {e}")
                await query.answer("❌ حدث خطأ في الترتيب")
                return

# Main.py - الجزء 7/7 - معالجة استعلامات Callback Query (الجزء الثالث) والدوال النهائية
        elif data.startswith("btn_sub:"):
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.ButtonManager import ButtonManager
                parts = data.split(":")
                action = parts[1]
        
                # إذا كان زر فرعي عادي (ليس للإدارة)
                if action == "press" and len(parts) > 2:
                    button_id = parts[2]
                    from Admin.ButtonManager import ButtonHandler
                    await ButtonHandler.handle_custom_button(update, context, button_id)
                    return
            
                elif action == "manage" and len(parts) > 2:
                    submenu_id = parts[2]
                    await ButtonManager.manage_submenu(update, context, submenu_id)
                elif action == "add" and len(parts) > 2:
                    submenu_id = parts[2]
                    await ButtonManager.add_submenu_button(update, context, submenu_id)
                return
            except Exception as e:
                logger.error(f"خطأ في معالجة الزر الفرعي: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return

        elif data.startswith("custom_btn_"):
            try:
                button_id = data.replace("custom_btn_", "")
                logger.info(f"🎯 معالجة زر مخصص: {button_id}")
        
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.ButtonManager import ButtonHandler
                logger.info("✅ تم استيراد ButtonHandler")
        
                result = await ButtonHandler.handle_custom_button(update, context, button_id)
                logger.info(f"✅ تمت معالجة الزر: {result}")
                return
        
            except ImportError as e:
                logger.error(f"❌ خطأ في الاستيراد: {e}")
                await query.answer("❌ النظام غير متوفر")
                return
            except Exception as e:
                logger.error(f"❌ خطأ في معالجة الزر المخصص: {e}", exc_info=True)
                await query.answer("❌ حدث خطأ في المعالجة")
                return

        # في Main.py - داخل handle_callback_query function
        elif data.startswith("btn_sub:press:"):
            try:
                # معالجة الضغط على الأزرار داخل القوائم الفرعية
                button_id = data.split(":")[2]
                logger.info(f"🎯 معالجة زر فرعي: {button_id}")
        
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.ButtonManager import ButtonHandler
                await ButtonHandler.handle_custom_button(update, context, button_id)
                return
            except Exception as e:
                logger.error(f"❌ خطأ في معالجة الزر الفرعي: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return

        elif data.startswith("btn_sub:press:"):
            try:
                # معالجة الضغط على الأزرار داخل القوائم الفرعية
                button_id = data.split(":")[2]
                logger.info(f"🎯 معالجة زر فرعي: {button_id}")
        
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.ButtonManager import ButtonHandler
                await ButtonHandler.handle_custom_button(update, context, button_id)
                return
            except Exception as e:
                logger.error(f"❌ خطأ في معالجة الزر الفرعي: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return

        # معالجات العضو - القوائم
        elif data in ["member_menu", "member_tasks_back"]:
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Member'))
                from Member.Menu import member_menu_handler
                await member_menu_handler(update, context)
                return
            except Exception as e:
                logger.error(f"❌ خطأ في معالجة قائمة العضو: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return
            
        elif data in ["member_invite_link", "member_invite_points", "member_invite_stats"]:
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Member'))
                from Member.Invite import invite_handler as member_invite_handler
                await member_invite_handler(update, context)
                return
            except Exception as e:
                logger.error(f"❌ خطأ في معالجة الدعوات: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return
            
        elif data in ["complaint_send", "complaint_policy"]:
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Member'))
                from Member.Complaint import complaint_handler
                await complaint_handler(update, context)
                return
            except Exception as e:
                logger.error(f"❌ خطأ في معالجة الشكاوى: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return
            
        elif data == "show_task_types":
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Member'))
                from Member.Menu import show_task_types
                await show_task_types(update, context)
                return
            except Exception as e:
                logger.error(f"❌ خطأ في عرض أنواع المهام: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return
            
        elif data.startswith("addtask_"):
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Member'))
                from Member.AddTask import choose_task_type
                await choose_task_type(update, context)
                return
            except Exception as e:
                logger.error(f"❌ خطأ في إضافة المهمة: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return
        
        # ✅ معالجات كود الهدية للعضو
        elif data == "member_gift_code":
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Member'))
                from Member.GiftCode import gift_code_handler
                await gift_code_handler(update, context)
                return
            except Exception as e:
                logger.error(f"خطأ في gift_code_handler: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return
        
        # ✅ معالجات الأزرار الجديدة للعضو
        elif data == "show_support_info":
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Member'))
                from Member.Menu import show_support_info
                await show_support_info(update, context)
                return
            except Exception as e:
                logger.error(f"خطأ في show_support_info: {e}")
                await query.answer("❌ حدث خطأ في عرض الدعم")
                return

        elif data == "show_terms_info":
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Member'))
                from Member.Menu import show_terms_info
                await show_terms_info(update, context)
                return
            except Exception as e:
                logger.error(f"خطأ في show_terms_info: {e}")
                await query.answer("❌ حدث خطأ في عرض الشروط")
                return

        # أضف هذا المعالج الجديد هنا
        elif data == "edit_terms_info":
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.InfoManager import edit_terms_info_handler
                await edit_terms_info_handler(update, context)
                return
            except Exception as e:
                logger.error(f"خطأ في edit_terms_info_handler: {e}")
                await query.answer("❌ حدث خطأ في تعديل الشروط")
                return

        # معالج زر إدارة المعلومات للمدير
        elif data == "info_manager_menu":
            try:
                context.user_data.pop('editing_text_type', None)
                context.user_data.pop('awaiting_', None)
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.InfoManager import info_manager_handler
                await info_manager_handler(update, context)
                return
            except Exception as e:
                logger.error(f"خطأ في info_manager_handler: {e}")
                await query.answer("❌ حدث خطأ في إدارة المعلومات")
                return

        # ✅ معالج زر إدارة المعلومات للمدير
        elif data == "info_manager_menu":
            try:
                context.user_data.pop('editing_text_type', None)
                context.user_data.pop('awaiting_', None)
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.InfoManager import info_manager_handler
                await info_manager_handler(update, context)
                return
            except Exception as e:
                logger.error(f"خطأ في info_manager_handler: {e}")
                await query.answer("❌ حدث خطأ في إدارة المعلومات")
                return
        
        # ✅ معالجات معلومات الحساب
        elif data == "account_info":
            try:
                context.user_data.pop('editing_text_type', None)
                context.user_data.pop('awaiting_', None)
                sys.path.insert(0, os.path.join(current_dir, 'Member'))
                from Member.Account import show_account_info
                await show_account_info(update, context)
                return
            except Exception as e:
                logger.error(f"خطأ في استيراد Account: {e}")
                await query.answer("❌ نظام الحساب غير متوفر")
                return
        
        # ✅ معالجات مهامي الجديدة
        elif data == "member_my_tasks":
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Member'))
                from Member.Tasks_View import view_my_tasks
                await view_my_tasks(update, context)
                return
            except Exception as e:
                logger.error(f"❌ خطأ في عرض مهامي: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return
            
        elif data.startswith("mytask_"):
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Member'))
                from Member.Tasks_View import show_my_task_details
                task_id = data.split("_")[1]
                await show_my_task_details(update, context, task_id)
                return
            except Exception as e:
                logger.error(f"❌ خطأ في عرض تفاصيل المهمة: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return
            
        elif data.startswith("delete_mytask_"):
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Member'))
                from Member.Tasks_View import delete_my_task
                task_id = data.split("_")[2]
                await delete_my_task(update, context, task_id)
                return
            except Exception as e:
                logger.error(f"❌ خطأ في حذف المهمة: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return
        
        # معالجات البحث
        elif data == "search_tasks":
            try:
                await query.edit_message_text(
                    "🔍 اكتب كود المهمة أو جزء من اسمها:",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="member_menu")]])
                )
                context.user_data['awaiting_search'] = True
                return
            except Exception as e:
                logger.error(f"❌ خطأ في البحث: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return
        
        # معالجات المهام - العرض والتصفح
        elif data in ["member_tasks_view", "back_to_task_types", 
                     "back_to_task_list"] or data.startswith("view_task_type_") or \
                     data.startswith("view_task_") or data in ["page_prev", "page_next"]:
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Member'))
                from Member.Tasks_View import tasks_view_handler
                await tasks_view_handler(update, context)
                return
            except Exception as e:
                logger.error(f"❌ خطأ في عرض المهام: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return
        
        # معالجات المهام - التنفيذ والإثباتات
        elif data.startswith("execute_task_") or data.startswith("cancel_execution_") or \
             data.startswith("accept_proof_") or data.startswith("reject_proof_") or \
             data == "send_proof_now":
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Member'))
                from Member.Tasks_Execution import tasks_execution_handler
                await tasks_execution_handler(update, context)
                return
            except Exception as e:
                logger.error(f"❌ خطأ في تنفيذ المهام: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return

        elif data.startswith("show_message:"):
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Member'))
                from Member.Menu import handle_custom_message_buttons
                await handle_custom_message_buttons(update, context)
                return
            except Exception as e:
                logger.error(f"❌ خطأ في عرض الرسالة: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return

        elif data == "cancel_add_task":
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Member'))
                from Member.AddTask import cancel_add_task
                await cancel_add_task(update, context)
                return
            except Exception as e:
                logger.error(f"❌ خطأ في إلغاء الإضافة: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return

        elif data == "show_help_message":
            try:
                sys.path.insert(0, os.path.join(current_dir, 'Member'))
                from Member.Menu import show_help_message
                await show_help_message(update, context)
                return
            except Exception as e:
                logger.error(f"❌ خطأ في عرض المساعدة: {e}")
                await query.answer("❌ حدث خطأ في المعالجة")
                return

        else:
            logger.warning(f"Callback query غير معروف: {data}")
            await query.edit_message_text("❌ الأمر غير معروف. استخدم /start للبدء.")
            return
        
    except Exception as e:
        logger.error(f"خطأ في معالجة callback query: {e}")
        await query.edit_message_text("❌ حدث خطأ في المعالجة. حاول مرة أخرى.")
        return

async def handle_protected_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE, button_id: str):
    """معالجة تلقائية لكل الأزرار المحمية"""
    try:
        protected_buttons = db.data["button_system"]["protected_buttons"]
        if button_id in protected_buttons:
            button_data = protected_buttons[button_id]
            
            if button_data.get("type") == "submenu":
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.ButtonManager import ButtonHandler
                await ButtonHandler.show_submenu_to_user(update, context, button_id)
            else:
                sys.path.insert(0, os.path.join(current_dir, 'Admin'))
                from Admin.ButtonManager import ButtonHandler
                await ButtonHandler.handle_custom_button(update, context, button_id)
            return True
        return False
    except Exception as e:
        logger.error(f"❌ خطأ في المعالجة التلقائية: {e}")
        return False

# Main.py - الجزء 3/3
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأخطاء العام المحدث"""
    try:
        logger.error(f"⚠️ حدث خطأ: {context.error}", exc_info=context.error)
        
        # تنظيف حالات الانتظار في حالة الخطأ
        if hasattr(context, 'user_data') and context.user_data:
            await cleanup_pending_states(context)
        
        # إرسال تقرير الخطأ للمالك
        if update and hasattr(update, 'effective_user'):
            error_info = await format_error_info(update, context)
            await send_error_report(context, error_info)
            
        # إرسال رسالة للمستخدم إذا كان الخطأ في محادثة
        if update and update.effective_chat:
            await send_user_error_message(update, context)
            
    except Exception as e:
        # إذا حدث خطأ في معالج الأخطاء نفسه
        logger.critical(f"💥 خطأ كارثي في معالج الأخطاء: {e}", exc_info=e)
        
    finally:
        # تنظيف نهائي لحالات الانتظار
        if hasattr(context, 'user_data') and context.user_data:
            await final_cleanup(context)

async def cleanup_pending_states(context: ContextTypes.DEFAULT_TYPE):
    """تنظيف حالات الانتظار"""
    try:
        pending_states = [
            # حالات الانتظار العامة
            'awaiting_task_search', 'awaiting_complaint', 'awaiting_search',
            'awaiting_gift_code', 'awaiting_admin_id', 'awaiting_remove_admin',
            'awaiting_block_id', 'awaiting_unblock_id', 'awaiting_tasks_channel',
            'awaiting_completed_channel', 'awaiting_gift_points', 'awaiting_gift_max_uses',
            'awaiting_gift_code', 'awaiting_gift_custom_code', 'awaiting_add_points',
            'awaiting_remove_points', 'awaiting_set_points', 'awaiting_send_all',
            'awaiting_broadcast', 'awaiting_channel', 'awaiting_profit_percentage',
            'awaiting_task_limits', 'awaiting_pin_price', 'awaiting_pin_duration',
            'awaiting_max_pins', 'awaiting_terms_edit',
            
            # حالات انتظار إدارة المعلومات
            'editing_text_type', 'editing_welcome_message', 'editing_terms_text',
            'editing_invite_message', 'editing_support_info', 'editing_terms_info',
            
            # حالات انتظار الأزرار
            'button_creation', 'submenu_button_creation', 'renaming_button',
            'changing_emoji', 'changing_content',
            
            # حالات انتظار سهم الحظ
            'awaiting_daily_limit', 'awaiting_invite_arrows', 'awaiting_invite_points',
            'awaiting_box_capacity', 'awaiting_give_arrows'
        ]
        
        for state in pending_states:
            context.user_data.pop(state, None)
            
        logger.info("🧹 تم تنظيف حالات الانتظار بسبب الخطأ")
        
    except Exception as e:
        logger.error(f"❌ خطأ في تنظيف الحالات: {e}")

async def format_error_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """تنسيق معلومات الخطأ"""
    try:
        error = context.error
        user = update.effective_user if update else None
        
        # معلومات الأساسية
        error_info = f"⚠️ **تقرير خطأ في البوت**\n\n"
        
        # معلومات المستخدم
        if user:
            error_info += f"👤 **المستخدم:** {user.first_name} (ID: {user.id})\n"
            if user.username:
                error_info += f"📎 @{user.username}\n"
        
        # نوع الخطأ
        error_info += f"🚨 **نوع الخطأ:** {type(error).__name__}\n"
        
        # رسالة الخطأ
        error_msg = str(error)
        if error_msg:
            error_info += f"📝 **الرسالة:** {error_msg[:200]}{'...' if len(error_msg) > 200 else ''}\n"
        
        # الوقت
        from datetime import datetime
        error_info += f"⏰ **الوقت:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        # معلومات إضافية
        if hasattr(update, 'callback_query') and update.callback_query:
            error_info += f"🎯 **Callback Data:** {update.callback_query.data}\n"
        
        elif hasattr(update, 'message') and update.message:
            error_info += f"💬 **نوع المحتوى:** {update.message.content_type}\n"
            if update.message.text:
                error_info += f"📋 **النص:** {update.message.text[:100]}{'...' if len(update.message.text) > 100 else ''}\n"
        
        return error_info
        
    except Exception as e:
        return f"❌ فشل في تنسيق معلومات الخطأ: {e}"

async def send_error_report(context: ContextTypes.DEFAULT_TYPE, error_info: str):
    """إرسال تقرير الخطأ للمالك"""
    try:
        from Config import OWNER_ID
        
        # تقطيع الرسالة إذا كانت طويلة
        if len(error_info) > 4000:
            error_info = error_info[:4000] + "..."
        
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=error_info,
            parse_mode='Markdown'
        )
        
        logger.info("📤 تم إرسال تقرير الخطأ للمالك")
        
    except Exception as e:
        logger.error(f"❌ فشل في إرسال تقرير الخطأ: {e}")

async def send_user_error_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إرسال رسالة خطأ للمستخدم"""
    try:
        error = context.error
        
        # تحديد رسالة الخطأ المناسبة
        error_message = "❌ حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى."
        
        if isinstance(error, TimeoutError):
            error_message = "⏰ انتهت مهلة الانتظار. يرجى المحاولة مرة أخرى."
        elif "blocked" in str(error).lower():
            error_message = "🔒无法发送消息给用户，可能是因为用户已阻止机器人。"
        elif "chat not found" in str(error).lower():
            error_message = "❌无法找到聊天，用户可能已删除聊天或阻止机器人。"
        elif "not enough rights" in str(error).lower():
            error_message = "🔐没有足够的权限执行此操作。"
        
        # إرسال الرسالة للمستخدم
        if hasattr(update, 'callback_query'):
            try:
                await update.callback_query.answer(error_message, show_alert=True)
            except:
                # إذا فشل إشعار الـ callback، حاول تعديل الرسالة
                try:
                    await update.callback_query.edit_message_text(
                        f"❌ {error_message}",
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 القائمة", callback_data="member_menu")]])
                    )
                except:
                    pass
                    
        elif hasattr(update, 'message'):
            await update.message.reply_text(
                error_message,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 القائمة", callback_data="member_menu")]])
            )
            
    except Exception as e:
        logger.error(f"❌ فشل في إرسال رسالة الخطأ للمستخدم: {e}")

async def final_cleanup(context: ContextTypes.DEFAULT_TYPE):
    """تنظيف نهائي"""
    try:
        # تنظيف أي بيانات مؤقتة
        temp_keys = [key for key in context.user_data.keys() if key.startswith('temp_')]
        for key in temp_keys:
            context.user_data.pop(key, None)
            
        # تنظيف مسار القوائم
        context.user_data.pop('menu_path', None)
        
    except Exception as e:
        logger.error(f"❌ خطأ في التنظيف النهائي: {e}")

def setup_error_handlers(application):
    """إعداد معالجات الأخطاء"""
    # معالج الأخطاء العام
    application.add_error_handler(error_handler)
    
    # معالجات أخطاء إضافية
    application.add_handler(MessageHandler(filters.ALL, handle_unexpected_messages))
    
    logger.info("✅ تم إعداد معالجات الأخطاء")

async def handle_unexpected_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل غير المتوقعة"""
    try:
        if update.message and update.message.text:
            # إذا كانت رسالة نصية غير متوقعة
            if update.message.text.startswith('/'):
                await update.message.reply_text(
                    "❌ الأمر غير معروف. استخدم /start للبدء.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🚀 البدء", callback_data="start")]])
                )
            else:
                # إذا كان المستخدم في منتصف عملية، تجاهل الرسالة
                has_pending_state = any(key in context.user_data for key in [
                    'awaiting_', 'editing_', 'button_'
                ])
                
                if not has_pending_state:
                    await update.message.reply_text(
                        "🤔 لم أفهم طلبك. استخدم /start لعرض القائمة.",
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📋 القائمة", callback_data="member_menu")]])
                    )
                    
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة الرسائل غير المتوقعة: {e}")

# استبدل الدالة main() الحالية بهذا الكود:
async def main_async():
    """الدالة الرئيسية لتشغيل البوت - محدثة بنظام سهم الحظ"""
    global application
    
    try:
        logger.info("🚀 بدء تشغيل البوت...")
        
        # إنشاء التطبيق
        application = Application.builder().token(BOT_TOKEN).build()
        
        # ✅ معالجة المهام المعلقة للنقل إلى القناة المنتهية
        try:
            class TemporaryContext:
                def __init__(self, bot):
                    self.bot = bot
            
            temp_context = TemporaryContext(application.bot)
            if hasattr(db, 'process_pending_task_moves'):
                db.process_pending_task_moves(temp_context)
            logger.info("✅ تم معالجة المهام المعلقة")
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة المهام المعلقة: {e}")
        
        # ✅ بدء أنظمة التنظيف التلقائي
        try:
            # نظام تنظيف الأسهم اليومي
            if hasattr(db, 'start_arrow_cleanup'):
                db.start_arrow_cleanup()
                logger.info("✅ بدأ نظام تنظيف الأسهم اليومي")
            
            # نظام تنظيف التثبيتات
            if hasattr(db, 'start_pin_cleanup'):
                db.start_pin_cleanup()
                logger.info("✅ بدأ نظام تنظيف التثبيتات")
            
            # نظام تنظيف الحجوزات
            if hasattr(db, 'start_reservation_cleanup'):
                db.start_reservation_cleanup()
                logger.info("✅ بدأ نظام تنظيف الحجوزات")
            
            # نظام التحقق من مهلات الإثباتات
            if hasattr(db, 'start_proof_timeout_checker'):
                db.start_proof_timeout_checker()
                logger.info("✅ بدأ نظام التحقق من مهلات الإثباتات")
            
        except Exception as e:
            logger.error(f"❌ خطأ في بدء أنظمة التنظيف: {e}")
        
        # ✅ إعداد معالجات الأخطاء
        try:
            setup_error_handlers(application)
            logger.info("✅ تم إعداد معالجات الأخطاء")
        except Exception as e:
            logger.error(f"❌ خطأ في إعداد معالجات الأخطاء: {e}")
        
        # ✅ إضافة معالجات الأوامر (التركيز على /start فقط)
        application.add_handler(CommandHandler("start", start))
        
        logger.info("✅ تم إضافة معالجات الأوامر")
        
        # ✅ معالجات Callback Query
        application.add_handler(CallbackQueryHandler(handle_callback_query))
        logger.info("✅ تم إضافة معالجات Callback Query")
        
        # ✅ معالجات الرسائل
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(MessageHandler(filters.PHOTO, handle_message))
        logger.info("✅ تم إضافة معالجات الرسائل")
        
        # ✅ معالج الأخطاء
        application.add_error_handler(error_handler)
        logger.info("✅ تم إضافة معالج الأخطاء")
        
        # ✅ التحقق من صحة البيانات
        try:
            if hasattr(db, 'validate_arrow_data'):
                data_issues = db.validate_arrow_data()
                if data_issues and len(data_issues) > 1:
                    logger.warning(f"⚠️ مشاكل في بيانات الأسهم: {data_issues}")
            
            # تنظيف بيانات الأسهم
            if hasattr(db, 'cleanup_arrow_data'):
                cleaned_count = db.cleanup_arrow_data()
                if cleaned_count > 0:
                    logger.info(f"🧹 تم تنظيف {cleaned_count} من بيانات الأسهم")
                
        except Exception as e:
            logger.error(f"❌ خطأ في التحقق من البيانات: {e}")
        
        # ✅ إرسال إشعار البدء للمالك
        try:
            from Config import OWNER_ID
            await application.bot.send_message(
                chat_id=OWNER_ID,
                text="✅ **تم تشغيل البوت بنجاح**\n\n"
                     f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                     f"🎯 نظام سهم الحظ: ✅ مفعل\n"
                     f"📊 المستخدمون: {len(db.data.get('users', {}))}\n"
                     f"🏹 الأسهم: {db.get_arrow_stats().get('total_arrows', 0) if hasattr(db, 'get_arrow_stats') else 0}",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"❌ خطأ في إرسال إشعار البدء: {e}")
        
        # ✅ بدء البوت
        logger.info("🎉 جاري بدء البوت...")
        await application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            timeout=30,
            connect_timeout=10,
            read_timeout=10,
            write_timeout=10
        )
        
    except Exception as e:
        logger.critical(f"💥 خطأ كارثي في تشغيل البوت: {e}", exc_info=e)

def main():
    """الدالة الرئيسية لتشغيل البوت"""
    global application
    
    try:
        # إنشاء التطبيق
        application = Application.builder().token(BOT_TOKEN).build()
        
        # ✅ معالجة المهام المعلقة للنقل إلى القناة المنتهية
        # ننشئ context مؤقت للمعالجة الأولية
        class TemporaryContext:
            def __init__(self, bot):
                self.bot = bot
        
        temp_context = TemporaryContext(application.bot)
        if hasattr(db, 'process_pending_task_moves'):
            db.process_pending_task_moves(temp_context)
        
        # إضافة معالجات الأوامر
        application.add_handler(CommandHandler("start", start))
        
        # معالجات Callback Query
        application.add_handler(CallbackQueryHandler(handle_callback_query))
        
        # معالجات الرسائل
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(MessageHandler(filters.PHOTO, handle_message))
        
        # معالج الأخطاء
        application.add_error_handler(error_handler)
        
        # بدء البوت
        logger.info("جاري تشغيل البوت...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"خطأ في تشغيل البوت: {e}")

if __name__ == "__main__":
    main()
