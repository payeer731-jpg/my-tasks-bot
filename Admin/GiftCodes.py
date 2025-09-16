# Admin/GiftCodes.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from Data import db
from Decorators import owner_only
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@owner_only
async def gift_codes_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أوامر أكواد الهدايا"""
    try:
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "gift_codes_menu":
            await gift_codes_menu(update, context)
        elif data == "gift_code_create":
            await create_gift_code_prompt(update, context)
        elif data == "gift_code_list":
            await list_gift_codes(update, context)
        elif data.startswith("view_gift_code_"):
            code = data.split("_")[3]
            await view_gift_code_details(update, context, code)
        elif data.startswith("use_auto_code_"):
            code = data.split("_")[3]
            await use_auto_code(update, context, code)
        elif data == "enter_custom_code":
            await enter_custom_code(update, context)
        else:
            await query.answer("❌ أمر غير معروف")
            
    except Exception as e:
        logger.error(f"❌ خطأ في gift_codes_handler: {e}")
        await update.callback_query.answer("❌ حدث خطأ في المعالجة")

@owner_only
async def gift_codes_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض قائمة إدارة أكواد الهدايا"""
    try:
        message = """
🎁 **إدارة أكواد الهدايا**

اختر الإجراء المطلوب:
"""
        
        keyboard = [
            [InlineKeyboardButton("➕ إنشاء كود هدية", callback_data="gift_code_create")],
            [InlineKeyboardButton("📋 قائمة الأكواد", callback_data="gift_code_list")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"❌ خطأ في gift_codes_menu: {e}")
        await update.callback_query.answer("❌ حدث خطأ في عرض القائمة")

@owner_only
async def create_gift_code_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مطالبة بإنشاء كود هدية جديد"""
    try:
        await update.callback_query.edit_message_text(
            "💰 أرسل عدد النقاط التي تريد منحها في هذا الكود:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="gift_codes_menu")]])
        )
        context.user_data['awaiting_gift_points'] = True
        
    except Exception as e:
        logger.error(f"❌ خطأ في create_gift_code_prompt: {e}")
        await update.callback_query.answer("❌ حدث خطأ في المعالجة")

@owner_only
async def list_gift_codes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض قائمة أكواد الهدايا"""
    try:
        gift_codes = db.get_all_gift_codes()
        
        if not gift_codes:
            message = "📭 لا توجد أكواد هدايا حالياً"
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="gift_codes_menu")]]
        else:
            message = "📋 **قائمة أكواد الهدايا:**\n\n"
            keyboard = []
            
            for code, data in gift_codes.items():
                status = "✅ نشط" if data['used_count'] < data['max_uses'] else "❌ منتهي"
                message += f"• `{code}`: {data['points']} نقاط ({data['used_count']}/{data['max_uses']}) - {status}\n"
                
                keyboard.append([InlineKeyboardButton(f"📝 {code}", callback_data=f"view_gift_code_{code}")])
            
            keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="gift_codes_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"❌ خطأ في list_gift_codes: {e}")
        await update.callback_query.answer("❌ حدث خطأ في عرض القائمة")

@owner_only
async def view_gift_code_details(update: Update, context: ContextTypes.DEFAULT_TYPE, code):
    """عرض تفاصيل كود هدية معين"""
    try:
        gift_code = db.get_gift_code(code)
        
        if not gift_code:
            await update.callback_query.answer("❌ الكود غير موجود")
            return
        
        message = f"""
🎯 **تفاصيل كود الهدية:** `{code}`

💰 **القيمة:** {gift_code['points']} نقطة
👥 **المستخدمون:** {gift_code['used_count']}/{gift_code['max_uses']}
⏰ **تاريخ الإنشاء:** {gift_code['created_at']}

📊 **المستخدمون الذين استخدموا الكود:**
"""
        
        if gift_code['used_by']:
            for user_id in gift_code['used_by']:
                message += f"• {user_id}\n"
        else:
            message += "📭 لم يستخدمه أي مستخدم بعد"
        
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="gift_code_list")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"❌ خطأ في view_gift_code_details: {e}")
        await update.callback_query.answer("❌ حدث خطأ في عرض التفاصيل")

@owner_only
async def use_auto_code(update: Update, context: ContextTypes.DEFAULT_TYPE, code):
    """استخدام الكود التلقائي الذي تم إنشاؤه"""
    try:
        gift_data = context.user_data.get('gift_data', {})
        
        # إضافة الكود إلى قاعدة البيانات
        code_data = {
            'code': code,
            'points': gift_data['points'],
            'max_uses': gift_data['max_uses'],
            'used_count': 0,
            'used_by': [],
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'created_by': update.effective_user.id
        }
        
        if db.add_gift_code(code_data):
            await update.callback_query.edit_message_text(
                f"✅ تم إنشاء كود الهدية بنجاح!\n\n"
                f"🎯 الكود: `{code}`\n"
                f"💰 القيمة: {gift_data['points']} نقطة\n"
                f"👥 عدد المستخدمين: {gift_data['max_uses']}\n\n"
                f"📝 يمكن للمستخدمين استخدامه من خلال زر '🎁 كود هدية'",
                parse_mode='Markdown'
            )
        else:
            await update.callback_query.answer("❌ حدث خطأ في إنشاء الكود")
            
        # مسح البيانات المؤقتة
        context.user_data.pop('gift_data', None)
        context.user_data.pop('awaiting_gift_code', None)
        
    except Exception as e:
        logger.error(f"❌ خطأ في use_auto_code: {e}")
        await update.callback_query.answer("❌ حدث خطأ في إنشاء الكود")

@owner_only
async def enter_custom_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الانتقال إلى وضع إدخال كود مخصص"""
    try:
        await update.callback_query.edit_message_text(
            "📝 أرسل الكود المخصص الذي تريد استخدامه:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="gift_codes_menu")]])
        )
        context.user_data['awaiting_gift_custom_code'] = True
        
    except Exception as e:
        logger.error(f"❌ خطأ في enter_custom_code: {e}")
        await update.callback_query.answer("❌ حدث خطأ في المعالجة")

# دالة مساعدة للاستخدام في Admin/Menu.py
async def handle_gift_code_creation(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """معالجة إنشاء أكواد الهدايا من الرسائل النصية"""
    try:
        if context.user_data.get('awaiting_gift_custom_code'):
            custom_code = text.strip().upper()
            if not custom_code:
                await update.message.reply_text("❌ يجب إدخال كود صحيح")
                return
                
            # التحقق من أن الكود غير مستخدم
            if db.get_gift_code(custom_code):
                await update.message.reply_text("❌ هذا الكود مستخدم مسبقاً، اختر كوداً آخر")
                return
                
            gift_data = context.user_data.get('gift_data', {})
            gift_data['code'] = custom_code
            
            # إضافة الكود إلى قاعدة البيانات
            code_data = {
                'code': custom_code,
                'points': gift_data['points'],
                'max_uses': gift_data['max_uses'],
                'used_count': 0,
                'used_by': [],
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'created_by': update.effective_user.id
            }
            
            if db.add_gift_code(code_data):
                await update.message.reply_text(
                    f"✅ تم إنشاء كود الهدية بنجاح!\n\n"
                    f"🎯 الكود: `{custom_code}`\n"
                    f"💰 القيمة: {gift_data['points']} نقطة\n"
                    f"👥 عدد المستخدمين: {gift_data['max_uses']}",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text("❌ حدث خطأ في إنشاء الكود")
                
            # مسح البيانات المؤقتة
            context.user_data.pop('gift_data', None)
            context.user_data.pop('awaiting_gift_custom_code', None)
            
    except Exception as e:
        logger.error(f"❌ خطأ في handle_gift_code_creation: {e}")
        await update.message.reply_text("❌ حدث خطأ في إنشاء الكود")