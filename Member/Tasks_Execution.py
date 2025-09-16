#[file name]: Member/Tasks_Execution.py
#[file content begin]
# Member/Tasks_Execution.py - ملف تنفيذ المهام والإثباتات
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from Data import db
from Decorators import user_only
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@user_only
async def tasks_execution_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج تنفيذ المهام"""
    query = update.callback_query
    data = query.data
    
    logger.info(f"تم استقبال بيانات التنفيذ: {data} من المستخدم: {update.effective_user.id}")
    
    if data.startswith("execute_task_"):
        task_id = data.split("_")[2]
        await start_task_execution(update, context, task_id)
    elif data.startswith("cancel_execution_"):
        reservation_id = data.split("_")[2]
        await cancel_task_execution(update, context, reservation_id)
    elif data.startswith("accept_proof_") or data.startswith("reject_proof_"):
        await handle_proof_review(update, context)
    elif data == "send_proof_now":
        await update.callback_query.answer("📤 يمكنك إرسال الإثبات الآن")
    else:
        logger.warning(f"حدث غير معروف في التنفيذ: {data}")
        await query.answer("⚠️ الأمر غير معروف")

@user_only
async def start_task_execution(update: Update, context: ContextTypes.DEFAULT_TYPE, task_id):
    """بدء تنفيذ المهمة مع الحجز - رسالة جديدة"""
    try:
        user_id = update.effective_user.id
        task = db.get_task(task_id)
        
        if not task:
            await update.callback_query.answer("❌ المهمة غير موجودة")
            return
        
        # محاولة حجز المهمة
        success, result = db.reserve_task(user_id, task_id)
        
        if not success:
            await update.callback_query.answer(f"❌ {result}")
            return
        
        reservation_id = result
        context.user_data['executing_task'] = task_id
        context.user_data['execution_step'] = 'awaiting_proof'
        context.user_data['reservation_id'] = reservation_id
        
        # حساب وقت الانتهاء
        expiry_time = (datetime.now() + timedelta(minutes=20)).strftime("%H:%M:%S")
        
        message = f"""
🚀 **بدء تنفيذ المهمة: {task.get('name', 'بدون اسم')}**

⏰ **مهلة التنفيذ:** حتى الساعة {expiry_time}
📝 **متطلبات الإثبات:** {task.get('proof', 'بدون متطلبات')}

⚠️ **تحذير:** إذا لم ترسل الإثبات خلال 20 دقيقة:
• سيتم حظرك من هذه المهمة لمدة 24 ساعة
• سيتم خصم 10 نقاط من رصيدك
        """
        
        keyboard = [
            [InlineKeyboardButton("📤 إرسال الإثبات الآن", callback_data="send_proof_now")],
            [InlineKeyboardButton("❌ إلغاء التنفيذ", callback_data=f"cancel_execution_{reservation_id}")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # إرسال رسالة جديدة بدلاً من تعديل الرسالة الحالية
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        # الإبقاء على رسالة تفاصيل المهمة كما هي
        await update.callback_query.answer("✅ تم بدء التنفيذ - افحص الرسائل الجديدة")
            
    except Exception as e:
        logger.error(f"خطأ في start_task_execution: {e}")
        await update.callback_query.answer("❌ حدث خطأ في بدء تنفيذ المهمة")

@user_only
async def cancel_task_execution(update: Update, context: ContextTypes.DEFAULT_TYPE, reservation_id):
    """إلغاء تنفيذ المهمة"""
    try:
        user_id = update.effective_user.id
        
        success, message = db.cancel_reservation(reservation_id, user_id)
        
        if success:
            # مسح بيانات التنفيذ من context
            context.user_data.pop('executing_task', None)
            context.user_data.pop('execution_step', None)
            context.user_data.pop('reservation_id', None)
            
            await update.callback_query.answer("✅ تم إلغاء التنفيذ بنجاح")
            
            # حذف رسالة التنفيذ إذا أردت، أو تركها كسجل
            try:
                await update.callback_query.message.delete()
            except:
                pass
            
        else:
            await update.callback_query.answer(f"❌ {message}")
            
    except Exception as e:
        logger.error(f"خطأ في cancel_task_execution: {e}")
        await update.callback_query.answer("❌ حدث خطأ في إلغاء التنفيذ")

@user_only
async def handle_proof_submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة إرسال الإثبات"""
    try:
        if 'executing_task' not in context.user_data:
            return
        
        task_id = context.user_data['executing_task']
        user_id = update.effective_user.id
        reservation_id = context.user_data.get('reservation_id')
        
        task = db.get_task(task_id)
        if not task:
            await update.message.reply_text("❌ المهمة غير موجودة")
            return
        
        # جمع بيانات الإثبات
        proof_text = ""
        proof_photo = None
        
        if update.message.text:
            proof_text = update.message.text
        elif update.message.caption:
            proof_text = update.message.caption
            if update.message.photo:
                proof_photo = update.message.photo[-1].file_id
        elif update.message.photo:
            proof_text = "إثبات بصورة"
            proof_photo = update.message.photo[-1].file_id
        else:
            await update.message.reply_text("❌ يجب إرسال نص أو صورة كإثبات")
            return
        
        # إضافة الإثبات إلى قاعدة البيانات
        success, proof_id = db.add_proof(task_id, user_id, proof_text, proof_photo)
        
        if success:
            # تعيين مهلة للإثبات (12 ساعة)
            db.set_proof_timeout(proof_id, 12)
            
            # إكمال الحجز
            if reservation_id:
                db.complete_reservation(reservation_id, proof_id)
            
            owner_id = task.get('owner_id')
            message = f"""
📩 **إثبات جديد للمهمة: {task.get('name', 'بدون اسم')}**

👤 **المنفذ:** {user_id}
📝 **الإثبات:** {proof_text}
🎯 **رقم الإثبات:** {proof_id}
⏰ **مهلة المراجعة:** 12 ساعة

⚠️ **إذا لم يتم المراجعة خلال 12 ساعة:**
• سيتم قبول الإثبات تلقائياً
• سيتم منح النقاط للمنفذ
            """
            
            keyboard = [
                [InlineKeyboardButton("✅ قبول", callback_data=f"accept_proof_{proof_id}")],
                [InlineKeyboardButton("❌ رفض", callback_data=f"reject_proof_{proof_id}")]
            ]
            
            if proof_photo:
                await context.bot.send_photo(
                    chat_id=owner_id,
                    photo=proof_photo,
                    caption=message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
            else:
                await context.bot.send_message(
                    chat_id=owner_id,
                    text=message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
            
            # إرسال تأكيد للمنفذ
            confirmation = f"""
✅ **تم إرسال إثباتك بنجاح!**

🏷️ **المهمة:** {task.get('name', 'غير معروف')}
🎯 **رقم الإثبات:** {proof_id}
⏰ **مهلة المراجعة:** 12 ساعة

📋 سيتم مراجعة الإثبات من قبل صاحب المهمة
🔔 إذا لم تتم المراجعة خلال 12 ساعة، سيتم القبول تلقائياً
            """
            
            await update.message.reply_text(confirmation, parse_mode='Markdown')
            
        else:
            await update.message.reply_text("❌ حدث خطأ في إرسال الإثبات")
        
        # مسح حالة التنفيذ
        context.user_data.pop('executing_task', None)
        context.user_data.pop('execution_step', None)
        context.user_data.pop('reservation_id', None)
            
    except Exception as e:
        logger.error(f"خطأ في handle_proof_submission: {e}")
        await update.message.reply_text("❌ حدث خطأ في معالجة الإثبات")

@user_only
async def handle_proof_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مراجعة الإثبات"""
    try:
        logger.info(f"🎯 بدء معالجة مراجعة الإثبات")
        logger.info(f"👤 المستخدم: {update.effective_user.id}")
        logger.info(f"📋 البيانات: {update.callback_query.data}")
        
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        # ✅ تسجيل معلومات context
        logger.info(f"🔍 نوع context: {type(context)}")
        logger.info(f"🔍 context يحتوي على bot: {hasattr(context, 'bot')}")
        if hasattr(context, 'bot'):
            logger.info(f"🤖 bot ID: {context.bot.id}")
        
        if data.startswith("accept_proof_"):
            status = "accepted"
            action_text = "قبول"
            emoji = "✅"
            proof_id = data.replace("accept_proof_", "")
            logger.info(f"✅ قبول الإثبات: {proof_id}")
        elif data.startswith("reject_proof_"):
            status = "rejected" 
            action_text = "رفض"
            emoji = "❌"
            proof_id = data.replace("reject_proof_", "")
            logger.info(f"❌ رفض الإثبات: {proof_id}")
        else:
            logger.warning(f"⚠️ أمر غير معروف: {data}")
            await query.answer("❌ أمر غير معروف")
            return
        
        proof = None
        for p in db.data["proofs"]:
            if str(p.get("id")) == proof_id:
                proof = p
                break
        
        if not proof:
            logger.error(f"❌ الإثبات غير موجود: {proof_id}")
            await query.answer("❌ الإثبات غير موجود")
            return
        
        task_id = proof.get("task_id")
        executor_id = proof.get("executor_id")
        task = db.get_task(task_id)
        
        if not task:
            logger.error(f"❌ المهمة غير موجودة: {task_id}")
            await query.answer("❌ المهمة غير موجودة")
            return
        
        if str(update.effective_user.id) != task.get('owner_id'):
            logger.warning(f"⚠️ مستخدم غير مصرح: {update.effective_user.id} حاول مراجعة مهمة: {task_id}")
            await query.answer("❌ فقط صاحب المهمة يمكنه المراجعة")
            return
        
        logger.info(f"📊 معلومات المهمة: {task_id}")
        logger.info(f"👤 المنفذ: {executor_id}")
        logger.info(f"📈 المكتمل: {task.get('completed_count', 0)}/{task.get('count', 0)}")
        
        # ✅ تمرير context بشكل صحيح
        logger.info(f"🔧 استدعاء update_proof_status مع context...")
        success = db.update_proof_status(proof_id, status, update.effective_user.id, context)
        
        if success:
            logger.info(f"✅ تم {action_text} الإثبات بنجاح")
            await query.answer(f"{emoji} تم {action_text} الإثبات")
            
            task_name = task.get('name', 'غير معروف')
            task_price = task.get('price', 0)
            
            if status == "accepted":
                notification = f"{emoji} **تم قبول إثباتك للمهمة:** {task_name} - {task_price} نقطة"
                logger.info(f"💰 منح {task_price} نقطة للمنفذ: {executor_id}")
            else:
                notification = f"{emoji} **تم رفض إثباتك للمهمة:** {task_name}"
                logger.info(f"❌ تم رفض إثبات المنفذ: {executor_id}")
            
            try:
                await context.bot.send_message(chat_id=executor_id, text=notification, parse_mode='Markdown')
                logger.info(f"📨 تم إرسال الإشعار للمنفذ: {executor_id}")
            except Exception as e:
                logger.error(f"❌ خطأ في إرسال الإشعار للمنفذ: {e}")
            
            review_message = f"{query.message.text}\n\n{emoji} **تم {action_text} الإثبات**"
            await query.edit_message_text(review_message, reply_markup=None, parse_mode='Markdown')
            logger.info(f"📝 تم تحديث رسالة المراجعة")
            
        else:
            logger.error(f"❌ فشل في معالجة الإثبات: {proof_id}")
            await query.answer("❌ حدث خطأ في معالجة الإثبات")
            
    except Exception as e:
        logger.error(f"❌ خطأ في handle_proof_review: {e}")
        logger.error(f"❌ تفاصيل الخطأ: {str(e)}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        
        try:
            await query.answer("❌ حدث خطأ في المعالجة")
        except:
            pass