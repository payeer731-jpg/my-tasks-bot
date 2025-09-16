# Member/Terms.py - الملف الكامل المعدل
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from Data import db
from Decorators import user_only
from datetime import datetime

logger = logging.getLogger(__name__)

@user_only
async def show_terms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض شروط الاستخدام للمستخدم"""
    try:
        user_id = update.effective_user.id
        
        # التحقق إذا كان المستخدم قد قبل الشروط مسبقاً
        if str(user_id) in db.data.get("accepted_terms_users", []):
            return True
        
        terms_text = db.data.get("terms_text", 
            "📜 **شروط وأحكام استخدام البوت**\n\n"
            "باستخدامك لهذا البوت، فإنك توافق على الالتزام بالشروط التالية:\n\n"
            "1. الالتزام بالأدب والاحترام في التعامل\n"
            "2. عدم نشر محتوى غير أخلاقي أو مسيء\n"
            "3. عدم استخدام البوت لأغراض غير قانونية\n"
            "4. الإدارة تحتفظ بالحق في حظر أي مستخدم يخالف الشروط\n"
            "5. النقاط غير قابلة للاسترداد أو التحويل بين الحسابات\n"
        )
        
        keyboard = [
            [InlineKeyboardButton("✅ أوافق على الشروط", callback_data="accept_terms")],
            [InlineKeyboardButton("❌ لا أوافق", callback_data="reject_terms")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(update, 'message') and update.message:
            await update.message.reply_text(terms_text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.callback_query.edit_message_text(terms_text, reply_markup=reply_markup, parse_mode='Markdown')
        
        return False
        
    except Exception as e:
        logger.error(f"خطأ في show_terms: {e}")
        return True

@user_only
async def terms_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة قبول/رفض الشروط"""
    try:
        query = update.callback_query
        data = query.data
        user_id = update.effective_user.id
        
        if data == "accept_terms":
            # إضافة المستخدم إلى قائمة المقبولين
            if "accepted_terms_users" not in db.data:
                db.data["accepted_terms_users"] = []
            
            if str(user_id) not in db.data["accepted_terms_users"]:
                db.data["accepted_terms_users"].append(str(user_id))
            
            # معالجة الدعوة إذا كان هناك رابط دعوة
            referrer_id = None
            if "pending_invites" in db.data and str(user_id) in db.data["pending_invites"]:
                referral_data = db.data["pending_invites"][str(user_id)]
                referrer_id = referral_data.get("referral_id")
                
                if referrer_id and referrer_id != str(user_id):
                    # معالجة الدعوة
                    success, message = await process_invite_usage(referrer_id, user_id, context)
                    
                    if success:
                        logger.info(f"✅ تم منح النقاط للمدعي {referrer_id} لدعوة {user_id}")
                        
                        # إرسال إشعار للمدعي
                        try:
                            # الحصول على اسم المدعو
                            try:
                                user_chat = await context.bot.get_chat(user_id)
                                invited_name = user_chat.first_name or f"المستخدم {user_id}"
                            except:
                                invited_name = f"المستخدم {user_id}"
                            
                            # الحصول على إعدادات الأسهم
                            invite_points = db.get_invite_points()
                            luck_settings = db.get_luck_arrow_settings()
                            invite_arrows = luck_settings.get("invite_arrows", 1)
                            
                            await context.bot.send_message(
                                chat_id=int(referrer_id),
                                text=f"🎉 **🎉 تهانينا! مستخدم جديد استخدم رمز الإحالة الخاص بك!**\n\n"
                                     f"👤 المستخدم {invited_name} !\n"
                                     f"💰 حصلت على {invite_points} نقطة في حسابك\n"
                                     f"🏹 حصلت على {invite_arrows} سهم حظ في حسابك\n\n"
                                     f"🎯 تابع دعوة المزيد لزيادة نقاطك وأسهمك!",
                                parse_mode='Markdown'
                            )
                            
                        except Exception as e:
                            logger.error(f"⚠️ خطأ في إرسال الإشعارات: {e}")
                    
                    # حذف الدعوة المعلقة
                    del db.data["pending_invites"][str(user_id)]
            
            db.save_data()
            
            # عرض رسالة القبول
            await query.edit_message_text(
                "✅ **تم قبول الشروط بنجاح!**\n\n"
                "🎉 يمكنك الآن استخدام جميع ميزات البوت.\n"
                "💰 ابدأ بكسب النقاط عبر تنفيذ المهام!",
                parse_mode='Markdown'
            )
            
            # عرض القائمة الرئيسية بعد بضع ثوان
            await asyncio.sleep(2)
            from Member.Menu import show_member_menu
            await show_member_menu(update, context)
            
        elif data == "reject_terms":
            await query.edit_message_text(
                "❌ **لم توافق على الشروط**\n\n"
                "عذراً، لا يمكنك استخدام البوت بدون الموافقة على الشروط والأحكام.\n\n"
                "إذا غيرت رأيك، يمكنك استخدام /start للعودة وإعادة النظر في الشروط.",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة الشروط: {e}")
        await query.answer("❌ حدث خطأ في المعالجة")

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
        invite_points = db.get_invite_points()
        
        # ✅ الحصول على إعدادات سهم الحظ
        luck_settings = db.get_luck_arrow_settings()
        invite_arrows = luck_settings.get("invite_arrows", 1)
        
        logger.info(f"💰 محاولة منح {invite_points} نقطة و{invite_arrows} سهم للمدعي {referrer_id}")
        
        # الحصول على نقاط المدعي الحالية قبل الإضافة
        current_points = referrer.get('points', 0)
        
        # ✅ حفظ المستوى القديم قبل الإضافة
        old_level = db.get_user_level(referrer_id)
        
        # منح النقاط
        success = db.add_points_to_user(referrer_id, invite_points)
        
        # منح الأسهم (سهم الحظ)
        arrow_success = False
        if success and invite_arrows > 0:
            arrow_success = db.add_arrows_to_user(referrer_id, invite_arrows)
            if not arrow_success:
                logger.error(f"❌ فشل في منح الأسهم للمدعي {referrer_id}")
        
        if success:
            new_points = db.get_user_points(referrer_id)
            logger.info(f"✅ تم منح النقاط والأسهم بنجاح: {referrer_id} ({current_points} → {new_points}) + {invite_arrows} سهم")
            
            # ✅ التحقق من الترقية
            new_level = db.get_user_level(referrer_id)
            if new_level != old_level:
                db.add_user_stat(referrer_id, "level_ups", 1)
                logger.info(f"🎉 المستخدم {referrer_id} ارتقى إلى مستوى جديد بسبب الدعوة")
                
                # إرسال رسالة الترقية إذا كان context متاحاً
                if context:
                    level_info = db.get_level_info(new_level)
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