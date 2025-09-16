# Member/AddTask.py - مع نظام النسبة والحدود وميزات المستوى
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from Data import db
from Decorators import user_only
from LinkValidator import validate_task_link
import logging

logger = logging.getLogger(__name__)

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

# حالة المحادثة (بدون استخدام ConversationHandler)
TASK_STATES = {}

@user_only
async def start_add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء عملية إضافة مهمة جديدة"""
    user_id = update.effective_user.id
    TASK_STATES[user_id] = {'step': 'choosing_type'}
    
    keyboard = [
        [InlineKeyboardButton("📱 تليجرام", callback_data="addtask_telegram")],
        [InlineKeyboardButton("📱 واتساب", callback_data="addtask_whatsapp")],
        [InlineKeyboardButton("📷 انستجرام", callback_data="addtask_instagram")],
        [InlineKeyboardButton("👥 فيسبوك", callback_data="addtask_facebook")],
        [InlineKeyboardButton("🎬 يوتيوب", callback_data="addtask_youtube")],
        [InlineKeyboardButton("🎵 تيك توك", callback_data="addtask_tiktok")],
        [InlineKeyboardButton("🌐 موقع ويب", callback_data="addtask_website")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="member_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.edit_message_text(
            "📋 اختر نوع المهمة:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "📋 اختر نوع المهمة:",
            reply_markup=reply_markup
        )

@user_only
async def choose_task_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اختيار نوع المهمة"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    task_type = query.data.replace("addtask_", "")
    
    TASK_STATES[user_id] = {
        'step': 'task_name',
        'task_data': {
            'type': task_type,
            'name': None,
            'description': None,
            'photo': None,
            'count': None,
            'price': None,
            'link': None,
            'proof': None,
            'total_cost': 0
        }
    }
    
    # عرض حدود المهمة للمستخدم
    task_limits = db.data.get("task_limits", {})
    limits_message = ""
    if task_type in task_limits:
        limits = task_limits[task_type]
        limits_message = f"\n📊 الحدود المسموحة: من {limits['min']} إلى {limits['max']} نقطة"
    
    await query.edit_message_text(
        f"✅ اخترت {task_type}{limits_message}\n\n📝 أرسل اسم المهمة:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 إلغاء", callback_data="cancel_add_task")]])
    )

@user_only
async def handle_task_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة رسائل إضافة المهمة"""
    user_id = update.effective_user.id
    
    if user_id not in TASK_STATES:
        return False  # ليس في حالة إضافة مهمة
    
    state = TASK_STATES[user_id]
    task_data = state['task_data']
    
    try:
        if state['step'] == 'task_name':
            task_data['name'] = update.message.text
            state['step'] = 'task_desc'
            await update.message.reply_text(
                "📋 أرسل وصف المهمة (يمكنك إرفاق صورة):",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 إلغاء", callback_data="cancel_add_task")]])
            )
            return True
            
        elif state['step'] == 'task_desc':
            if update.message.photo:
                task_data['description'] = update.message.caption or "بدون وصف"
                task_data['photo'] = update.message.photo[-1].file_id
            else:
                task_data['description'] = update.message.text
                task_data['photo'] = None
            
            state['step'] = 'task_count'
            await update.message.reply_text(
                "👥 أرسل عدد الأشخاص المطلوبين للتنفيذ:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 إلغاء", callback_data="cancel_add_task")]])
            )
            return True
            
        elif state['step'] == 'task_count':
            try:
                count = int(update.message.text)
                if count <= 0:
                    await update.message.reply_text("❌ يجب أن يكون العدد أكبر من الصفر")
                    return True
                if count > 1000:
                    await update.message.reply_text("❌ الحد الأقصى للمنفذين هو 1000")
                    return True
                
                task_data['count'] = count
                state['step'] = 'task_price'
                
                await update.message.reply_text(
                    f"👥 تم تحديد {count} منفذ\n\n💰 أرسل سعر المهمة لكل منفذ (بالنقاط):",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 إلغاء", callback_data="cancel_add_task")]])
                )
                return True
            except ValueError:
                await update.message.reply_text("❌ يجب إدخال رقم صحيح")
                return True
            
        elif state['step'] == 'task_price':
            try:
                price = int(update.message.text)
        
                # ✅ التحقق من حدود المهمة
                task_limits = db.data.get("task_limits", {})
                task_type = task_data['type']
        
                if task_type in task_limits:
                    limits = task_limits[task_type]
                    if price < limits['min']:
                        await update.message.reply_text(
                            f"❌ السعر أقل من المسموح!\n"
                            f"📊 الحد الأدنى لـ {task_type}: {limits['min']} نقطة\n\n"
                            f"💰 أرسل سعر المهمة ضمن الحدود المسموحة:",
                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 إلغاء", callback_data="cancel_add_task")]])
                        )
                        return True
                    if price > limits['max']:
                        await update.message.reply_text(
                            f"❌ السعر أعلى من المسموح!\n"
                            f"📊 الحد الأقصى لـ {task_type}: {limits['max']} نقطة\n\n"
                            f"💰 أرسل سعر المهمة ضمن الحدود المسموحة:",
                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 إلغاء", callback_data="cancel_add_task")]])
                        )
                        return True
        
                # ✅ تطبيق خصم المستوى هنا - الإصلاح
                discount = get_user_discount(user_id)
                original_price = price
                discounted_price = price
                discount_amount_per_unit = 0  # ✅ تهيئة المتغير أولاً

                if discount > 0:
                    discount_amount_per_unit = original_price * discount / 100  # استخدام القسمة العادية
                    discounted_price = original_price - discount_amount_per_unit
         
               # حفظ السعر المخفض
                task_data['price'] = discounted_price
                task_data['original_price'] = original_price
                task_data['discount'] = discount
                task_data['discount_amount_per_unit'] = discount_amount_per_unit if discount > 0 else 0
        
                discount_message = f"\n🎯 خصم {discount}%: -{discount_amount_per_unit:.1f} نقطة للواحد" if discount > 0 else ""
        
                await update.message.reply_text(
                    f"💰 تم تحديد السعر: {original_price} نقطة{discount_message}\n"
                    f"💎 السعر بعد الخصم: {discounted_price:.1f} نقطة لكل منفذ\n\n"
                    f"🔗 أرسل رابط المهمة:",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 إلغاء", callback_data="cancel_add_task")]])
                )
         
                state['step'] = 'task_link'
                return True
        
            except ValueError:
                await update.message.reply_text("❌ يجب إدخال رقم صحيح")
                return True
            
        elif state['step'] == 'task_link':
            task_data['link'] = update.message.text
            
            # ✅ التحقق من صحة الرابط
            is_valid, message = validate_task_link(task_data['link'], task_data['type'])
            if not is_valid:
                await update.message.reply_text(
                    f"{message}\n\n📝 يرجى إرسال رابط صحيح:",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 إلغاء", callback_data="cancel_add_task")]])
                )
                return True
            
            state['step'] = 'task_proof'
            await update.message.reply_text(
                "📝 أرسل متطلبات الإثبات (ما يجب على المنفذ تقديمه):",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 إلغاء", callback_data="cancel_add_task")]])
            )
            return True

        elif state['step'] == 'task_proof':
            task_data['proof'] = update.message.text
    
            # حساب التكلفة الإجمالية مع الخصم
            total_cost = task_data['count'] * task_data['price']
    
            # حساب نسبة الربح
            profit_percentage = db.data.get("profit_percentage", 15)
            profit_amount = total_cost * profit_percentage / 100
            total_with_profit = total_cost + profit_amount
    
            task_data['total_cost'] = total_with_profit
    
            user_points = db.get_user_points(user_id)
    
            # التحقق من رصيد النقاط
            if user_points < total_with_profit:
                await update.message.reply_text(
                    f"❌ نقاطك غير كافية!\n"
                    f"💳 نقاطك الحالية: {user_points}\n"
                    f"💰 التكلفة الإجمالية: {total_with_profit:.1f} نقطة\n\n"
                    f"📝 تحتاج إلى {total_with_profit - user_points:.1f} نقطة إضافية",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="member_menu")]])
                )
                del TASK_STATES[user_id]
                return True
    
            # إضافة المهمة إلى قاعدة البيانات
            success, task_id = db.add_task(
                user_id, task_data['type'], task_data['name'], task_data['description'],
                task_data['photo'], task_data['count'], task_data['price'],
                task_data['link'], task_data['proof']
            )
    
            if success:
                # خصم النقاط (بما في ذلك نسبة الربح)
                db.remove_points_from_user(user_id, total_with_profit)
        
                # إرسال المهمة إلى القناة
                try:
                    from Admin.TasksChannels import send_task_to_channel
                    task = db.get_task(task_id)
                    await send_task_to_channel(task, context)
                except Exception as e:
                    logger.error(f"خطأ في إرسال المهمة للقناة: {e}")
                    # نستمر حتى لو فشل الإرسال للقناة
        
                # رسالة النجاح مع تفاصيل الخصم - الإصلاح هنا
                discount = task_data.get('discount', 0)
                original_price = task_data.get('original_price', task_data['price'])
                discount_amount_per_unit = task_data.get('discount_amount_per_unit', 0)
                total_discount_amount = discount_amount_per_unit * task_data['count'] if discount > 0 else 0
        
                message = f"""
        ✅ **تم إضافة المهمة بنجاح!**

        📊 كود المهمة: #{db.get_task(task_id).get('code', '')}
        📝 النوع: {task_data['type']}
        👥 العدد: {task_data['count']} منفذ
        💰 السعر الأصلي: {original_price} نقطة للواحد
        🎯 خصم {discount}%: -{discount_amount_per_unit:.1f} نقطة للواحد
        💎 السعر النهائي: {task_data['price']:.1f} نقطة للواحد
        📈 التكلفة الأساسية: {total_cost:.1f} نقطة
        🏆 نسبة الأرباح: +{profit_amount:.1f} نقطة
        💳 المبلغ المخصوم: {total_with_profit:.1f} نقطة
        🔢 رصيدك الجديد: {user_points - total_with_profit:.1f} نقطة

        🚀 تم إرسال المهمة إلى قناة المهام المتاحة
        """
        
                await update.message.reply_text(
                    message,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📋 مهامي", callback_data="member_my_tasks")]]),
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    "❌ حدث خطأ في إضافة المهمة. يرجى المحاولة مرة أخرى.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="member_menu")]])
                )
    
            # مسح حالة المحادثة
            del TASK_STATES[user_id]
            return True
            
    except Exception as e:
        logger.error(f"خطأ في معالجة إضافة المهمة: {e}")
        await update.message.reply_text(
            "❌ حدث خطأ غير متوقع في إضافة المهمة",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="member_menu")]])
        )
        if user_id in TASK_STATES:
            del TASK_STATES[user_id]
        return True
    
    return False

@user_only
async def cancel_add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إلغاء عملية إضافة المهمة"""
    user_id = update.effective_user.id
    
    if user_id in TASK_STATES:
        del TASK_STATES[user_id]
    
    if hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.answer("✅ تم إلغاء إضافة المهمة")
        from Member.Menu import show_member_menu
        await show_member_menu(update, context)
    else:
        await update.message.reply_text("✅ تم إلغاء إضافة المهمة")

# معالج الاستعلامات
def get_add_task_handlers():
    return [
        CallbackQueryHandler(start_add_task, pattern="^show_task_types$"),
        CallbackQueryHandler(choose_task_type, pattern="^addtask_"),
        CallbackQueryHandler(cancel_add_task, pattern="^cancel_add_task$")
    ]

# دالة مساعدة للحصول على سعر نوع المهمة
def get_task_type_price(task_type):
    """الحصول على السعر الافتراضي لنوع المهمة"""
    task_limits = db.data.get("task_limits", {})
    if task_type in task_limits:
        return task_limits[task_type]['max']
    return 10  # سعر افتراضي

# معالج لرسائل إضافة المهمة
async def handle_task_creation_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة رسائل إنشاء المهمة مع تطبيق خصم المستوى"""
    try:
        user_id = update.effective_user.id
        
        if user_id not in TASK_STATES:
            return False
            
        state = TASK_STATES[user_id]
        
        if state['step'] == 'awaiting_description':
            # معالجة وصف المهمة
            task_data = state['task_data']
            
            if update.message.photo:
                task_data['description'] = update.message.caption or "بدون وصف"
                task_data['photo'] = update.message.photo[-1].file_id
            else:
                task_data['description'] = update.message.text
                task_data['photo'] = None
            
            state['step'] = 'awaiting_count'
            await update.message.reply_text(
                "👥 أرسل عدد الأشخاص المطلوبين للتنفيذ:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 إلغاء", callback_data="cancel_add_task")]])
            )
            return True
            
        elif state['step'] == 'awaiting_count':
            # معالجة عدد المنفذين
            try:
                count = int(update.message.text)
                if count <= 0:
                    await update.message.reply_text("❌ يجب أن يكون العدد أكبر من الصفر")
                    return True
                if count > 1000:
                    await update.message.reply_text("❌ الحد الأقصى للمنفذين هو 1000")
                    return True
                
                state['task_data']['count'] = count
                state['step'] = 'awaiting_price_confirmation'
                
                # حساب التكلفة الإجمالية مع الخصم
                discounted_price = context.user_data.get('task_price', 10)
                total_cost = count * discounted_price
                
                # حساب نسبة الربح
                profit_percentage = db.data.get("profit_percentage", 15)
                profit_amount = total_cost * profit_percentage / 100
                total_with_profit = total_cost + profit_amount
                
                state['task_data']['total_cost'] = total_with_profit
                state['task_data']['price'] = discounted_price
                
                await update.message.reply_text(
                    f"💰 **التكلفة الإجمالية بعد الخصم**\n\n"
                    f"👥 عدد المنفذين: {count}\n"
                    f"💎 سعر الوحدة: {discounted_price} نقطة\n"
                    f"📊 التكلفة الأساسية: {total_cost} نقطة\n"
                    f"📈 نسبة الأرباح ({profit_percentage}%): +{profit_amount:.1f} نقطة\n"
                    f"💳 المبلغ الإجمالي: {total_with_profit:.1f} نقطة\n\n"
                    f"🔗 أرسل رابط المهمة:",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 إلغاء", callback_data="cancel_add_task")]]),
                    parse_mode='Markdown'
                )
                return True
                
            except ValueError:
                await update.message.reply_text("❌ يجب إدخال رقم صحيح")
                return True
                
        elif state['step'] == 'awaiting_link':
            # معالجة رابط المهمة
            task_data = state['task_data']
            task_data['link'] = update.message.text
            
            # التحقق من صحة الرابط
            is_valid, message = validate_task_link(task_data['link'], task_data['type'])
            if not is_valid:
                await update.message.reply_text(
                    f"{message}\n\n📝 يرجى إرسال رابط صحيح:",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 إلغاء", callback_data="cancel_add_task")]])
                )
                return True
            
            state['step'] = 'awaiting_proof'
            await update.message.reply_text(
                "📝 أرسل متطلبات الإثبات (ما يجب على المنفذ تقديمه):",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 إلغاء", callback_data="cancel_add_task")]])
            )
            return True
            
        elif state['step'] == 'awaiting_proof':
            # معالجة متطلبات الإثبات
            task_data = state['task_data']
            task_data['proof'] = update.message.text
            
            # التحقق من الرصيد النهائي
            total_with_profit = task_data['total_cost']
            user_points = db.get_user_points(user_id)
            
            if user_points < total_with_profit:
                await update.message.reply_text(
                    f"❌ نقاطك غير كافية!\n"
                    f"💳 نقاطك الحالية: {user_points}\n"
                    f"💰 التكلفة الإجمالية: {total_with_profit:.1f} نقطة\n\n"
                    f"📝 تحتاج إلى {total_with_profit - user_points:.1f} نقطة إضافية",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="member_menu")]])
                )
                del TASK_STATES[user_id]
                return True
            
            # إضافة المهمة إلى قاعدة البيانات - الإصلاح هنا
            success, task_id = db.add_task(
                user_id, 
                task_data['type'], 
                task_data['name'], 
                task_data['description'],
                task_data['photo'], 
                task_data['count'], 
                task_data['price'],
                task_data['link'], 
                task_data['proof']
            )
            
            if success:
                # خصم النقاط (بما في ذلك نسبة الربح)
                db.remove_points_from_user(user_id, total_with_profit)
                
                # إرسال المهمة إلى القناة
                try:
                    from Admin.TasksChannels import send_task_to_channel
                    task = db.get_task(task_id)
                    await send_task_to_channel(task, context)
                except Exception as e:
                    logger.error(f"خطأ في إرسال المهمة للقناة: {e}")
                    # نستمر حتى لو فشل الإرسال للقناة
                
                # إرسال رسالة النجاح مع تفاصيل الخصم
                discount = context.user_data.get('task_discount', 0)
                original_price = context.user_data.get('task_original_price', 0)
                discount_amount = (original_price - task_data['price']) * task_data['count'] if discount > 0 else 0
                
                message = f"""
✅ **تم إضافة المهمة بنجاح!**

📊 كود المهمة: #{db.get_task(task_id).get('code', '')}
📝 النوع: {task_data['type']}
👥 العدد: {task_data['count']} منفذ
💰 السعر الأصلي: {original_price} نقطة
🎯 خصم {discount}%: -{discount_amount} نقطة
💎 السعر النهائي: {task_data['price']} نقطة لكل منفذ
📈 التكلفة الإجمالية: {total_cost:.1f} نقطة
🏆 نسبة الأرباح: +{profit_amount:.1f} نقطة
💳 المبلغ المخصوم: {total_with_profit:.1f} نقطة
🔢 رصيدك الجديد: {user_points - total_with_profit:.1f} نقطة

🚀 تم إرسال المهمة إلى قناة المهام المتاحة
"""
                
                await update.message.reply_text(
                    message,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📋 مهامي", callback_data="member_my_tasks")]]),
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    "❌ حدث خطأ في إضافة المهمة. يرجى المحاولة مرة أخرى.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="member_menu")]])
                )
            
            # مسح حالة المحادثة
            del TASK_STATES[user_id]
            if 'task_price' in context.user_data:
                del context.user_data['task_price']
            if 'task_discount' in context.user_data:
                del context.user_data['task_discount']
            if 'task_original_price' in context.user_data:
                del context.user_data['task_original_price']
                
            return True
            
    except Exception as e:
        logger.error(f"خطأ في معالجة إنشاء المهمة: {e}")
        await update.message.reply_text(
            "❌ حدث خطأ غير متوقع في إنشاء المهمة",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="member_menu")]])
        )
        if user_id in TASK_STATES:
            del TASK_STATES[user_id]
        return True
    
    return False

# دالة لبدء عملية إضافة المهمة مع الخصم
@user_only
async def start_task_with_discount(update: Update, context: ContextTypes.DEFAULT_TYPE, task_type: str):
    """بدء عملية إضافة مهمة مع تطبيق خصم المستوى"""
    try:
        user_id = update.effective_user.id
        
        TASK_STATES[user_id] = {
            'step': 'awaiting_description',
            'task_data': {
                'type': task_type,
                'name': context.user_data.get('task_name', ''),
                'description': None,
                'photo': None,
                'count': None,
                'price': None,
                'link': None,
                'proof': None,
                'total_cost': 0
            }
        }
        
        # حساب الخصم والسعر
        discount = get_user_discount(user_id)
        original_price = get_task_type_price(task_type)
        discounted_price = original_price
        
        if discount > 0:
            discount_amount_per_unit = original_price * discount / 100
            discounted_price = original_price - discount_amount
        
        # حفظ بيانات السعر
        context.user_data['task_price'] = discounted_price
        context.user_data['task_discount'] = discount
        context.user_data['task_original_price'] = original_price
        
        # الحصول على اسم المستوى
        level_name = db.get_user_level_name(user_id)
        
        discount_message = f"\n🎯 خصم {discount}%: -{discount_amount} نقطة" if discount > 0 else ""
        
        message = f"""
💰 **إضافة مهمة جديدة مع الخصم**

📝 نوع المهمة: {task_type}
🏷️ السعر الأصلي: {original_price} نقطة
{discount_message}
💎 السعر بعد الخصم: {discounted_price} نقطة
🎯 مستواك: {level_name}

📝 أرسل وصف المهمة:
"""
        
        await update.callback_query.edit_message_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"خطأ في بدء المهمة مع الخصم: {e}")
        await update.callback_query.answer("❌ حدث خطأ في المعالجة")

# معالج الاستعلامات المحدث
def get_add_task_handlers():
    """الحصول على معالجات إضافة المهمة"""
    return [
        CallbackQueryHandler(start_add_task, pattern="^show_task_types$"),
        CallbackQueryHandler(choose_task_type, pattern="^addtask_"),
        CallbackQueryHandler(cancel_add_task, pattern="^cancel_add_task$"),
        CallbackQueryHandler(start_task_with_discount, pattern="^start_task_")
    ]

# تصدير الدوال اللازمة
__all__ = [
    'start_add_task',
    'choose_task_type', 
    'handle_task_message',
    'cancel_add_task',
    'handle_task_price',
    'get_add_task_handlers',
    'handle_task_creation_message',
    'start_task_with_discount'
]

