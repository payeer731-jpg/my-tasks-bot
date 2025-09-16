# ButtonManager.py - الإصدار المصحح (مع التحقق من الصلاحيات)
# ============ الجزء 1/6: الاستيرادات والإعدادات الأساسية ============
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from Data import db
import logging
import uuid
from datetime import datetime
from Config import OWNER_ID
from Decorators import admin_only  # استيراد الديكوراتور

logger = logging.getLogger(__name__)

def is_user_admin(user_id):
    """التحقق إذا كان المستخدم مشرفاً"""
    return str(user_id) in db.get_admins() or user_id == OWNER_ID

class ButtonManager:
    """نظام إدارة الأزرار المتقدم والمحترف"""

    @staticmethod
    def find_button_by_id(button_id: str):
        """البحث عن زر بواسطة المعرف - الإصدار المحسن"""
        try:
            # 1. البحث في الأزرار المخصصة الرئيسية
            for button in db.data["button_system"]["main_menu_buttons"]:
                if button["id"] == button_id:
                    return button
        
            # 2. البحث في الأزرار المحمية
            protected_buttons = db.data["button_system"]["protected_buttons"]
            if button_id in protected_buttons:
                return {"id": button_id, **protected_buttons[button_id], "type": "protected"}
        
            # 3. البحث في الأزرار الفرعية داخل القوائم الفرعية
            submenus = db.data["button_system"].get("submenus", {})
            for submenu_id, submenu_data in submenus.items():
                for button in submenu_data.get("buttons", []):
                    if button["id"] == button_id:
                        return button
        
            return None
        
        except Exception as e:
            logger.error(f"❌ خطأ في البحث عن الزر: {e}")
            return None

    @staticmethod
    @admin_only
    async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """القائمة الرئيسية لإدارة الأزرار - للمشرفين فقط"""
        try:
            keyboard = [
                [InlineKeyboardButton("📱 إدارة أزرار القائمة", callback_data="btn_mgr:main_menu")],
                [InlineKeyboardButton("🔄 إعادة ترتيب الأزرار", callback_data="btn_mgr:reorder")],
                [InlineKeyboardButton("🏗️ إنشاء زر جديد", callback_data="btn_mgr:create")],
                [InlineKeyboardButton("📁 إنشاء قائمة فرعية", callback_data="btn_mgr:create_submenu")],
                [InlineKeyboardButton("⚙️ الإعدادات المتقدمة", callback_data="btn_mgr:advanced_settings")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="admin_menu")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            stats = ButtonManager.get_system_stats()
            
            await update.callback_query.edit_message_text(
                f"🎛️ **نظام إدارة الأزرار المتقدم**\n\n"
                f"📊 **الإحصائيات:**\n"
                f"• 🎯 الأزرار الأساسية: {stats['protected_buttons']}\n"
                f"• 🎨 الأزرار المخصصة: {stats['custom_buttons']}\n"
                f"• 📁 القوائم الفرعية: {stats['submenus']}\n\n"
                f"💡 **اختر الإدارة المناسبة:**",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"خطأ في عرض قائمة إدارة الأزرار: {e}")
            await update.callback_query.answer("❌ حدث خطأ في تحميل القائمة")
    
    @staticmethod
    def get_system_stats():
        """الحصول على إحصائيات النظام"""
        return {
            'protected_buttons': len(db.data["button_system"]["protected_buttons"]),
            'custom_buttons': len(db.data["button_system"]["main_menu_buttons"]),
            'submenus': len(db.data["button_system"].get("submenus", {})),
            'total_buttons': len(db.data["button_system"]["protected_buttons"]) + 
                           len(db.data["button_system"]["main_menu_buttons"])
        }
    
    @staticmethod
    @admin_only
    async def manage_main_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إدارة أزرار القائمة الرئيسية - للمشرفين فقط"""
        try:
            buttons = db.data["button_system"]["main_menu_buttons"]
            protected_buttons = db.data["button_system"]["protected_buttons"]
            
            keyboard = []
            
            # عرض الأزرار المحمية
            keyboard.append([InlineKeyboardButton("🔒 الأزرار الأساسية (غير قابلة للحذف)", callback_data="btn_mgr:protected_info")])
            for btn_id, btn_data in sorted(protected_buttons.items(), key=lambda x: x[1]["position"]):
                keyboard.append([InlineKeyboardButton(
                    f"✏️ {btn_data['name']}", 
                    callback_data=f"btn_mgr:edit_protected:{btn_id}"
                )])
            
            # عرض الأزرار المخصصة
            if buttons:
                keyboard.append([InlineKeyboardButton("🎯 الأزرار المخصصة", callback_data="btn_mgr:custom_info")])
                for btn in sorted(buttons, key=lambda x: x["position"]):
                    emoji = "📁" if btn.get("type") == "submenu" else "🔘"
                    keyboard.append([InlineKeyboardButton(
                        f"{emoji} {btn['name']} ✏️🗑️", 
                        callback_data=f"btn_mgr:edit_custom:{btn['id']}"
                    )])
            else:
                keyboard.append([InlineKeyboardButton("📭 لا توجد أزرار مخصصة", callback_data="btn_mgr:no_custom")])
            
            # أزرار التحكم
            control_buttons = []
            control_buttons.append(InlineKeyboardButton("🆕 إنشاء زر جديد", callback_data="btn_mgr:create_main"))
            control_buttons.append(InlineKeyboardButton("📁 قائمة فرعية", callback_data="btn_mgr:create_submenu"))
            keyboard.append(control_buttons)
            
            keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="btn_mgr:main")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                "📋 **إدارة أزرار القائمة الرئيسية**\n\n"
                "🔒 **الأزرار الأساسية:** يمكن تعديل الأسماء فقط\n"
                "🎯 **الأزرار المخصصة:** تحكم كامل (تعديل/حذف/نقل)\n"
                "📁 **القوائم الفرعية:** أزرار تحتوي على أزرار أخرى\n\n"
                "💡 **اختر الزر للإدارة:**",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"خطأ في إدارة الأزرار الرئيسية: {e}")
            await update.callback_query.answer("❌ حدث خطأ في التحميل")

# ============ الجزء 2/6: تعديل وإدارة الأزرار ============
    @staticmethod
    @admin_only
    async def edit_custom_button(update: Update, context: ContextTypes.DEFAULT_TYPE, button_id: str):
        """تعديل زر مخصص - للمشرفين فقط"""
        try:
            button = ButtonManager.find_button_by_id(button_id)
            
            if not button:
                await update.callback_query.answer("❌ الزر غير موجود")
                return
            
            is_submenu = button.get("type") == "submenu"
            submenu_info = "\n📂 **قائمة فرعية**" if is_submenu else ""
            
            keyboard = [
                [InlineKeyboardButton("✏️ تعديل الاسم", callback_data=f"btn_edit:rename:{button_id}")],
                [InlineKeyboardButton("📝 تعديل المحتوى", callback_data=f"btn_edit:recontent:{button_id}")],
                [InlineKeyboardButton("🎨 تعديل الإيموجي", callback_data=f"btn_edit:emoji:{button_id}")],
                [InlineKeyboardButton("⬆️ نقل لأعلى", callback_data=f"btn_edit:move_up:{button_id}")],
                [InlineKeyboardButton("⬇️ نقل لأسفل", callback_data=f"btn_edit:move_down:{button_id}")],
            ]
            
            if is_submenu:
                keyboard.append([InlineKeyboardButton("📂 إدارة الأزرار الفرعية", callback_data=f"btn_edit:manage_sub:{button_id}")])
            
            keyboard.append([InlineKeyboardButton("🗑️ حذف الزر", callback_data=f"btn_edit:delete:{button_id}")])
            keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="btn_mgr:main_menu")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                f"⚙️ **تعديل الزر المخصص**{submenu_info}\n\n"
                f"🏷️ **الاسم:** {button['name']}\n"
                f"📝 **المحتوى:** {button['content'][:100]}...\n"
                f"📍 **الموضع:** {button['position'] + 1}\n"
                f"🆔 **المعرف:** {button['id']}\n"
                f"📅 **تاريخ الإنشاء:** {button.get('created_at', 'غير معروف')}",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"خطأ في تعديل الزر: {e}")
            await update.callback_query.answer("❌ حدث خطأ في التعديل")
    
    @staticmethod
    @admin_only
    async def edit_protected_button(update: Update, context: ContextTypes.DEFAULT_TYPE, button_id: str):
        """تعديل زر محمي (إعادة تسمية فقط) - للمشرفين فقط"""
        try:
            protected_buttons = db.data["button_system"]["protected_buttons"]
            button_data = protected_buttons.get(button_id)
            
            if not button_data:
                await update.callback_query.answer("❌ الزر غير موجود")
                return
            
            keyboard = [
                [InlineKeyboardButton("✏️ إعادة تسمية", callback_data=f"btn_edit:rename_protected:{button_id}")],
                [InlineKeyboardButton("🎨 تغيير الإيموجي", callback_data=f"btn_edit:emoji_protected:{button_id}")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="btn_mgr:main_menu")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                f"⚙️ **تعديل زر أساسي**\n\n"
                f"🔒 **حالة:** محمي (غير قابل للحذف)\n"
                f"🏷️ **الاسم الحالي:** {button_data['name']}\n"
                f"🎯 **الوظيفة:** {button_id}\n"
                f"📍 **الموضع:** {button_data['position'] + 1}\n\n"
                f"💡 يمكنك تعديل الاسم والإيموجي فقط",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"خطأ في تعديل الزر المحمي: {e}")
            await update.callback_query.answer("❌ حدث خطأ في التعديل")

    @staticmethod
    @admin_only
    async def create_button_start(update: Update, context: ContextTypes.DEFAULT_TYPE, button_type="main"):
        """بدء عملية إنشاء زر جديد - للمشرفين فقط"""
        try:
            context.user_data["button_creation"] = {
                "step": "awaiting_name",
                "type": button_type,
                "data": {}
            }
            
            button_type_text = "قائمة فرعية" if button_type == "submenu" else "زر جديد"
            
            await update.callback_query.edit_message_text(
                f"🏗️ **إنشاء {button_type_text}**\n\n"
                "أرسل اسم الزر:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 إلغاء", callback_data="btn_mgr:main_menu")]
                ]),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"خطأ في بدء إنشاء الزر: {e}")
            await update.callback_query.answer("❌ حدث خطأ في البدء")
    
    @staticmethod
    @admin_only
    async def handle_button_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة إنشاء الزر - للمشرفين فقط"""
        if "button_creation" not in context.user_data:
            return False
        
        creation_data = context.user_data["button_creation"]
        current_step = creation_data["step"]
        user_input = update.message.text
        
        try:
            if current_step == "awaiting_name":
                creation_data["data"]["name"] = user_input
                creation_data["step"] = "awaiting_emoji"
                
                await update.message.reply_text(
                    "✅ تم حفظ اسم الزر\n\n"
                    "🎨 أرسل الإيموجي الذي تريد إضافته للزر (اختياري):\n"
                    "مثال: 📱, 💰, 🎯\n\n"
                    "أو أرسل 'تخطي' للمتابعة بدون إيموجي",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⏭️ تخطي", callback_data="btn_create:skip_emoji")],
                        [InlineKeyboardButton("🔙 إلغاء", callback_data="btn_mgr:main_menu")]
                    ])
                )
                return True
                
            elif current_step == "awaiting_emoji":
                if user_input.lower() != 'تخطي':
                    creation_data["data"]["emoji"] = user_input.strip()
                creation_data["step"] = "awaiting_content"
                
                await update.message.reply_text(
                    "✅ تم حفظ الإيموجي\n\n"
                    "📝 أرسل محتوى الزر (النص الذي سيظهر عند الضغط عليه):\n\n"
                    "💡 **المتغيرات المتاحة:**\n"
                    "• `{user_id}` - رقم المستخدم\n"
                    "• `{user_name}` - اسم المستخدم\n" 
                    "• `{points}` - النقاط\n"
                    "• `{level_name}` - المستوى\n"
                    "• `{active_tasks}` - المهام النشطة\n"
                    "• `{current_date}` - التاريخ\n"
                    "• `{total_earned}` - إجمالي الأرباح\n"
                    "• `{invites_count}` - عدد الدعوات",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 إلغاء", callback_data="btn_mgr:main_menu")]
                    ])
                )
                return True

# ============ الجزء 3/6: تأكيد الإنشاء والحذف ============
            elif current_step == "awaiting_content":
                creation_data["data"]["content"] = user_input
                creation_data["step"] = "awaiting_confirmation"
                
                # إنشاء الزر
                new_button = {
                    "id": str(uuid.uuid4())[:8],
                    "name": creation_data["data"]["name"],
                    "content": creation_data["data"]["content"],
                    "type": creation_data["type"],
                    "position": len(db.data["button_system"]["main_menu_buttons"]),
                    "created_at": datetime.now().isoformat(),
                    "emoji": creation_data["data"].get("emoji", "")
                }
                
                if creation_data["type"] == "submenu":
                    new_button["sub_buttons"] = []
                
                # حفظ مؤقت
                context.user_data["button_creation"]["data"]["button"] = new_button
                
                # تحضير لوحة التأكيد
                emoji_display = new_button["emoji"] + " " if new_button["emoji"] else ""
                
                keyboard = [
                    [InlineKeyboardButton("✅ تأكيد الإنشاء", callback_data="btn_create:confirm")],
                    [InlineKeyboardButton("✏️ تعديل الاسم", callback_data="btn_create:edit_name")],
                    [InlineKeyboardButton("🎨 تعديل الإيموجي", callback_data="btn_create:edit_emoji")],
                    [InlineKeyboardButton("📝 تعديل المحتوى", callback_data="btn_create:edit_content")],
                    [InlineKeyboardButton("🔙 إلغاء", callback_data="btn_mgr:main_menu")]
                ]
                
                await update.message.reply_text(
                    f"📋 **تأكيد إنشاء الزر**\n\n"
                    f"🏷️ **الاسم:** {emoji_display}{new_button['name']}\n"
                    f"📝 **المحتوى:** {new_button['content'][:100]}...\n"
                    f"📊 **النوع:** {'قائمة فرعية' if new_button['type'] == 'submenu' else 'زر عادي'}\n"
                    f"📍 **الموضع:** {new_button['position'] + 1}\n\n"
                    f"هل تريد إنشاء هذا الزر؟",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
                return True
                
        except Exception as e:
            logger.error(f"خطأ في معالجة إنشاء الزر: {e}")
            await update.message.reply_text("❌ حدث خطأ في المعالجة")
            return False
        
        return False
    
    @staticmethod
    @admin_only
    async def confirm_button_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تأكيد إنشاء الزر - للمشرفين فقط"""
        try:
            if "button_creation" not in context.user_data:
                await update.callback_query.answer("❌ لا توجد عملية إنشاء")
                return
        
            button_data = context.user_data["button_creation"]["data"]["button"]
        
            # حفظ الزر في قاعدة البيانات
            db.data["button_system"]["main_menu_buttons"].append(button_data)
            db.data["button_system"]["button_counter"] += 1
        
            # إذا كان قائمة فرعية، ننشئها في التصنيفات
            if button_data["type"] == "submenu":
                if "submenus" not in db.data["button_system"]:
                    db.data["button_system"]["submenus"] = {}
                
                # إنشاء القائمة الفرعية فارغة
                db.data["button_system"]["submenus"][button_data["id"]] = {
                    "name": button_data["name"],
                    "buttons": []  # قائمة فارغة للأزرار الفرعية
                }
        
            db.save_data()

            # تنظيف البيانات المؤقتة
            del context.user_data["button_creation"]
        
            emoji_display = button_data["emoji"] + " " if button_data["emoji"] else ""
        
            await update.callback_query.edit_message_text(
                f"✅ **تم إنشاء الزر بنجاح!**\n\n"
                f"🏷️ **الاسم:** {emoji_display}{button_data['name']}\n"
                f"📍 **الموضع:** {button_data['position'] + 1}\n"
                f"📊 **النوع:** {'قائمة فرعية' if button_data['type'] == 'submenu' else 'زر عادي'}\n\n"
                f"💡 تمت إضافته إلى القائمة الرئيسية",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎛️ العودة للإدارة", callback_data="btn_mgr:main_menu")]
                ]),
                parse_mode='Markdown'
            )
        
        except Exception as e:
            logger.error(f"خطأ في تأكيد إنشاء الزر: {e}")
            await update.callback_query.answer("❌ حدث خطأ في الإنشاء")

    @staticmethod
    @admin_only
    async def delete_button(update: Update, context: ContextTypes.DEFAULT_TYPE, button_id: str):
        """حذف زر مخصص - للمشرفين فقط"""
        try:
            # البحث عن الزر وحذفه
            buttons = db.data["button_system"]["main_menu_buttons"]
            for i, button in enumerate(buttons):
                if button["id"] == button_id:
                    # إذا كان قائمة فرعية، نحذف الأزرار الفرعية أيضاً
                    if button.get("type") == "submenu":
                        if "submenus" in db.data["button_system"]:
                            db.data["button_system"]["submenus"].pop(button_id, None)
                    
                    # الحذف من القائمة الرئيسية
                    deleted_button = buttons.pop(i)
                    
                    # إعادة ترتيب المواضع
                    for j, btn in enumerate(buttons[i:], start=i):
                        btn["position"] = j
                    
                    db.save_data()
                    
                    await update.callback_query.edit_message_text(
                        f"🗑️ **تم حذف الزر بنجاح**\n\n"
                        f"🏷️ **الاسم:** {deleted_button['name']}\n"
                        f"📅 **تاريخ الإنشاء:** {deleted_button.get('created_at', 'غير معروف')}\n\n"
                        f"✅ تم الحذف بشكل دائم",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🎛️ العودة للإدارة", callback_data="btn_mgr:main_menu")]
                        ]),
                        parse_mode='Markdown'
                    )
                    return
            
            await update.callback_query.answer("❌ الزر غير موجود")
            
        except Exception as e:
            logger.error(f"خطأ في حذف الزر: {e}")
            await update.callback_query.answer("❌ حدث خطأ في الحذف")


# ============ الجزء 4/6: إعادة التسمية وتغيير المحتوى ============
    @staticmethod
    @admin_only
    async def rename_button(update: Update, context: ContextTypes.DEFAULT_TYPE, button_id: str, is_protected=False):
        """إعادة تسمية زر - للمشرفين فقط"""
        try:
            if is_protected:
                # تسمية زر محمي
                if button_id in db.data["button_system"]["protected_buttons"]:
                    context.user_data["renaming_button"] = {
                        "button_id": button_id,
                        "is_protected": True,
                        "old_name": db.data["button_system"]["protected_buttons"][button_id]["name"]
                    }
                    
                    await update.callback_query.edit_message_text(
                        f"✏️ **إعادة تسمية زر أساسي**\n\n"
                        f"الاسم الحالي: {db.data['button_system']['protected_buttons'][button_id]['name']}\n\n"
                        f"أرسل الاسم الجديد:",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🔙 إلغاء", callback_data=f"btn_mgr:edit_protected:{button_id}")]
                        ]),
                        parse_mode='Markdown'
                    )
                else:
                    await update.callback_query.answer("❌ الزر غير موجود")
            else:
                # تسمية زر مخصص
                button = ButtonManager.find_button_by_id(button_id)
                if button:
                    context.user_data["renaming_button"] = {
                        "button_id": button_id,
                        "is_protected": False,
                        "old_name": button["name"]
                    }
                    
                    await update.callback_query.edit_message_text(
                        f"✏️ **إعادة تسمية زر مخصص**\n\n"
                        f"الاسم الحالي: {button['name']}\n\n"
                        f"أرسل الاسم الجديد:",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🔙 إلغاء", callback_data=f"btn_mgr:edit_custom:{button_id}")]
                        ]),
                        parse_mode='Markdown'
                    )
                else:
                    await update.callback_query.answer("❌ الزر غير موجود")
                    
        except Exception as e:
            logger.error(f"خطأ في بدء إعادة التسمية: {e}")
            await update.callback_query.answer("❌ حدث خطأ في التسمية")

    @staticmethod
    @admin_only
    async def handle_button_rename(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة إعادة تسمية الزر - للمشرفين فقط"""
        try:
            if "renaming_button" not in context.user_data:
                return False
            
            rename_data = context.user_data["renaming_button"]
            new_name = update.message.text.strip()
            
            if not new_name:
                await update.message.reply_text("❌ يجب إدخال اسم صحيح")
                return True
            
            if rename_data["is_protected"]:
                # تحديث الزر المحمي
                if rename_data["button_id"] in db.data["button_system"]["protected_buttons"]:
                    db.data["button_system"]["protected_buttons"][rename_data["button_id"]]["name"] = new_name
                    db.save_data()
                    
                    await update.message.reply_text(
                        f"✅ تم إعادة تسمية الزر\n\n"
                        f"من: {rename_data['old_name']}\n"
                        f"إلى: {new_name}",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🎛️ العودة للإدارة", callback_data="btn_mgr:main_menu")]
                        ])
                    )
            else:
                # تحديث الزر المخصص
                button = ButtonManager.find_button_by_id(rename_data["button_id"])
                if button:
                    button["name"] = new_name
                    db.save_data()
                    
                    await update.message.reply_text(
                        f"✅ تم إعادة تسمية الزر\n\n"
                        f"من: {rename_data['old_name']}\n"
                        f"إلى: {new_name}",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🎛️ العودة للإدارة", callback_data=f"btn_mgr:edit_custom:{rename_data['button_id']}")]
                        ])
                    )
            
            # تنظيف البيانات المؤقتة
            del context.user_data["renaming_button"]
            return True
            
        except Exception as e:
            logger.error(f"خطأ في معالجة إعادة التسمية: {e}")
            await update.message.reply_text("❌ حدث خطأ في التسمية")
            return True

    @staticmethod
    @admin_only
    async def change_button_emoji(update: Update, context: ContextTypes.DEFAULT_TYPE, button_id: str, is_protected=False):
        """تغيير إيموجي الزر - للمشرفين فقط"""
        try:
            if is_protected:
                # تغيير إيموجي زر محمي
                if button_id in db.data["button_system"]["protected_buttons"]:
                    context.user_data["changing_emoji"] = {
                        "button_id": button_id,
                        "is_protected": True,
                        "old_emoji": db.data["button_system"]["protected_buttons"][button_id].get("emoji", "")
                    }
                    
                    await update.callback_query.edit_message_text(
                        f"🎨 **تغيير إيموجي الزر**\n\n"
                        f"الإيموجي الحالي: {db.data['button_system']['protected_buttons'][button_id].get('emoji', 'لا يوجد')}\n\n"
                        f"أرسل الإيموجي الجديد (أو 'حذف' لإزالة الإيموجي):",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🔙 إلغاء", callback_data=f"btn_mgr:edit_protected:{button_id}")]
                        ]),
                        parse_mode='Markdown'
                    )
            else:
                # تغيير إيموجi زر مخصص
                button = ButtonManager.find_button_by_id(button_id)
                if button:
                    context.user_data["changing_emoji"] = {
                        "button_id": button_id,
                        "is_protected": False,
                        "old_emoji": button.get("emoji", "")
                    }
                    
                    await update.callback_query.edit_message_text(
                        f"🎨 **تغيير إيموجي الزر**\n\n"
                        f"الإيموجي الحالي: {button.get('emoji', 'لا يوجد')}\n\n"
                        f"أرسل الإيموجي الجديد (أو 'حذف' لإزالة الإيموجي):",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🔙 إلغاء", callback_data=f"btn_mgr:edit_custom:{button_id}")]
                        ]),
                        parse_mode='Markdown'
                    )
                    
        except Exception as e:
            logger.error(f"خطأ في تغيير الإيموجي: {e}")
            await update.callback_query.answer("❌ حدث خطأ في التغيير")

    @staticmethod
    @admin_only
    async def handle_emoji_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة تغيير الإيموجي - للمشرفين فقط"""
        try:
            if "changing_emoji" not in context.user_data:
                return False
            
            change_data = context.user_data["changing_emoji"]
            new_emoji = update.message.text.strip()
            
            if new_emoji.lower() == 'حذف':
                new_emoji = ""
            
            if change_data["is_protected"]:
                # تحديث الإيموجي للزر المحمي
                if change_data["button_id"] in db.data["button_system"]["protected_buttons"]:
                    db.data["button_system"]["protected_buttons"][change_data["button_id"]]["emoji"] = new_emoji
                    db.save_data()
                    
                    await update.message.reply_text(
                        f"✅ تم {'إزالة' if not new_emoji else 'تغيير'} إيموجي الزر",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🎛️ العودة", callback_data=f"btn_mgr:edit_protected:{change_data['button_id']}")]
                        ])
                    )
            else:
                # تحديث الإيموجي للزر المخصص
                button = ButtonManager.find_button_by_id(change_data["button_id"])
                if button:
                    button["emoji"] = new_emoji
                    db.save_data()
                    
                    await update.message.reply_text(
                        f"✅ تم {'إزالة' if not new_emoji else 'تغيير'} إيموجي الزر",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🎛️ العودة", callback_data=f"btn_mgr:edit_custom:{change_data['button_id']}")]
                        ])
                    )
            
            # تنظيف البيانات المؤقتة
            del context.user_data["changing_emoji"]
            return True
            
        except Exception as e:
            logger.error(f"خطأ في معالجة تغيير الإيموجي: {e}")
            await update.message.reply_text("❌ حدث خطأ في التغيير")
            return True

    @staticmethod
    @admin_only
    async def change_button_content(update: Update, context: ContextTypes.DEFAULT_TYPE, button_id: str):
        """تغيير محتوى الزر - للمشرفين فقط"""
        try:
            button = ButtonManager.find_button_by_id(button_id)
            if button:
                context.user_data["changing_content"] = {
                    "button_id": button_id,
                    "old_content": button["content"]
                }
                
                await update.callback_query.edit_message_text(
                    f"📝 **تغيير محتوى الزر**\n\n"
                    f"المحتوى الحالي: {button['content'][:100]}...\n\n"
                    f"أرسل المحتوى الجديد:",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 إلغاء", callback_data=f"btn_mgr:edit_custom:{button_id}")]
                    ]),
                    parse_mode='Markdown'
                )
            else:
                await update.callback_query.answer("❌ الزر غير موجود")
                
        except Exception as e:
            logger.error(f"خطأ في تغيير المحتوى: {e}")
            await update.callback_query.answer("❌ حدث خطأ في التغيير")

# ============ الجزء 5/6: معالجة المحتوى وإعادة الترتيب ============
    @staticmethod
    @admin_only
    async def handle_content_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة تغيير المحتوى - للمشرفين فقط"""
        try:
            if "changing_content" not in context.user_data:
                return False
            
            change_data = context.user_data["changing_content"]
            new_content = update.message.text
            
            button = ButtonManager.find_button_by_id(change_data["button_id"])
            if button:
                button["content"] = new_content
                db.save_data()
                
                await update.message.reply_text(
                    "✅ تم تحديث محتوى الزر بنجاح",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🎛️ العودة", callback_data=f"btn_mgr:edit_custom:{change_data['button_id']}")]
                    ])
                )
            
            # تنظيف البيانات المؤقتة
            del context.user_data["changing_content"]
            return True
            
        except Exception as e:
            logger.error(f"خطأ في معالجة تغيير المحتوى: {e}")
            await update.message.reply_text("❌ حدث خطأ في التحديث")
            return True

    @staticmethod
    @admin_only
    async def move_button(update: Update, context: ContextTypes.DEFAULT_TYPE, button_id: str, direction: str):
        """نقل زر لأعلى أو لأسفل - للمشرفين فقط"""
        try:
            buttons = db.data["button_system"]["main_menu_buttons"]
            button_index = -1
            
            # البحث عن الزر
            for i, button in enumerate(buttons):
                if button["id"] == button_id:
                    button_index = i
                    break
            
            if button_index == -1:
                await update.callback_query.answer("❌ الزر غير موجود")
                return
            
            if direction == "up" and button_index > 0:
                # نقل لأعلى
                buttons[button_index], buttons[button_index - 1] = buttons[button_index - 1], buttons[button_index]
                buttons[button_index]["position"] = button_index
                buttons[button_index - 1]["position"] = button_index - 1
                
            elif direction == "down" and button_index < len(buttons) - 1:
                # نقل لأسفل
                buttons[button_index], buttons[button_index + 1] = buttons[button_index + 1], buttons[button_index]
                buttons[button_index]["position"] = button_index
                buttons[button_index + 1]["position"] = button_index + 1
            else:
                await update.callback_query.answer("⚠️ لا يمكن النقل في هذا الاتجاه")
                return
            
            db.save_data()
            await update.callback_query.answer("✅ تم نقل الزر")
            
            # إعادة تحميل واجهة التعديل
            await ButtonManager.edit_custom_button(update, context, button_id)
            
        except Exception as e:
            logger.error(f"خطأ في نقل الزر: {e}")
            await update.callback_query.answer("❌ حدث خطأ في النقل")

    @staticmethod
    @admin_only
    async def reorder_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """واجهة إعادة ترتيب الأزرار - للمشرفين فقط"""
        try:
            buttons = db.data["button_system"]["main_menu_buttons"]
            
            if not buttons:
                await update.callback_query.answer("❌ لا توجد أزرار لإعادة الترتيب")
                return
            
            keyboard = []
            
            for i, button in enumerate(sorted(buttons, key=lambda x: x["position"])):
                emoji = button.get("emoji", "") + " " if button.get("emoji") else ""
                move_buttons = []
                
                if i > 0:
                    move_buttons.append(InlineKeyboardButton("⬆️", callback_data=f"btn_reorder:move_up:{button['id']}"))
                if i < len(buttons) - 1:
                    move_buttons.append(InlineKeyboardButton("⬇️", callback_data=f"btn_reorder:move_down:{button['id']}"))
                
                keyboard.append([
                    InlineKeyboardButton(f"{i+1}. {emoji}{button['name']}", callback_data=f"btn_mgr:edit_custom:{button['id']}"),
                    *move_buttons
                ])
            
            # أزرار التحكم يجب أن تكون خارج حلقة for
            keyboard.append([InlineKeyboardButton("✅ حفظ الترتيب", callback_data="btn_reorder:save")])
            keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="btn_mgr:main")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                "🔄 **إعادة ترتيب الأزرار**\n\n"
                "💡 استخدم الأزرار لتحريك الأزرار للأعلى أو الأسفل\n"
                "✅ اضغط 'حفظ الترتيب' عند الانتهاء\n\n"
                "📋 **ترتيب الأزرار الحالي:**",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
                
        except Exception as e:
            logger.error(f"خطأ في عرض واجهة إعادة الترتيب: {e}")
            await update.callback_query.answer("❌ حدث خطأ في التحميل")

    @staticmethod
    @admin_only
    async def handle_reorder_action(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str, button_id: str):
        """معالجة إجراءات إعادة الترتيب - للمشرفين فقط"""
        try:
            if action == "move_up":
                await ButtonManager.move_button(update, context, button_id, "up")
            elif action == "move_down":
                await ButtonManager.move_button(update, context, button_id, "down")
            elif action == "save":
                await update.callback_query.answer("✅ تم حفظ الترتيب بنجاح")
                await ButtonManager.manage_main_buttons(update, context)
                
        except Exception as e:
            logger.error(f"خطأ في معالجة إعادة الترتيب: {e}")
            await update.callback_query.answer("❌ حدث خطأ في المعالجة")

    @staticmethod
    @admin_only
    async def create_submenu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إنشاء قائمة فرعية جديدة - للمشرفين فقط"""
        await ButtonManager.create_button_start(update, context, "submenu")

    @staticmethod
    async def show_submenu_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE, submenu_id: str):
        """عرض القائمة الفرعية للمستخدمين العاديين"""
        try:
            # التحقق من الصلاحية أولاً
            user_id = update.effective_user.id
            
            # الحصول على القائمة الفرعية
            submenu = db.data["button_system"]["submenus"].get(submenu_id)
            if not submenu:
                await update.callback_query.answer("❌ القائمة غير موجودة")
                return
        
            buttons = submenu.get("buttons", [])
        
            keyboard = []
        
            for button in buttons:
                emoji = button.get("emoji", "") + " " if button.get("emoji") else ""
                keyboard.append([
                    InlineKeyboardButton(
                        f"{emoji}{button['name']}", 
                        callback_data=f"btn_sub:press:{button['id']}"
                    )
                ])
        
            keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="member_menu")])
        
            reply_markup = InlineKeyboardMarkup(keyboard)
        
            await update.callback_query.edit_message_text(
                f"📂 {submenu['name']}\n\n"
                f"اختر من القائمة:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        
        except Exception as e:
            logger.error(f"خطأ في عرض القائمة الفرعية: {e}")
            await update.callback_query.answer("❌ حدث خطأ في التحميل")

# ============ الجزء 6/6: الأزرار الفرعية ومعالجات النظام ============
    @staticmethod
    @admin_only
    async def manage_submenu(update: Update, context: ContextTypes.DEFAULT_TYPE, submenu_id: str):
        """إدارة قائمة فرعية - للمشرفين فقط"""
        try:
            submenu = db.data["button_system"]["submenus"].get(submenu_id)
            if not submenu:
                await update.callback_query.answer("❌ القائمة غير موجودة")
                return
            
            buttons = submenu.get("buttons", [])
            
            keyboard = []
            
            if buttons:
                keyboard.append([InlineKeyboardButton("🎯 الأزرار الفرعية", callback_data="btn_sub:buttons_info")])
                for i, button in enumerate(buttons):
                    keyboard.append([InlineKeyboardButton(
                        f"{i+1}. {button['name']} ✏️🗑️", 
                        callback_data=f"btn_sub:edit:{submenu_id}:{button['id']}"
                    )])
            else:
                keyboard.append([InlineKeyboardButton("📭 لا توجد أزرار فرعية", callback_data="btn_sub:no_buttons")])
            
            keyboard.append([InlineKeyboardButton("➕ إضافة زر فرعي", callback_data=f"btn_sub:add:{submenu_id}")])
            keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="btn_mgr:main_menu")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                f"📂 **إدارة القائمة الفرعية: {submenu['name']}**\n\n"
                f"🔢 عدد الأزرار: {len(buttons)}\n"
                f"🆔 المعرف: {submenu_id}\n\n"
                f"💡 اختر الإدارة المناسبة:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"خطأ في إدارة القائمة الفرعية: {e}")
            await update.callback_query.answer("❌ حدث خطأ في التحميل")

    @staticmethod
    @admin_only
    async def add_submenu_button(update: Update, context: ContextTypes.DEFAULT_TYPE, submenu_id: str):
        """إضافة زر إلى قائمة فرعية - للمشرفين فقط"""
        try:
            context.user_data["submenu_button_creation"] = {
                "step": "awaiting_name",
                "submenu_id": submenu_id,
                "data": {}
            }
            
            await update.callback_query.edit_message_text(
                f"➕ **إضافة زر إلى القائمة الفرعية**\n\n"
                f"أرسل اسم الزر الفرعي:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 إلغاء", callback_data=f"btn_sub:manage:{submenu_id}")]
                ]),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"خطأ في بدء إضافة زر فرعي: {e}")
            await update.callback_query.answer("❌ حدث خطأ في البدء")

    @staticmethod
    @admin_only
    async def handle_submenu_button_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة إنشاء زر فرعي - للمشرفين فقط"""
        if "submenu_button_creation" not in context.user_data:
            return False
        
        creation_data = context.user_data["submenu_button_creation"]
        current_step = creation_data["step"]
        user_input = update.message.text
        
        try:
            if current_step == "awaiting_name":
                creation_data["data"]["name"] = user_input
                creation_data["step"] = "awaiting_content"
                
                await update.message.reply_text(
                    "✅ تم حفظ اسم الزر الفرعي\n\n"
                    "📝 أرسل محتوى الزر الفرعي:",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 إلغاء", callback_data=f"btn_sub:manage:{creation_data['submenu_id']}")]
                    ])
                )
                return True
                
            elif current_step == "awaiting_content":
                creation_data["data"]["content"] = user_input
                
                # إنشاء الزر الفرعي
                new_button = {
                    "id": str(uuid.uuid4())[:8],
                    "name": creation_data["data"]["name"],
                    "content": creation_data["data"]["content"],
                    "position": len(db.data["button_system"]["submenus"][creation_data["submenu_id"]]["buttons"])
                }
                
                # إضافة الزر إلى القائمة الفرعية
                db.data["button_system"]["submenus"][creation_data["submenu_id"]]["buttons"].append(new_button)
                db.save_data()
                
                # تنظيف البيانات المؤقتة
                del context.user_data["submenu_button_creation"]
                
                await update.message.reply_text(
                    f"✅ تم إضافة الزر الفرعي بنجاح\n\n"
                    f"🏷️ الاسم: {new_button['name']}\n"
                    f"📍 الموضع: {new_button['position'] + 1}",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📂 العودة للإدارة", callback_data=f"btn_sub:manage:{creation_data['submenu_id']}")]
                    ])
                )
                return True
                
        except Exception as e:
            logger.error(f"خطأ في معالجة إنشاء الزر الفرعي: {e}")
            await update.message.reply_text("❌ حدث خطأ في المعالجة")
            return False
        
        return False

    @staticmethod
    @admin_only
    async def edit_submenu_button(update: Update, context: ContextTypes.DEFAULT_TYPE, submenu_id: str, button_id: str):
        """تعديل زر فرعي - للمشرفين فقط"""
        try:
            submenu = db.data["button_system"]["submenus"].get(submenu_id)
            if not submenu:
                await update.callback_query.answer("❌ القائمة غير موجودة")
                return
            
            button = None
            for btn in submenu["buttons"]:
                if btn["id"] == button_id:
                    button = btn
                    break
            
            if not button:
                await update.callback_query.answer("❌ الزر غير موجود")
                return
            
            keyboard = [
                [InlineKeyboardButton("✏️ تعديل الاسم", callback_data=f"btn_sub_edit:rename:{submenu_id}:{button_id}")],
                [InlineKeyboardButton("📝 تعديل المحتوى", callback_data=f"btn_sub_edit:content:{submenu_id}:{button_id}")],
                [InlineKeyboardButton("🗑️ حذف الزر", callback_data=f"btn_sub_edit:delete:{submenu_id}:{button_id}")],
                [InlineKeyboardButton("🔙 رجوع", callback_data=f"btn_sub:manage:{submenu_id}")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                f"⚙️ **تعديل زر فرعي**\n\n"
                f"🏷️ الاسم: {button['name']}\n"
                f"📝 المحتوى: {button['content'][:50]}...\n"
                f"📍 الموضع: {button['position'] + 1}",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"خطأ في تعديل الزر الفرعي: {e}")
            await update.callback_query.answer("❌ حدث خطأ في التعديل")

class ButtonHandler:
    """معالجة الضغط على الأزرار المخصصة"""

    @staticmethod
    async def handle_custom_button(update: Update, context: ContextTypes.DEFAULT_TYPE, button_id: str):
        """معالجة الضغط على زر مخصص"""
        try:
            logger.info(f"🔍 البحث عن الزر: {button_id}")
            button = ButtonManager.find_button_by_id(button_id)
        
            if not button:
                logger.error(f"❌ الزر غير موجود: {button_id}")
                await update.callback_query.answer("❌ الزر غير موجود")
                return
        
            logger.info(f"✅ وجد الزر: {button['name']}")
            
            # إذا كان زر قائمة فرعية
            if button.get("type") == "submenu":
                await ButtonManager.show_submenu_to_user(update, context, button["id"])
                return
        
            # تنسيق المحتوى مع المتغيرات
            from Admin.InfoManager import format_dynamic_text
            user_id = update.effective_user.id
            user_data = db.get_user(user_id)
        
            formatted_content = format_dynamic_text(
                button["content"],
                {
                    "user_id": user_id,
                    "user_name": update.effective_user.first_name,
                    "points": user_data.get("points", 0),
                    "level_name": db.get_user_level_name(user_id),
                    "active_tasks": len([t for t in db.get_user_tasks(user_id) if t.get("status") == "active"]),
                    "current_date": datetime.now().strftime("%Y-%m-%d"),
                    "total_earned": user_data.get("total_earned", 0),
                    "invites_count": len(user_data.get("invited_users", []))
                }
            )
        
            keyboard = [
                [InlineKeyboardButton("🔙 رجوع", callback_data="member_menu")]
            ]
        
            await update.callback_query.edit_message_text(
                formatted_content,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            logger.info(f"✅ تم عرض محتوى الزر: {button['name']}")
            return True
        
        except Exception as e:
            logger.error(f"❌ خطأ في handle_custom_button: {e}", exc_info=True)
            await update.callback_query.answer("❌ حدث خطأ في المعالجة")
            return False

# معالج الاستدعاءات الرئيسي
async def button_manager_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """المعالج الرئيسي لإدارة الأزرار"""
    query = update.callback_query
    data = query.data
    
    try:
        # التحقق من الصلاحية أولاً
        if not is_user_admin(update.effective_user.id):
            await query.answer("❌ ليس لديك صلاحية للوصول إلى هذه القائمة")
            return
            
        if data == "btn_mgr:main":
            await ButtonManager.main_menu(update, context)
        elif data == "btn_mgr:main_menu":
            await ButtonManager.manage_main_buttons(update, context)
        elif data == "btn_mgr:create":
            await ButtonManager.create_button_start(update, context)
        elif data == "btn_mgr:create_submenu":
            await ButtonManager.create_submenu(update, context)
        elif data.startswith("btn_mgr:edit_custom:"):
            button_id = data.split(":")[2]
            await ButtonManager.edit_custom_button(update, context, button_id)
        elif data.startswith("btn_mgr:edit_protected:"):
            button_id = data.split(":")[2]
            await ButtonManager.edit_protected_button(update, context, button_id)
        elif data.startswith("btn_reorder:"):
            parts = data.split(":")
            if len(parts) >= 3:
                action = parts[1]
                button_id = parts[2]
                await ButtonManager.handle_reorder_action(update, context, action, button_id)
        elif data.startswith("btn_sub:manage:"):
            submenu_id = data.split(":")[2]
            await ButtonManager.manage_submenu(update, context, submenu_id)
        elif data.startswith("btn_sub:add:"):
            submenu_id = data.split(":")[2]
            await ButtonManager.add_submenu_button(update, context, submenu_id)
        elif data.startswith("btn_sub:edit:"):
            parts = data.split(":")
            submenu_id = parts[2]
            button_id = parts[3]
            await ButtonManager.edit_submenu_button(update, context, submenu_id, button_id)
        elif data.startswith("btn_sub:press:"):
            button_id = data.split(":")[2]
            await ButtonHandler.handle_custom_button(update, context, button_id)
        else:
            await query.answer("⚠️ أمر غير معروف")
            
    except Exception as e:
        logger.error(f"خطأ في معالجة استدعاء الزر: {e}")
        await query.answer("❌ حدث خطأ في المعالجة")


