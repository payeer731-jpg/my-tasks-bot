# Admin/Invite.py - محدث بنظام الأسهم
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from Data import db
from Decorators import admin_only
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@admin_only
async def invite_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if data == "invite_menu":
        await invite_menu(update, context)
        return True
    elif data == "invite_add_points":
        await add_points_prompt(update, context)
        return True
    elif data == "invite_remove_points":
        await remove_points_prompt(update, context)
        return True
    elif data == "invite_set_points":
        await set_points_prompt(update, context)
        return True
    elif data == "invite_send_all":
        await send_points_all_prompt(update, context)
        return True
    elif data == "invite_reset_all":
        await reset_points_all(update, context)
        return True
    elif data == "confirm_reset_all":
        await confirm_reset_all(update, context)
        return True
    elif data == "invite_toggle_system":
        await toggle_invite_system(update, context)
        return True
    elif data == "invite_arrow_settings":
        await arrow_settings_menu(update, context)
        return True
    elif data == "invite_stats":
        await show_invite_stats(update, context)
        return True
    
    return False

@admin_only
async def invite_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض قائمة إدارة نظام الدعوة والنقاط والأسهم"""
    try:
        current_points = db.get_invite_points()
        total_points = sum(user.get("points", 0) for user in db.data.get("users", {}).values())
        total_users = len(db.data.get("users", {}))
        
        # إحصائيات الأسهم
        arrow_stats = db.get_arrow_stats()
        total_arrows = arrow_stats["total_arrows"]
        
        invite_enabled = db.is_invite_system_enabled()
        status = "✅ مفعل" if invite_enabled else "❌ معطل"
        
        # إعدادات الأسهم
        luck_settings = db.get_luck_arrow_settings()
        invite_bonus_points = luck_settings.get("invite_points", 1)
        invite_arrows = luck_settings.get("invite_arrows", 1)
        
        message = f"""
💰 **إدارة النقاط ونظام الدعوة والأسهم**

• حالة النظام: {status}
• نقاط الدعوة الحالية: {current_points}
• مكافأة الأسهم: {invite_arrows} سهم لكل دعوة
• مكافأة النقاط الإضافية: {invite_bonus_points} نقطة

📊 **الإحصائيات:**
• عدد المستخدمين: {total_users}
• إجمالي النقاط: {total_points}
• إجمالي الأسهم: {total_arrows}

🎯 **اختر الإجراء المطلوب:**
"""
        
        keyboard = [
            # الصف الأول: إدارة النقاط
            [
                InlineKeyboardButton("➕ إضافة نقاط", callback_data="invite_add_points"),
                InlineKeyboardButton("➖ خصم نقاط", callback_data="invite_remove_points")
            ],
            # الصف الثاني: الإرسال الجماعي
            [
                InlineKeyboardButton("🎁 إرسال للجميع", callback_data="invite_send_all"),
                InlineKeyboardButton("🔄 تصفير الجميع", callback_data="invite_reset_all")
            ],
            # الصف الثالث: الإعدادات
            [
                InlineKeyboardButton("🎯 تعيين النقاط", callback_data="invite_set_points"),
                InlineKeyboardButton("🏹 إعدادات الأسهم", callback_data="invite_arrow_settings")
            ],
            # الصف الرابع: التحكم والتقارير
            [
                InlineKeyboardButton(f"🔧 {'تعطيل' if invite_enabled else 'تفعيل'} النظام", callback_data="invite_toggle_system"),
                InlineKeyboardButton("📈 الإحصائيات", callback_data="invite_stats")
            ],
            # زر العودة
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"خطأ في invite_menu: {e}")
        await update.callback_query.answer("❌ حدث خطأ في عرض القائمة")

@admin_only
async def arrow_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """قائمة إعدادات مكافآت الأسهم في الدعوة"""
    try:
        luck_settings = db.get_luck_arrow_settings()
        invite_points = luck_settings.get("invite_points", 1)
        invite_arrows = luck_settings.get("invite_arrows", 1)
        
        message = f"""
🏹 **إعدادات مكافآت الدعوة**

📊 **الإعدادات الحالية:**
• النقاط الإضافية لكل دعوة: {invite_points} نقطة
• الأسهم لكل دعوة: {invite_arrows} سهم

💡 **المكافأة الكلية لكل دعوة:**
• {db.get_invite_points() + invite_points} نقطة
• {invite_arrows} سهم

🎯 **اختر الإعداد لتعديله:**
"""
        
        keyboard = [
            [
                InlineKeyboardButton("📊 نقاط الدعوة", callback_data="set_invite_points"),
                InlineKeyboardButton("🏹 أسهم الدعوة", callback_data="set_invite_arrows")
            ],
            [InlineKeyboardButton("🔙 رجوع", callback_data="invite_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"خطأ في arrow_settings_menu: {e}")
        await update.callback_query.answer("❌ حدث خطأ في المعالجة")

@admin_only
async def toggle_invite_system(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تفعيل أو تعطيل نظام الدعوة"""
    try:
        current_status = db.is_invite_system_enabled()
        new_status = not current_status
        
        if db.toggle_invite_system(new_status):
            status_text = "✅ تم تفعيل نظام الدعوة" if new_status else "❌ تم تعطيل نظام الدعوة"
            await update.callback_query.answer(status_text)
        else:
            await update.callback_query.answer("❌ حدث خطأ في تغيير حالة النظام")
        
        await invite_menu(update, context)
        
    except Exception as e:
        logger.error(f"خطأ في toggle_invite_system: {e}")
        await update.callback_query.answer("❌ حدث خطأ في المعالجة")

@admin_only
async def add_points_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مطالبة بإضافة نقاط لمستخدم"""
    try:
        await update.callback_query.edit_message_text(
            "💰 أرسل ايدي المستخدم وعدد النقاط (مثال: 123456789 10):\n\n"
            "📝 يمكنك إرسال:\n"
            "• ايدي مستخدم + عدد النقاط\n"
            "• 'all' + عدد النقاط لإرسال للجميع",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="invite_menu")]])
        )
        context.user_data['awaiting_add_points'] = True
        
    except Exception as e:
        logger.error(f"خطأ في add_points_prompt: {e}")
        await update.callback_query.answer("❌ حدث خطأ في المعالجة")

@admin_only
async def remove_points_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مطالبة بخصم نقاط من مستخدم"""
    try:
        await update.callback_query.edit_message_text(
            "💸 أرسل ايدي المستخدم وعدد النقاط (مثال: 123456789 5):\n\n"
            "⚠️ سيتم خصم النقاط من رصيد المستخدم",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="invite_menu")]])
        )
        context.user_data['awaiting_remove_points'] = True
        
    except Exception as e:
        logger.error(f"خطأ في remove_points_prompt: {e}")
        await update.callback_query.answer("❌ حدث خطأ في المعالجة")

@admin_only
async def set_points_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مطالبة بتعيين نقاط الدعوة"""
    try:
        current_points = db.get_invite_points()
        
        await update.callback_query.edit_message_text(
            f"🎯 أرسل عدد نقاط الدعوة الجديدة:\n\n"
            f"📊 القيمة الحالية: {current_points} نقطة\n\n"
            "💡 هذه النقاط الأساسية التي يحصل عليها المستخدم عند دعوة كل صديق",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="invite_menu")]])
        )
        context.user_data['awaiting_set_points'] = True
        
    except Exception as e:
        logger.error(f"خطأ في set_points_prompt: {e}")
        await update.callback_query.answer("❌ حدث خطأ في المعالجة")

@admin_only
async def send_points_all_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مطالبة بإرسال نقاط للجميع"""
    try:
        await update.callback_query.edit_message_text(
            "🎁 أرسل عدد النقاط التي تريد إرسالها للجميع:\n\n"
            "📦 سيتم إرسال النقاط لجميع المستخدمين المسجلين",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="invite_menu")]])
        )
        context.user_data['awaiting_send_all'] = True
        
    except Exception as e:
        logger.error(f"خطأ في send_points_all_prompt: {e}")
        await update.callback_query.answer("❌ حدث خطأ في المعالجة")

@admin_only
async def reset_points_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """طلب تأكيد تصفير نقاط جميع المستخدمين"""
    try:
        total_users = len(db.data.get("users", {}))
        total_points = sum(user.get("points", 0) for user in db.data.get("users", {}).values())
        
        message = f"""
⚠️ **تأكيد تصفير النقاط**

❗ **هذا الإجراء لا يمكن التراجع عنه!**

📊 الإحصائيات الحالية:
• 👥 عدد المستخدمين: {total_users}
• 💰 إجمالي النقاط: {total_points}

❌ سيتم حذف جميع النقاط من جميع المستخدمين
🔄 لا يمكن استعادة النقاط بعد التصفير

🔒 هل أنت متأكد منwant to continue?
"""
        
        keyboard = [
            [InlineKeyboardButton("✅ نعم، تصفير جميع النقاط", callback_data="confirm_reset_all")],
            [InlineKeyboardButton("❌ لا، إلغاء العملية", callback_data="invite_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"خطأ في طلب تأكيد التصفير: {e}")
        await update.callback_query.answer("❌ حدث خطأ في المعالجة")

@admin_only
async def confirm_reset_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تأكيد وتنفيذ تصفير النقاط"""
    try:
        query = update.callback_query
        await query.answer()
        
        # تنفيذ التصفير
        success_count = 0
        for user_id, user_data in db.data.get("users", {}).items():
            user_data["points"] = 0
            success_count += 1
        
        db.save_data()
        
        message = f"""
✅ **تم تصفير النقاط بنجاح**

• 👥 عدد المستخدمين: {success_count}
• 💰 تم تصفير جميع النقاط
• ⏰ التاريخ: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

📝 تمت العملية بواسطة: {update.effective_user.first_name}
"""
        
        keyboard = [
            [InlineKeyboardButton("📊 العودة للقائمة", callback_data="invite_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"خطأ في تأكيد التصفير: {e}")
        await update.callback_query.answer("❌ حدث خطأ في تصفير النقاط")

@admin_only
async def show_invite_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض إحصائيات الدعوة المفصلة مع الأسهم"""
    try:
        total_users = len(db.data["users"])
        total_points = sum(user["points"] for user in db.data["users"].values())
        
        # إحصائيات الأسهم
        arrow_stats = db.get_arrow_stats()
        
        # حساب إحصائيات الدعوة
        total_invites = 0
        active_inviters = 0
        top_inviters = []
        
        for user_id, user_data in db.data["users"].items():
            invited_count = len(user_data.get("invited_users", []))
            total_invites += invited_count
            
            if invited_count > 0:
                active_inviters += 1
                top_inviters.append((user_id, invited_count))
        
        # ترتيب أفضل 10 مدعين
        top_inviters.sort(key=lambda x: x[1], reverse=True)
        top_10 = top_inviters[:10]
        
        # إعدادات الأسهم
        luck_settings = db.get_luck_arrow_settings()
        invite_bonus_points = luck_settings.get("invite_points", 1)
        invite_arrows = luck_settings.get("invite_arrows", 1)
        total_reward_points = db.get_invite_points() + invite_bonus_points
        
        message = f"""
📈 **إحصائيات الدعوة والأسهم**

👥 **المستخدمون:**
• الإجمالي: {total_users} مستخدم
• النشطون في الدعوة: {active_inviters} مدعٍ
• إجمالي الدعوات: {total_invites} دعوة

💰 **النقاط:**
• الإجمالي: {total_points} نقطة
• نقاط الدعوة: {total_reward_points} لكل دعوة
• الأسهم: {invite_arrows} سهم لكل دعوة

🏹 **إحصائيات الأسهم:**
• إجمالي الأسهم: {arrow_stats['total_arrows']}
• المستخدمون النشطون: {arrow_stats['active_users']}
• إجمالي الرميات: {arrow_stats['total_spins']}

🏆 **أفضل 10 مدعين:**
"""
        
        if top_10:
            for i, (user_id, count) in enumerate(top_10, 1):
                try:
                    user = await context.bot.get_chat(user_id)
                    username = user.first_name or user_id
                    message += f"{i}. {username}: {count} دعوة\n"
                except:
                    message += f"{i}. {user_id}: {count} دعوة\n"
        else:
            message += "📭 لا توجد دعوات حتى الآن\n"
        
        message += f"\n🔧 **حالة النظام:** {'✅ مفعل' if db.is_invite_system_enabled() else '❌ معطل'}"
        
        keyboard = [
            [InlineKeyboardButton("🔄 تحديث الإحصائيات", callback_data="invite_stats")],
            [InlineKeyboardButton("📊 العودة للقائمة", callback_data="invite_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"خطأ في show_invite_stats: {e}")
        await update.callback_query.answer("❌ حدث خطأ في عرض الإحصائيات")

async def handle_invite_messages(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """معالجة رسائل إدارة الدعوة"""
    try:
        if context.user_data.get('awaiting_add_points'):
            try:
                parts = text.split()
                if len(parts) == 2:
                    user_id = parts[0].strip()
                    points = int(parts[1])
                    
                    if user_id.lower() == 'all':
                        # إرسال للجميع
                        success_count = 0
                        for uid in db.data["users"].keys():
                            if db.add_points_to_user(uid, points):
                                success_count += 1
                        
                        await update.message.reply_text(f"✅ تم إضافة {points} نقطة لـ {success_count} مستخدم")
                    else:
                        # إرسال لمستخدم محدد
                        if db.add_points_to_user(user_id, points):
                            await update.message.reply_text(f"✅ تم إضافة {points} نقطة للمستخدم {user_id}")
                        else:
                            await update.message.reply_text("❌ خطأ في إضافة النقاط. تأكد من صحة ID المستخدم")
                else:
                    await update.message.reply_text("❌ تنسيق غير صحيح. استخدم: ايدي عدد_النقاط أو all عدد_النقاط")
            except ValueError:
                await update.message.reply_text("❌ يجب إدخال رقم صحيح للنقاط")
            except Exception as e:
                logger.error(f"خطأ في إضافة النقاط: {e}")
                await update.message.reply_text("❌ حدث خطأ غير متوقع")
            finally:
                context.user_data.pop('awaiting_add_points', None)
            return
            
        elif context.user_data.get('awaiting_remove_points'):
            try:
                parts = text.split()
                if len(parts) == 2:
                    user_id = parts[0].strip()
                    points = int(parts[1])
                    
                    if db.remove_points_from_user(user_id, points):
                        await update.message.reply_text(f"✅ تم خصم {points} نقطة من المستخدم {user_id}")
                    else:
                        await update.message.reply_text("❌ خطأ في خصم النقاط. تأكد من صحة ID المستخدم")
                else:
                    await update.message.reply_text("❌ تنسيق غير صحيح. استخدم: ايدي عدد_النقاط")
            except ValueError:
                await update.message.reply_text("❌ يجب إدخال رقم صحيح للنقاط")
            except Exception as e:
                logger.error(f"خطأ في خصم النقاط: {e}")
                await update.message.reply_text("❌ حدث خطأ غير متوقع")
            finally:
                context.user_data.pop('awaiting_remove_points', None)
            return
            
        elif context.user_data.get('awaiting_set_points'):
            try:
                points = int(text)
                if points < 0:
                    await update.message.reply_text("❌ يجب أن تكون النقاط أكبر أو تساوي الصفر")
                    return
                    
                if db.set_invite_points(points):
                    await update.message.reply_text(f"✅ تم تعيين نقاط الدعوة إلى {points}")
                else:
                    await update.message.reply_text("❌ خطأ في تعيين النقاط")
            except ValueError:
                await update.message.reply_text("❌ يجب إدخال رقم صحيح")
            except Exception as e:
                logger.error(f"خطأ في تعيين نقاط الدعوة: {e}")
                await update.message.reply_text("❌ حدث خطأ غير متوقع")
            finally:
                context.user_data.pop('awaiting_set_points', None)
            return
            
        elif context.user_data.get('awaiting_send_all'):
            try:
                points = int(text)
                success_count = 0
                for user_id in db.data["users"].keys():
                    if db.add_points_to_user(user_id, points):
                        success_count += 1
                
                await update.message.reply_text(f"✅ تم إضافة {points} نقطة لـ {success_count} مستخدم")
            except ValueError:
                await update.message.reply_text("❌ يجب إدخال رقم صحيح")
            except Exception as e:
                logger.error(f"خطأ في إرسال النقاط للجميع: {e}")
                await update.message.reply_text("❌ حدث خطأ أثناء الإرسال")
            finally:
                context.user_data.pop('awaiting_send_all', None)
            return
            
    except Exception as e:
        logger.error(f"خطأ في handle_invite_messages: {e}")
        await update.message.reply_text("❌ حدث خطأ في المعالجة")