# Member/Menu.py - الإصدار المحدث بالكامل
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from Data import db
from Decorators import user_only
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@user_only
async def show_member_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض قائمة العضو الرئيسية مع الأزرار الديناميكية"""
    try:
        user_id = update.effective_user.id
        
        # إنشاء لوحة المفاتيح الديناميكية
        keyboard = create_dynamic_keyboard(user_id)
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # رسالة الترحيب
        welcome_message = get_welcome_message(user_id)
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(
                welcome_message, 
                reply_markup=reply_markup, 
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                welcome_message, 
                reply_markup=reply_markup, 
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"خطأ في show_member_menu: {e}")
        error_message = "❌ حدث خطأ في تحميل القائمة. يرجى المحاولة مرة أخرى."
        try:
            if hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.edit_message_text(error_message)
            else:
                await update.message.reply_text(error_message)
        except:
            pass

def create_dynamic_keyboard(user_id):
    """إنشاء لوحة مفاتيح ديناميكية مع الأزرار الأساسية والمخصصة"""
    try:
        # الأزرار الأساسية المحمية
        protected_buttons = db.data["button_system"]["protected_buttons"]
        base_buttons = []
        
        # ✅ ترتيب الأزرار حسب الـ position
        protected_list = sorted(protected_buttons.items(), key=lambda x: x[1]["position"])
        
        # ✅ فصل الأزرار إلى مجموعات حسب الترتيب المطلوب
        row1_buttons = []  # البحث + الإضافة
        row2_buttons = []  # مهامي + عرض المهام  
        row3_buttons = []  # سهم الحظ (لوحده)
        row4_buttons = []  # نقاطي + رابط الدعوة
        row5_buttons = []  # مستواي
        
        for btn_id, btn_data in protected_list:
            emoji = btn_data.get("emoji", "") + " " if btn_data.get("emoji") else ""
            button = InlineKeyboardButton(f"{emoji}{btn_data['name']}", callback_data=btn_id)
            
            # ✅ توزيع الأزرار على الصفوف حسب الموقع
            if btn_id == "search_tasks" or btn_id == "show_task_types":
                row1_buttons.append(button)  # الصف الأول: البحث + الإضافة
            elif btn_id == "member_my_tasks" or btn_id == "member_tasks_view":
                row2_buttons.append(button)  # الصف الثاني: مهامي + عرض المهام
            elif btn_id == "member_luck_arrow":
                row3_buttons.append(button)  # الصف الثالث: سهم الحظ (لوحده)
            elif btn_id == "member_invite_points" or btn_id == "member_invite_link":
                row4_buttons.append(button)  # الصف الرابع: نقاطي + رابط الدعوة
            elif btn_id == "member_level_info":
                row5_buttons.append(button)  # الصف الخامس: مستواي  (لوحده)        

        # ✅ بناء الصفوف بالترتيب المطلوب
        if row1_buttons:
            base_buttons.append(row1_buttons)
        
        if row2_buttons:
            base_buttons.append(row2_buttons)
        
        if row3_buttons:
            base_buttons.append(row3_buttons)  # سهم الحظ في سطر لوحده
        
        if row4_buttons:
            base_buttons.append(row4_buttons)
        
        if row5_buttons:
            base_buttons.append(row5_buttons)
        
        # ✅ إضافة الأزرار المخصصة في صفوف مزدوجة (كل زرين في سطر)
        custom_buttons = sorted(db.data["button_system"]["main_menu_buttons"], key=lambda x: x["position"])
        
        # تجميع الأزرار المخصصة في صفوف مزدوجة
        custom_rows = []
        current_row = []
        
        for i, btn in enumerate(custom_buttons):
            emoji = btn.get("emoji", "") + " " if btn.get("emoji") else ""
            callback_data = f"custom_btn_{btn['id']}"
            button = InlineKeyboardButton(f"{emoji}{btn['name']}", callback_data=callback_data)
            
            current_row.append(button)
            
            # إذا كان لدينا زرين في الصف أو انتهت القائمة
            if len(current_row) == 2 or i == len(custom_buttons) - 1:
                custom_rows.append(current_row)
                current_row = []
        
        # إضافة الأزرار المخصصة إلى القائمة الرئيسية
        base_buttons.extend(custom_rows)
        
        return base_buttons
        
    except Exception as e:
        logger.error(f"خطأ في create_dynamic_keyboard: {e}")
        # لوحة مفاتيح افتراضية في حالة الخطأ
        return [
            [
                InlineKeyboardButton("🔍 بحث سريع", callback_data="search_tasks"),
                InlineKeyboardButton("➕ إضافة مهمة", callback_data="show_task_types")
            ],
            [
                InlineKeyboardButton("📊 مهامي", callback_data="member_my_tasks"),
                InlineKeyboardButton("📋 عرض المهام", callback_data="member_tasks_view")
            ],
            [
                InlineKeyboardButton("🎯 سهم الحظ", callback_data="member_luck_arrow")
            ],
            [
                InlineKeyboardButton("💰 نقاطي", callback_data="member_invite_points"),
                InlineKeyboardButton("📨 رابط الدعوة", callback_data="member_invite_link")
            ],
            [
                InlineKeyboardButton("🏆مستواي", callback_data="member_level_info")
            ]
        ]

def get_welcome_message(user_id):
    """الحصول على رسالة ترحيب مخصصة"""
    try:
        user_data = db.get_user(user_id)
        welcome_text = db.data.get("welcome_message", "🎊 مرحباً بك في بوت المهام!")
        
        # تنسيق النص مع المتغيرات الديناميكية
        variables = {
            '{user_id}': str(user_id),
            '{user_name}': '',  # سيتم ملؤه لاحقاً
            '{points}': user_data.get("points", 0),
            '{level_name}': db.get_user_level_name(user_id),
            '{active_tasks}': len([t for t in db.get_user_tasks(user_id) if t.get("status") == "active"]),
            '{current_date}': datetime.now().strftime("%Y-%m-%d"),
            '{total_earned}': user_data.get("total_earned", 0),
            '{invites_count}': len(user_data.get("invited_users", []))
        }
        
        for var, value in variables.items():
            welcome_text = welcome_text.replace(var, str(value))
            
        return welcome_text
        
    except Exception as e:
        logger.error(f"خطأ في get_welcome_message: {e}")
        return "🎊 مرحباً بك في بوت المهام!\n\n👤 اختر من القائمة:"

@user_only
async def member_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج قائمة العضو"""
    await show_member_menu(update, context)

@user_only
async def show_task_types(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض أنواع المهام المتاحة للإضافة"""
    try:
        message = """
🎯 **اختر نوع المهمة التي تريد إضافتها:**

📝 سيتم خصم النقاط من رصيدك حسب سعر المهمة
        """
        
        keyboard = [
            [
                InlineKeyboardButton("📱 تليجرام", callback_data="addtask_telegram"),
                InlineKeyboardButton("💚 واتساب", callback_data="addtask_whatsapp")
            ],
            [
                InlineKeyboardButton("📷 انستجرام", callback_data="addtask_instagram"),
                InlineKeyboardButton("👥 فيسبوك", callback_data="addtask_facebook")
            ],
            [
                InlineKeyboardButton("🎬 يوتيوب", callback_data="addtask_youtube"),
                InlineKeyboardButton("🎵 تيك توك", callback_data="addtask_tiktok")
            ],
            [
                InlineKeyboardButton("🌐 موقع ويب", callback_data="addtask_website"),
                InlineKeyboardButton("🔙 رجوع", callback_data="member_menu")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            message, 
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"خطأ في show_task_types: {e}")
        await update.callback_query.answer("❌ حدث خطأ في المعالجة")

@user_only
async def send_welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إرسال رسالة ترحيبية جميلة"""
    try:
        user_id = update.effective_user.id
        welcome_message = get_welcome_message(user_id)
        
        keyboard = create_dynamic_keyboard(user_id)
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"خطأ في send_welcome_message: {e}")
        await update.message.reply_text(
            "🎉 **مرحباً بك في بوت المهام!**\n\n📋 اختر من القائمة:",
            reply_markup=InlineKeyboardMarkup(create_dynamic_keyboard(update.effective_user.id))
        )

@user_only
async def show_support_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض معلومات الدعم"""
    try:
        user_id = update.effective_user.id
        user_data = db.get_user(user_id)
        support_text = db.data.get("support_info", "📞 للاستفسارات والمساعدة: @E8EOE")
        
        # تنسيق النص مع المتغيرات
        formatted_text = support_text.replace("{user_id}", str(user_id))
        formatted_text = formatted_text.replace("{points}", str(user_data.get("points", 0)))
        
        keyboard = [
            [InlineKeyboardButton("🔙 رجوع", callback_data="member_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            formatted_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"خطأ في show_support_info: {e}")
        await update.callback_query.answer("❌ حدث خطأ في عرض الدعم")

@user_only
async def show_terms_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض شروط الاستخدام"""
    try:
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name or "المستخدم"
        terms_text = db.data.get("terms_info", "📜 الشروط والأحكام")
        
        # تنسيق النص مع المتغيرات
        formatted_text = terms_text.replace("{user_name}", user_name)
        formatted_text = formatted_text.replace("{user_id}", str(user_id))
        formatted_text = formatted_text.replace("{current_date}", datetime.now().strftime("%Y-%m-%d"))
        
        keyboard = [
            [InlineKeyboardButton("🔙 رجوع", callback_data="member_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            formatted_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"خطأ في show_terms_info: {e}")
        await update.callback_query.answer("❌ حدث خطأ في عرض الشروط")

@user_only
async def show_user_guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض دليل الاستخدام"""
    try:
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name or "المستخدم"
        user_data = db.get_user(user_id)
        guide_text = db.data.get("user_guide_text", "📖 دليل الاستخدام")
        
        # تنسيق النص مع المتغيرات
        formatted_text = guide_text.replace("{user_name}", user_name)
        formatted_text = formatted_text.replace("{points}", str(user_data.get("points", 0)))
        formatted_text = formatted_text.replace("{level_name}", db.get_user_level_name(user_id))
        
        keyboard = [
            [InlineKeyboardButton("🔙 رجوع", callback_data="member_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            formatted_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"خطأ في show_user_guide: {e}")
        await update.callback_query.answer("❌ حدث خطأ في عرض الدليل")

@user_only
async def show_exchange_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض معلومات استبدال النقاط"""
    try:
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name or "المستخدم"
        user_data = db.get_user(user_id)
        exchange_text = db.data.get("exchange_text", "💱 استبدال النقاط")
        
        # تنسيق النص مع المتغيرات
        formatted_text = exchange_text.replace("{user_name}", user_name)
        formatted_text = formatted_text.replace("{points}", str(user_data.get("points", 0)))
        formatted_text = formatted_text.replace("{user_id}", str(user_id))
        
        keyboard = [
            [InlineKeyboardButton("🔙 رجوع", callback_data="member_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            formatted_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"خطأ في show_exchange_points: {e}")
        await update.callback_query.answer("❌ حدث خطأ في عرض الاستبدال")

@user_only
async def show_help_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض رسالة المساعدة"""
    try:
        help_message = """
🤖 **دليل استخدام البوت:**

📋 **عرض المهام:** تصفح المهام المتاحة للتنفيذ
➕ **إضافة مهمة:** أنشئ مهمة جديدة بكسب النقاط
💰 **نقاطي:** تحقق من رصيدك وإحصائياتك
🎁 **كود هدية:** استخدم أكواد الهدايا لكسب نقاط إضافية
📨 **رابط الدعوة:** ادعُ أصدقاءك واحصل على مكافآت
🏆 **مستواي:** تتبع تقدمك في نظام المستويات

💡 للمساعدة: @E8EOE
        """
        
        keyboard = [
            [InlineKeyboardButton("🔙 رجوع", callback_data="member_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            help_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"خطأ في show_help_message: {e}")
        await update.callback_query.answer("❌ حدث خطأ في عرض المساعدة")

@user_only
async def show_member_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض قائمة العضو الرئيسية مع الأزرار الديناميكية"""
    try:
        # تنظيف مسار القوائم عند العودة إلى الرئيسية
        if 'menu_path' in context.user_data:
            context.user_data['menu_path'] = []
        
        user_id = update.effective_user.id
        
        # إنشاء لوحة المفاتيح الديناميكية
        keyboard = create_dynamic_keyboard(user_id)
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # رسالة الترحيب
        welcome_message = get_welcome_message(user_id)
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(
                welcome_message, 
                reply_markup=reply_markup, 
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                welcome_message, 
                reply_markup=reply_markup, 
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"خطأ في show_member_menu: {e}")
        error_message = "❌ حدث خطأ في تحميل القائمة. يرجى المحاولة مرة أخرى."
        try:
            if hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.edit_message_text(error_message)
            else:
                await update.message.reply_text(error_message)
        except:
            pass


@user_only
async def handle_custom_message_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة أزرار الرسائل المخصصة"""
    try:
        query = update.callback_query
        data = query.data
        
        if data.startswith("show_message:"):
            message_type = data.split(":")[1]
            
            if message_type == "support":
                await show_support_info(update, context)
            elif message_type == "terms":
                await show_terms_info(update, context)
            elif message_type == "guide":
                await show_user_guide(update, context)
            elif message_type == "exchange":
                await show_exchange_points(update, context)
            elif message_type == "help":
                await show_help_message(update, context)
                
    except Exception as e:
        logger.error(f"خطأ في handle_custom_message_buttons: {e}")
        await update.callback_query.answer("❌ حدث خطأ في المعالجة")

def get_member_handlers():
    """الحصول على معالجات العضو"""
    return [
        CallbackQueryHandler(show_support_info, pattern="^show_support_info$"),
        CallbackQueryHandler(show_terms_info, pattern="^show_terms_info$"),
        CallbackQueryHandler(show_user_guide, pattern="^user_guide$"),
        CallbackQueryHandler(show_exchange_points, pattern="^exchange_points$"),
        CallbackQueryHandler(member_menu_handler, pattern="^member_menu$"),
        CallbackQueryHandler(show_task_types, pattern="^show_task_types$"),
        CallbackQueryHandler(show_help_message, pattern="^show_help_message$"),
        CallbackQueryHandler(handle_custom_message_buttons, pattern="^show_message:")
    ]