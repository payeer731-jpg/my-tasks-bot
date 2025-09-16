# Member/Tasks_View.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from Data import db
from Decorators import user_only
import logging

logger = logging.getLogger(__name__)

# تعريف أنواع المهام وأسمائها المعروضة
TASK_TYPES = {
    "telegram": "📱 تليجرام",
    "whatsapp": "📱 واتساب", 
    "instagram": "📷 انستجرام",
    "facebook": "👥 فيسبوك",
    "youtube": "🎬 يوتيوب",
    "tiktok": "🎵 تيك توك",
    "website": "🌐 موقع ويب",
    "all": "🌐 جميع المهام"
}

def get_type_emoji(task_type):
    """الحصول على إيموجي لنوع المهمة"""
    emoji_map = {
        "telegram": "📱",
        "whatsapp": "💚", 
        "instagram": "📷",
        "facebook": "👥",
        "youtube": "🎬",
        "tiktok": "🎵",
        "website": "🌐"
    }
    return emoji_map.get(task_type, "📋")

def get_progress_emoji(completion_percentage):
    """الحصول على إيموجي حسب نسبة الإكمال"""
    if completion_percentage >= 80:
        return "🟢"  # أخضر - قريب من الانتهاء
    elif completion_percentage >= 50:
        return "🟡"  # أصفر - متوسطة
    else:
        return "🔴"  # أحمر - جديدة

@user_only
async def tasks_view_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج عرض المهام"""
    query = update.callback_query
    data = query.data
    
    logger.info(f"تم استقبال بيانات العرض: {data} من المستخدم: {update.effective_user.id}")
    
    if data == "member_tasks_view":
        await show_task_types_menu(update, context)
    elif data.startswith("view_task_type_"):
        task_type = data.split("_")[3]
        context.user_data["current_task_page"] = 0
        await view_tasks_by_type(update, context, task_type)
    elif data == "back_to_task_types":
        await show_task_types_menu(update, context)
    elif data.startswith("view_task_"):
        task_id = data.split("_")[2]
        await view_task_details(update, context, task_id)
    elif data == "back_to_task_list":
        task_type = context.user_data.get("current_task_type", "all")
        await view_tasks_by_type(update, context, task_type)
    elif data == "member_my_tasks":
        await view_my_tasks(update, context)
    elif data.startswith("mytask_"):
        task_id = data.split("_")[1]
        await show_my_task_details(update, context, task_id)
    elif data.startswith("delete_mytask_"):
        task_id = data.split("_")[2]
        await delete_my_task(update, context, task_id)
    elif data in ["page_prev", "page_next"]:
        await handle_page_navigation(update, context)
    elif data.startswith("pin_task_"):
        task_id = data.split("_")[2]
        await pin_task(update, context, task_id)
    elif data.startswith("unpin_task_"):
        task_id = data.split("_")[2]
        await unpin_task(update, context, task_id)
    else:
        logger.warning(f"حدث غير معروف في العرض: {data}")
        await query.answer("⚠️ الأمر غير معروف")

@user_only
async def show_task_types_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض قائمة أنواع المهام للمستخدم بشكل أفقي"""
    try:
        keyboard = []
        
        # ✅ إضافة أزرار أنواع المهام في صفوف أفقية (مهمتين في كل صف)
        task_types = list(TASK_TYPES.items())
        
        # تقسيم أنواع المهام إلى أزواج
        for i in range(0, len(task_types), 2):
            row = []
            # الزر الأول في الصف
            if i < len(task_types):
                task_key, task_name = task_types[i]
                row.append(InlineKeyboardButton(task_name, callback_data=f"view_task_type_{task_key}"))
            
            # الزر الثاني في الصف (إذا موجود)
            if i + 1 < len(task_types):
                task_key, task_name = task_types[i + 1]
                row.append(InlineKeyboardButton(task_name, callback_data=f"view_task_type_{task_key}"))
            
            if row:
                keyboard.append(row)
        
        # ✅ أزرار التنقل في أسفل القائمة
        keyboard.append([InlineKeyboardButton("📋 مهامي", callback_data="member_my_tasks")])
        keyboard.append([InlineKeyboardButton("🔍 بحث في المهام", callback_data="search_tasks")])
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="member_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = "📋 اختر نوع المهام التي ترغب في تنفيذها:"
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup)
            
    except Exception as e:
        logger.error(f"خطأ في show_task_types_menu: {e}")
        await update.callback_query.answer("❌ حدث خطأ في المعالجة")

@user_only
async def view_tasks_by_type(update: Update, context: ContextTypes.DEFAULT_TYPE, task_type):
    """عرض المهام حسب النوع المحدد"""
    try:
        user_id = update.effective_user.id
        context.user_data["current_task_type"] = task_type
        
        # جلب المهام من النظام الجديد
        tasks = db.get_tasks_by_type(task_type)
        current_page = context.user_data.get("current_task_page", 0)
        tasks_per_page = 10
        
        type_name = TASK_TYPES.get(task_type, "جميع المهام")
        total_pages = max(1, (len(tasks) + tasks_per_page - 1) // tasks_per_page)
        
        if not tasks:
            message = f"📭 لا توجد مهام متاحة لنوع {type_name} حالياً.\n\n🚀 كن أول من ينشئ مهمة جديدة!"
        else:
            message = f"📋 {type_name} - الصفحة {current_page + 1}\n\n"
        
        keyboard = []
        
        # تقسيم المهام إلى أزواج (صفوف تحتوي على زرين)
        start_idx = current_page * tasks_per_page
        end_idx = start_idx + tasks_per_page
        current_tasks = tasks[start_idx:end_idx]
        
        for i in range(0, len(current_tasks), 2):
            row = []
            # الزر الأول في الصف
            if i < len(current_tasks):
                task1 = current_tasks[i]
                task1_name = task1.get('name', 'بدون اسم')
                if len(task1_name) > 12:
                    task1_name = task1_name[:9] + "..."
                
                # حساب نسبة الإكمال
                completion = (task1.get('completed_count', 0) / task1.get('count', 1)) * 100
                progress_emoji = get_progress_emoji(completion)
                
                # ✅ الإصلاح: إظهار اسم المهمة فقط بدون ID
                btn_text = f"{progress_emoji} {task1_name}"
                row.append(InlineKeyboardButton(btn_text, callback_data=f"view_task_{task1['id']}"))
            
            # الزر الثاني في الصف (إذا موجود)
            if i + 1 < len(current_tasks):
                task2 = current_tasks[i + 1]
                task2_name = task2.get('name', 'بدون اسم')
                if len(task2_name) > 12:
                    task2_name = task2_name[:9] + "..."
                
                completion = (task2.get('completed_count', 0) / task2.get('count', 1)) * 100
                progress_emoji = get_progress_emoji(completion)
                
                # ✅ الإصلاح: إظهار اسم المهمة فقط بدون ID
                btn_text = f"{progress_emoji} {task2_name}"
                row.append(InlineKeyboardButton(btn_text, callback_data=f"view_task_{task2['id']}"))
            
            if row:  # فقط أضف الصف إذا كان يحتوي على أزرار
                keyboard.append(row)
        
        # أزرار التنقل بين الصفحات
        nav_buttons = []
        if current_page > 0:
            nav_buttons.append(InlineKeyboardButton("◀️ السابق", callback_data="page_prev"))
        if current_page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("التالي ▶️", callback_data="page_next"))
        
        if nav_buttons:  # فقط أضف أزرار التنقل إذا كانت موجودة
            keyboard.append(nav_buttons)
        
        # زر الرجوع
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="back_to_task_types")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup)
            
    except Exception as e:
        logger.error(f"خطأ في view_tasks_by_type: {e}")
        error_msg = "❌ حدث خطأ في تحميل المهام. حاول مرة أخرى لاحقاً."
        await update.callback_query.edit_message_text(error_msg)

@user_only
async def handle_page_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة التنقل بين صفحات المهام"""
    try:
        query = update.callback_query
        data = query.data
        
        current_page = context.user_data.get("current_task_page", 0)
        task_type = context.user_data.get("current_task_type", "all")
        tasks = db.get_tasks_by_type(task_type)
        tasks_per_page = 10
        total_pages = max(1, (len(tasks) + tasks_per_page - 1) // tasks_per_page)
        
        if data == "page_next":
            current_page = min(current_page + 1, total_pages - 1)
        elif data == "page_prev":
            current_page = max(0, current_page - 1)
        
        context.user_data["current_task_page"] = current_page
        
        # إعادة تحميل المهام مع الصفحة الجديدة
        await view_tasks_by_type(update, context, task_type)
        
    except Exception as e:
        logger.error(f"خطأ في handle_page_navigation: {e}")
        await query.answer("❌ حدث خطأ في التنقل بين الصفحات")

# Member/Tasks_View.py - الإصلاح

@user_only
async def view_task_details(update: Update, context: ContextTypes.DEFAULT_TYPE, task_id):
    """عرض تفاصيل المهمة"""
    try:
        task = db.get_task(task_id)
        
        if not task:
            await update.callback_query.answer("❌ المهمة غير موجودة")
            return
        
        user_id = update.effective_user.id
        remaining = task.get('count', 0) - task.get('completed_count', 0)
        
        # استخدام تنسيق HTML بدلاً من Markdown
        message = f"""
🎯 <b>تفاصيل المهمة</b>

🆔 <b>الكود:</b> <code>{task.get('code', 'غير متوفر')}</code>
🏷️ <b>الاسم:</b> {task.get('name', 'بدون اسم')}
📊 <b>النوع:</b> {get_type_emoji(task.get('type'))} {task.get('type', 'غير معروف')}
💰 <b>السعر:</b> {task.get('price', 0)} نقطة
👥 <b>المطلوب:</b> {task.get('count', 0)} منفذ
✅ <b>المكتمل:</b> {task.get('completed_count', 0)}
🔄 <b>المتبقي:</b> {remaining}

🔗 <b>الرابط:</b> {task.get('link', 'بدون رابط')}
📝 <b>الوصف:</b> {task.get('description', 'بدون وصف')}
🎯 <b>متطلبات الإثبات:</b> {task.get('proof', 'بدون متطلبات')}

⏰ <b>تاريخ النشر:</b> {task.get('created_at', 'غير معروف')}
        """
        
        keyboard = [
            [InlineKeyboardButton("🚀 تنفيذ المهمة", callback_data=f"execute_task_{task_id}")],
            [InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="back_to_task_list")]
        ]
        
        # ✅ التحقق إذا كان المستخدم هو مالك المهمة
        is_owner = str(user_id) == str(task.get('owner_id'))
        
        # ✅ التحقق إذا كانت المهمة مثبتة
        is_pinned = db.is_task_pinned(str(task_id))
        
        # ✅ إضافة زر التثبيت إذا كان المستخدم هو المالك
        if is_owner:
            if is_pinned:
                keyboard.append([InlineKeyboardButton("📌 إلغاء التثبيت", callback_data=f"unpin_task_{task_id}")])
            else:
                pin_price = db.data.get("pin_settings", {}).get("pin_price", 10)
                keyboard.append([InlineKeyboardButton(f"📌 تثبيت المهمة ({pin_price} نقطة)", callback_data=f"pin_task_{task_id}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # ✅ تغيير parse_mode إلى HTML
        await update.callback_query.edit_message_text(
            message, 
            reply_markup=reply_markup, 
            parse_mode='HTML'  # ⬅️ هذا هو الإصلاح
        )
            
    except Exception as e:
        logger.error(f"خطأ في view_task_details: {e}")
        await update.callback_query.answer("❌ حدث خطأ في عرض تفاصيل المهمة")

@user_only
async def view_my_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض المهام التي أنشأها المستخدم على شكل أزرار"""
    try:
        user_id = update.effective_user.id
        
        # الحصول على المهام التي أنشأها المستخدم
        all_tasks = db.get_tasks_by_type("all")
        my_tasks = [task for task in all_tasks if task.get('owner_id') == str(user_id)]
        
        if not my_tasks:
            message = "📭 لم تقم بإنشاء أي مهام بعد.\n\n💡 يمكنك إنشاء مهمة جديدة من الزر أدناه!"
            keyboard = [
                [InlineKeyboardButton("➕ إنشاء مهمة جديدة", callback_data="show_task_types")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="member_menu")]
            ]
        else:
            message = "📋 المهام التي أنشأتها:\n\n"
            message += "💡 اختر المهمة لعرض التفاصيل أو حذفها:\n"
            
            keyboard = []
            
            # تقسيم المهام إلى أزواج (صفوف تحتوي على زرين)
            for i in range(0, len(my_tasks), 2):
                row = []
                # الزر الأول في الصف
                if i < len(my_tasks):
                    task1 = my_tasks[i]
                    task1_name = task1.get('name', 'بدون اسم')
                    if len(task1_name) > 15:
                        task1_name = task1_name[:12] + "..."
                    
                    status_emoji = "✅" if task1.get('status') == 'completed' else "🟡"
                    btn_text = f"{status_emoji} {task1_name}"
                    row.append(InlineKeyboardButton(btn_text, callback_data=f"mytask_{task1['id']}"))
                
                # الزر الثاني في الصف (إذا موجود)
                if i + 1 < len(my_tasks):
                    task2 = my_tasks[i + 1]
                    task2_name = task2.get('name', 'بدون اسم')
                    if len(task2_name) > 15:
                        task2_name = task2_name[:12] + "..."
                    
                    status_emoji = "✅" if task2.get('status') == 'completed' else "🟡"
                    btn_text = f"{status_emoji} {task2_name}"
                    row.append(InlineKeyboardButton(btn_text, callback_data=f"mytask_{task2['id']}"))
                
                if row:
                    keyboard.append(row)
            
            # أزرار التنقل
            keyboard.append([InlineKeyboardButton("➕ إنشاء مهمة جديدة", callback_data="show_task_types")])
            keyboard.append([InlineKeyboardButton("📋 المهام المتاحة", callback_data="member_tasks_view")])
        
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="member_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup)
            
    except Exception as e:
        logger.error(f"خطأ في view_my_tasks: {e}")
        await update.callback_query.answer("❌ حدث خطأ في عرض المهام الشخصية")

@user_only
async def show_my_task_details(update: Update, context: ContextTypes.DEFAULT_TYPE, task_id):
    """عرض تفاصيل المهمة الشخصية مع خيار الحذف"""
    try:
        task = db.get_task(task_id)
        
        if not task:
            await update.callback_query.answer("❌ المهمة غير موجودة")
            return
        
        user_id = update.effective_user.id
        
        # ❌ إزالة التحقق من الملكية (غير ضروري في "مهامي")
        # ✅ جميع المهام في "مهامي" مملوكة للمستخدم
        
        remaining = task.get('count', 0) - task.get('completed_count', 0)
        completion_percentage = (task.get('completed_count', 0) / task.get('count', 1)) * 100
        status = "✅ مكتملة" if task.get('status') == 'completed' else "🟡 قيد التنفيذ"
        
        # حساب النقاط المستردة في حالة الحذف
        points_to_refund = remaining * task.get('price', 0)
        
        message = f"""
🎯 <b>تفاصيل المهمة الشخصية</b>

┌────────────────────────────
│ <b>🏷️ الاسم:</b> {task.get('name', 'بدون اسم')}
│ <b>📊 النوع:</b> {get_type_emoji(task.get('type'))} {task.get('type', 'غير معروف')}
│ <b>💰 السعر:</b> {task.get('price', 0)} نقطة
│ <b>👥 المطلوب:</b> {task.get('count', 0)} منفذ
│ <b>✅ المكتمل:</b> {task.get('completed_count', 0)}
│ <b>🔄 المتبقي:</b> {remaining}
│ <b>📈 الإنجاز:</b> {completion_percentage:.1f}%
│ <b>📊 الحالة:</b> {status}
│ <b>🆔 الكود:</b> <code>{task.get('code', 'غير متوفر')}</code>
└────────────────────────────

💡 <b>في حالة الحذف:</b>
• سيتم استرداد: {points_to_refund} نقطة
• سيتم حذف المهمة من النظام
• سيتم حذفها من قناة المهام
        """
        
        keyboard = []
        
        # ✅ إضافة زر التثبيت/إلغاء التثبيت (بدون تحقق ملكية)
        is_pinned = db.is_task_pinned(str(task_id))
        if is_pinned:
            keyboard.append([InlineKeyboardButton("📌 إلغاء التثبيت", callback_data=f"unpin_task_{task_id}")])
        else:
            pin_price = db.data.get("pin_settings", {}).get("pin_price", 10)
            keyboard.append([InlineKeyboardButton(f"📌 تثبيت المهمة ({pin_price} نقطة)", callback_data=f"pin_task_{task_id}")])
        
        # إضافة زر الحذف
        keyboard.append([InlineKeyboardButton("🗑️ حذف المهمة", callback_data=f"delete_mytask_{task_id}")])
        keyboard.append([InlineKeyboardButton("🔙 رجوع إلى مهامي", callback_data="member_my_tasks")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')
            
    except Exception as e:
        logger.error(f"خطأ في show_my_task_details: {e}")
        await update.callback_query.answer("❌ حدث خطأ في عرض التفاصيل")

@user_only
async def delete_my_task(update: Update, context: ContextTypes.DEFAULT_TYPE, task_id):
    """حذف المهمة الشخصية واسترداد النقاط"""
    try:
        task = db.get_task(task_id)
        
        if not task:
            await update.callback_query.answer("❌ المهمة غير موجودة")
            return
        
        user_id = update.effective_user.id
        
        # التحقق من أن المستخدم هو صاحب المهمة
        if str(user_id) != task.get('owner_id'):
            await update.callback_query.answer("❌ ليس لديك صلاحية حذف هذه المهمة")
            return
        
        # حساب النقاط المستردة
        remaining = task.get('count', 0) - task.get('completed_count', 0)
        points_to_refund = remaining * task.get('price', 0)
        
        # حذف المهمة من القناة أولاً
        try:
            from Admin.TasksChannels import move_task_to_completed
            # نحاول حذفها من القناة
            await move_task_to_completed(task_id, context)
        except Exception as e:
            logger.error(f"⚠️ خطأ في حذف المهمة من القناة: {e}")
            # نستمر في الحذف حتى لو فشل حذف القناة
        
        # حذف المهمة من قاعدة البيانات
        for i, t in enumerate(db.data["tasks_new"]):
            if str(t.get("id")) == str(task_id):
                db.data["tasks_new"].pop(i)
                break
        
        # استرداد النقاط
        if points_to_refund > 0:
            db.add_points_to_user(user_id, points_to_refund)
        
        # حفظ التغييرات
        db.save_data()
        
        logger.info(f"✅ تم حذف المهمة {task_id} واسترداد {points_to_refund} نقطة")
        
        await update.callback_query.answer(f"✅ تم حذف المهمة واسترداد {points_to_refund} نقطة")
        await view_my_tasks(update, context)
            
    except Exception as e:
        logger.error(f"❌ خطأ في delete_my_task: {e}")
        await update.callback_query.answer("❌ حدث خطأ في حذف المهمة")

@user_only
async def search_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE, search_term):
    """بحث المهام بالكود أو الاسم"""
    try:
        all_tasks = db.get_tasks_by_type("all")
        found_tasks = []
        
        for task in all_tasks:
            # البحث بالكود
            if task.get('code', '').lower() == search_term.lower():
                found_tasks = [task]  # وجدت بالضبط
                break
            
            # البحث بالاسم
            if search_term.lower() in task.get('name', '').lower():
                found_tasks.append(task)
        
        if not found_tasks:
            await update.message.reply_text(f"🔍 لم يتم العثور على مهام تطابق: '{search_term}'")
            return
        
        # عرض النتائج
        if len(found_tasks) == 1:
            await view_task_details_simple(update, context, found_tasks[0]['id'])
        else:
            message = f"🔍 نتائج البحث عن: '{search_term}'\n\n"
            for i, task in enumerate(found_tasks, 1):
                task_name = task.get('name', 'بدون اسم')
                if len(task_name) > 20:
                    task_name = task_name[:17] + "..."
                
                message += f"{i}. {task_name}\n"
                message += f"   🆔 الكود: #{task.get('code', '')}\n"
                message += f"   📊 {task.get('type', 'غير معروف')} | 💰 {task.get('price', 0)} نقاط\n"
                message += f"   ✅ {task.get('completed_count', 0)}/{task.get('count', 0)} مكتمل\n\n"
            
            await update.message.reply_text(message)
            
    except Exception as e:
        logger.error(f"خطأ في البحث: {e}")
        await update.message.reply_text("❌ حدث خطأ في البحث")

@user_only
async def view_task_details_simple(update: Update, context: ContextTypes.DEFAULT_TYPE, task_id):
    """عرض تفاصيل المهمة بشكل مبسط للبحث"""
    try:
        task = db.get_task(task_id)
        
        if not task:
            await update.message.reply_text("❌ المهمة غير موجودة")
            return
        
        remaining = task.get('count', 0) - task.get('completed_count', 0)
        
        message = f"""
🎯 **تم العثور على المهمة**

🆔 **الكود:** `{task.get('code', 'غير متوفر')}`
🏷️ **الاسم:** {task.get('name', 'بدون اسم')}
📊 **النوع:** {get_type_emoji(task.get('type'))} {task.get('type', 'غير معروف')}
💰 **السعر:** {task.get('price', 0)} نقطة
👥 **المطلوب:** {task.get('count', 0)} منفذ
✅ **المكتمل:** {task.get('completed_count', 0)}
🔄 **المتبقي:** {remaining}

🔗 **الرابط:** {task.get('link', 'بدون رابط')}
📝 **الوصف:** {task.get('description', 'بدون وصف')}
        """
        
        keyboard = [
            [InlineKeyboardButton("🚀 تنفيذ المهمة", callback_data=f"execute_task_{task_id}")],
            [InlineKeyboardButton("📋 العودة للقائمة", callback_data="member_tasks_view")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"خطأ في عرض تفاصيل المهمة: {e}")
        await update.message.reply_text("❌ حدث خطأ في عرض التفاصيل")

@user_only
async def pin_task(update: Update, context: ContextTypes.DEFAULT_TYPE, task_id):
    """تثبيت المهمة"""
    try:
        task = db.get_task(task_id)
        
        if not task:
            await update.callback_query.answer("❌ المهمة غير موجودة")
            return
        
        user_id = update.effective_user.id
        
        # التحقق من أن المستخدم هو صاحب المهمة
        if str(user_id) != task.get('owner_id'):
            await update.callback_query.answer("❌ ليس لديك صلاحية تثبيت هذه المهمة")
            return
        
        # التحقق إذا كانت المهمة مثبتة بالفعل
        if db.is_task_pinned(task_id):
            await update.callback_query.answer("⚠️ المهمة مثبتة بالفعل")
            return
        
        # الحصول على سعر التثبيت
        pin_price = db.data.get("pin_settings", {}).get("pin_price", 10)
        
        # التحقق من رصيد المستخدم
        user_points = db.get_user_points(user_id)
        if user_points < pin_price:
            await update.callback_query.answer(f"❌ رصيدك غير كافي. تحتاج {pin_price} نقطة")
            return
        
        # خصم النقاط وتثبيت المهمة
        db.deduct_points_from_user(user_id, pin_price)
        db.pin_task(task_id)
        
        await update.callback_query.answer(f"✅ تم تثبيت المهمة وخصم {pin_price} نقطة")
        await view_task_details(update, context, task_id)
            
    except Exception as e:
        logger.error(f"❌ خطأ في pin_task: {e}")
        await update.callback_query.answer("❌ حدث خطأ في تثبيت المهمة")

@user_only
async def unpin_task(update: Update, context: ContextTypes.DEFAULT_TYPE, task_id):
    """إلغاء تثبيت المهمة"""
    try:
        task = db.get_task(task_id)
        
        if not task:
            await update.callback_query.answer("❌ المهمة غير موجودة")
            return
        
        user_id = update.effective_user.id
        
        # التحقق من أن المستخدم هو صاحب المهمة
        if str(user_id) != task.get('owner_id'):
            await update.callback_query.answer("❌ ليس لديك صلاحية إلغاء تثبيت هذه المهمة")
            return
        
        # التحقق إذا كانت المهمة غير مثبتة بالفعل
        if not db.is_task_pinned(task_id):
            await update.callback_query.answer("⚠️ المهمة غير مثبتة بالفعل")
            return
        
        # إلغاء تثبيت المهمة
        db.unpin_task(task_id)
        
        await update.callback_query.answer("✅ تم إلغاء تثبيت المهمة")
        await view_task_details(update, context, task_id)
            
    except Exception as e:
        logger.error(f"❌ خطأ في unpin_task: {e}")
        await update.callback_query.answer("❌ حدث خطأ في إلغاء تثبيت المهمة")