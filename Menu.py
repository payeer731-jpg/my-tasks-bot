# Admin/Menu.py - الجزء 1/2
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from Data import db
from Config import OWNER_ID
from Decorators import admin_only
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@admin_only
async def show_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        
        # إحصائيات سريعة
        total_users = len(db.data["users"])
        total_tasks = len(db.data.get("tasks_new", []))
        total_points = sum(user["points"] for user in db.data["users"].values())
        
        # إنشاء القائمة الجديدة مع أزرار بكامل العرض
        keyboard = []
        
        # الصف 1: إدارة المديرين (للمالك فقط)
        if user_id == OWNER_ID:
            keyboard.append([InlineKeyboardButton("👥 ادارة المديرين", callback_data="admins_list")])
        
        # الصف 2: إدارة الحظر - إدارة المهام
        keyboard.append([
            InlineKeyboardButton("🚫 ادارة الحظر", callback_data="blocked_list"),
            InlineKeyboardButton("📋 ادارة المهام", callback_data="tasks_menu")
        ])
        
        # الصف 3: إدارة النقاط والدعوة
        keyboard.append([
            InlineKeyboardButton("💰 ادارة النقاط", callback_data="invite_menu"),
            InlineKeyboardButton("📊 إحصائيات الدعوة", callback_data="invite_stats")
        ])
        
        # الصف 4: إدارة القنوات - إدارة الكابتشا
        keyboard.append([
            InlineKeyboardButton("📺 ادارة القنوات", callback_data="channel_menu"),
            InlineKeyboardButton("💰 إعدادات الأرباح", callback_data="profit_settings_menu")
        ])
        
        # الصف 5: إدارة الإذاعة والإحصائيات
        keyboard.append([
            InlineKeyboardButton("📢 ادارة الاذاعة", callback_data="moder_menu"),
            InlineKeyboardButton("📈 الاحصائيات", callback_data="moder_stats")
        ])
        
        # الصف 6: قنوات المهام وأكواد الهدايا (للمالك فقط)
        if user_id == OWNER_ID:
            keyboard.append([
                InlineKeyboardButton("📊 قنوات المهام", callback_data="tasks_channels_menu"),
                InlineKeyboardButton("🎁 ادارة الهدايا", callback_data="gift_codes_menu")
            ])
        # الصف 7: إدارة المعلومات (للمالك فقط) - الزر الجديد
        if user_id == OWNER_ID:
            keyboard.append([InlineKeyboardButton("🎛️ إدارة الأزرار", callback_data="button_manager_menu")])
        
        # الصف 8: إعادة تشغيل - رجوع
        keyboard.append([
            InlineKeyboardButton("🔄 اعادة تشغيل", callback_data="admin_restart"),
            InlineKeyboardButton("📌 إعدادات التثبيت", callback_data="pin_settings_menu")
        ])

        keyboard.append([
            InlineKeyboardButton("🎯 ادارة الأسهم", callback_data="luck_arrow_admin"),
            InlineKeyboardButton("🎁 ادارة الهدايا", callback_data="gift_codes_menu")
       ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = f"""
🎛️ **لوحة تحكم المدير**

📊 **إحصائيات سريعة:**
• 👥 المستخدمون: {total_users}
• 📋 المهام: {total_tasks}
• 💰 النقاط: {total_points}

🎯 **اختر من القائمة:**
"""
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"خطأ في show_admin_menu: {e}")
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.answer("❌ حدث خطأ في عرض القائمة")

@admin_only
async def admin_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if data == "admin_menu":
        await show_admin_menu(update, context)
    
    elif data == "button_manager_menu":  # ✅ المعالج الجديد
        try:
            from Admin.ButtonManager import ButtonManager
            await ButtonManager.main_menu(update, context)
        except ImportError:
            await query.answer("❌ نظام إدارة الأزرار غير متوفر حالياً")
        except Exception as e:
            logger.error(f"خطأ في تحميل إدارة الأزرار: {e}")
            await query.answer("❌ حدث خطأ في تحميل النظام")
    
    elif data == "moder_stats":
        from Admin.Moder import show_stats
        await show_stats(update, context)
    
    elif data == "blocked_list":
        from Admin.Block import show_blocked_list
        await show_blocked_list(update, context)
    
    elif data == "admin_settings":
        from Admin.Settings import show_admin_settings
        await show_admin_settings(update, context)
    
    else:
        await query.answer("⚠️ الأمر غير معروف")

async def handle_admin_messages(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    # التحقق من أن الرسالة في محادثة خاصة
    if update.message.chat.type != "private":
        return
        
    user_id = update.effective_user.id
    text = update.message.text
    
    # تسجيل المعلومات للتصحيح
    logger.info(f"تم استقبال رسالة من المدير {user_id}: {text}")
    
    # تخطي المعالجة إذا كان المستخدم في منتصف إنشاء مهمة
    if context.user_data.get('step', '').startswith('awaiting_') and str(user_id) not in db.get_admins() and user_id != OWNER_ID:
        return
    
    # معالجة البحث عن المهام أولاً
    if context.user_data.get('awaiting_task_search'):
        try:
            from Admin.Tasks import handle_task_search
            await handle_task_search(update, context, text)
            return
        except Exception as e:
            logger.error(f"خطأ في معالجة البحث: {e}")
            await update.message.reply_text("❌ حدث خطأ في البحث عن المهمة")
        return
    
    # 1. معالجة إضافة المديرين
    if context.user_data.get('awaiting_admin_id'):
        try:
            new_admin_id = int(text)
            if db.add_admin(str(new_admin_id)):
                await update.message.reply_text(f"✅ تم إضافة المدير بنجاح (ID: {new_admin_id})")
            else:
                await update.message.reply_text("⚠️ المستخدم مدير بالفعل")
        except ValueError:
            await update.message.reply_text("❌ يجب إدخال رقم صحيح")
        context.user_data.pop('awaiting_admin_id', None)
        return
            
    # معالجات رسائل إدارة المعلومات - أضف هنا
    elif context.user_data.get('editing_welcome_message'):
        try:
            db.data["welcome_message"] = text
            db.save_data()
            await update.message.reply_text(
                "✅ تم تحديث رسالة الترحيب بنجاح",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📋 العودة", callback_data="info_manager_menu")]])
            )
            context.user_data.pop('editing_welcome_message', None)
            return
        except Exception as e:
            logger.error(f"خطأ في تحديث رسالة الترحيب: {e}")
            await update.message.reply_text("❌ حدث خطأ في تحديث رسالة الترحيب")
            context.user_data.pop('editing_welcome_message', None)
            return

    elif context.user_data.get('editing_terms_text'):
        try:
            db.data["terms_text"] = text
            db.save_data()
            await update.message.reply_text(
                "✅ تم تحديث شروط البوت بنجاح",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📋 العودة", callback_data="info_manager_menu")]])
            )
            context.user_data.pop('editing_terms_text', None)
            return
        except Exception as e:
            logger.error(f"خطأ في تحديث الشروط: {e}")
            await update.message.reply_text("❌ حدث خطأ في تحديث الشروط")
            return

    elif context.user_data.get('editing_invite_message'):
        try:
            db.data["invite_message"] = text
            db.save_data()
            await update.message.reply_text(
                "✅ تم تحديث رسالة الدعوة بنجاح",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📋 العودة", callback_data="info_manager_menu")]])
            )
            context.user_data.pop('editing_invite_message', None)
            return
        except Exception as e:
            logger.error(f"خطأ في تحديث رسالة الدعوة: {e}")
            await update.message.reply_text("❌ حدث خطأ في تحديث رسالة الدعوة")
            context.user_data.pop('editing_invite_message', None)
            return

    elif context.user_data.get('editing_support_info'):
        try:
            db.data["support_info"] = text
            db.save_data()
            await update.message.reply_text(
                "✅ تم تحديث معلومات الدعم بنجاح",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📋 العودة", callback_data="info_manager_menu")]])
            )
            context.user_data.pop('editing_support_info', None)
            return
        except Exception as e:
            logger.error(f"خطأ في تحديث معلومات الدعم: {e}")
            await update.message.reply_text("❌ حدث خطأ في تحديث معلومات الدعم")
            context.user_data.pop('editing_support_info', None)
            return

    elif context.user_data.get('editing_terms_info'):
        try:
            db.data["terms_info"] = text
            db.save_data()
            await update.message.reply_text(
                "✅ تم تحديث شروط الاستخدام بنجاح",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📋 العودة", callback_data="info_manager_menu")]])
            )
            context.user_data.pop('editing_terms_info', None)
            return
        except Exception as e:
            logger.error(f"خطأ في تحديث شروط الاستخدام: {e}")
            await update.message.reply_text("❌ حدث خطأ في تحديث شروط الاستخدام")
            context.user_data.pop('editing_terms_info', None)
            return

    elif context.user_data.get('awaiting_terms_edit'):
        try:
            db.data["terms_info"] = text
            db.save_data()
            await update.message.reply_text(
                "✅ تم تحديث شروط الاستخدام بنجاح",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📋 العودة", callback_data="info_manager_menu")]])
            )
            context.user_data.pop('awaiting_terms_edit', None)
            return
        except Exception as e:
            logger.error(f"خطأ في تحديث الشروط: {e}")
            await update.message.reply_text("❌ حدث خطأ في التحديث")
            context.user_data.pop('awaiting_terms_edit', None)
            return

# Admin/Menu.py - الجزء 2/2
    elif context.user_data.get('awaiting_remove_admin'):
        try:
            admin_id = int(text)
            if admin_id == OWNER_ID:
                await update.message.reply_text("❌ لا يمكن حذف المالك")
            elif db.remove_admin(str(admin_id)):
                await update.message.reply_text(f"✅ تم حذف المدير (ID: {admin_id})")
            else:
                await update.message.reply_text("⚠️ المستخدم ليس مديراً")
        except ValueError:
            await update.message.reply_text("❌ يجب إدخال رقم صحيح")
        context.user_data.pop('awaiting_remove_admin', None)
        return
    
    # 2. معالجة الحظر وفك الحظر
    elif context.user_data.get('awaiting_block_id'):
        try:
            block_id = int(text)
            
            # منع حظر النفس
            if block_id == user_id:
                await update.message.reply_text("❌ لا يمكنك حظر نفسك")
                context.user_data.pop('awaiting_block_id', None)
                return
                
            # منع حظر المالك
            if block_id == OWNER_ID:
                await update.message.reply_text("❌ لا يمكنك حظر المالك")
                context.user_data.pop('awaiting_block_id', None)
                return
                
            # منع حظر أدمن آخر (ما لم يكن المستخدم هو المالك)
            if str(block_id) in db.get_admins() and user_id != OWNER_ID:
                await update.message.reply_text("❌ لا يمكنك حظر مدير آخر")
                context.user_data.pop('awaiting_block_id', None)
                return
                
            if db.block_user(str(block_id)):
                await update.message.reply_text(f"✅ تم حظر المستخدم (ID: {block_id})")
            else:
                await update.message.reply_text("⚠️ المستخدم محظور بالفعل")
        except ValueError:
            await update.message.reply_text("❌ يجب إدخال رقم صحيح")
        context.user_data.pop('awaiting_block_id', None)
        return
    
    elif context.user_data.get('awaiting_unblock_id'):
        try:
            unblock_id = int(text)
            
            if db.unblock_user(str(unblock_id)):
                await update.message.reply_text(f"✅ تم فك حظر المستخدم (ID: {unblock_id})")
            else:
                await update.message.reply_text("⚠️ المستخدم غير محظور")
        except ValueError:
            await update.message.reply_text("❌ يجب إدخال رقم صحيح")
        context.user_data.pop('awaiting_unblock_id', None)
        return
    
    # 3. معالجة إعدادات قنوات المهام (للمالك فقط)
    elif user_id == OWNER_ID and (context.user_data.get('awaiting_tasks_channel') or context.user_data.get('awaiting_completed_channel')):
        from Admin.TasksChannels import handle_tasks_channels_settings
        await handle_tasks_channels_settings(update, context, text)
        return
    
    # 4. معالجة إنشاء أكواد الهدايا (للمالك فقط)
    elif user_id == OWNER_ID and context.user_data.get('awaiting_gift_points'):
        try:
            points = int(text)
            if points <= 0:
                await update.message.reply_text("❌ يجب أن تكون النقاط أكبر من الصفر")
                return
                
            context.user_data['gift_data'] = {'points': points}
            context.user_data['awaiting_gift_max_uses'] = True
            context.user_data.pop('awaiting_gift_points', None)
            
            await update.message.reply_text(
                "👥 أرسل الحد الأقصى لعدد المستخدمين الذين يمكنهم استخدام هذا الكود:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 إلغاء", callback_data="gift_codes_menu")]])
            )
        except ValueError:
            await update.message.reply_text("❌ يجب إدخال رقم صحيح")
        return
    
    elif user_id == OWNER_ID and context.user_data.get('awaiting_gift_max_uses'):
        try:
            max_uses = int(text)
            if max_uses <= 0:
                await update.message.reply_text("❌ يجب أن يكون العدد أكبر من الصفر")
                return
                
            context.user_data['gift_data']['max_uses'] = max_uses
            context.user_data['awaiting_gift_code'] = True
            context.user_data.pop('awaiting_gift_max_uses', None)
            
            # إنشاء كود تلقائي
            auto_code = db.generate_gift_code()
            context.user_data['gift_data']['auto_code'] = auto_code
            
            await update.message.reply_text(
                f"🔢 الكود التلقائي: `{auto_code}`\n\n"
                "📝 يمكنك استخدام هذا الكود أو إرسال كود مخصص:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ استخدام الكود التلقائي", callback_data=f"use_auto_code_{auto_code}")],
                    [InlineKeyboardButton("📝 إدخال كود مخصص", callback_data="enter_custom_code")],
                    [InlineKeyboardButton("🔙 إلغاء", callback_data="gift_codes_menu")]
                ]),
                parse_mode='Markdown'
            )
        except ValueError:
            await update.message.reply_text("❌ يجب إدخال رقم صحيح")
        return
    
    elif user_id == OWNER_ID and context.user_data.get('awaiting_gift_custom_code'):
        try:
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
                'created_by': user_id
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
            logger.error(f"خطأ في إنشاء كود الهدية: {e}")
            await update.message.reply_text("❌ حدث خطأ في إنشاء الكود")
        return
    
    # 5. معالجة إدارة النقاط والدعوة
    elif context.user_data.get('awaiting_add_points'):
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
                    return
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
    
    # 6. معالجة الإذاعة
    elif context.user_data.get('awaiting_broadcast'):
        users = db.data["users"].keys()
        success = 0
        for user in users:
            try:
                await context.bot.send_message(chat_id=user, text=f"📢 إشعار من الإدارة:\n\n{text}")
                success += 1
            except:
                continue
        await update.message.reply_text(f"✅ تم إرسال الإذاعة إلى {success} مستخدم")
        context.user_data.pop('awaiting_broadcast', None)
        return
    
    # 7. معالجة الشكاوى
    elif context.user_data.get('awaiting_complaint'):
        # إرسال الشكوى للمالك
        try:
            await context.bot.send_message(chat_id=OWNER_ID, text=f"📞 شكوى من المستخدم {user_id}:\n\n{text}")
            await update.message.reply_text("✅ تم إرسال شكواك بنجاح، سيتم الرد عليك قريباً")
        except:
            await update.message.reply_text("❌ حدث خطأ في إرسال الشكوى")
        context.user_data.pop('awaiting_complaint', None)
        return
    
    elif context.user_data.get('awaiting_channel'):
        from Admin.Channel import handle_channel_subscription
        await handle_channel_subscription(update, context, text)
        return

    # 8. معالجة إضافة القنوات
    elif context.user_data.get('awaiting_channel'):
        try:
            # إضافة قناة جديدة للاشتراك الإجباري
            channel_username = text.strip()
            if not channel_username.startswith('@'):
                channel_username = '@' + channel_username
                
            # إضافة القناة للقائمة إذا لم تكن موجودة
            if 'subscription_channels' not in db.data:
                db.data['subscription_channels'] = []
                
            if channel_username not in db.data['subscription_channels']:
                db.data['subscription_channels'].append(channel_username)
                db.save_data()
                await update.message.reply_text(f"✅ تم إضافة قناة الاشتراك الإجباري: {channel_username}")
            else:
                await update.message.reply_text("⚠️ هذه القناة مضافه بالفعل")
                
        except Exception as e:
            await update.message.reply_text("❌ حدث خطأ في إضافة القناة")
            print(f"Error adding channel: {e}")
        finally:
            context.user_data.pop('awaiting_channel', None)
        return

    elif context.user_data.get('awaiting_profit_percentage') or context.user_data.get('awaiting_task_limits'):
        from Admin.ProfitSettings import handle_profit_settings_messages
        await handle_profit_settings_messages(update, context, text)
        return

    elif (context.user_data.get('awaiting_pin_price') or 
          context.user_data.get('awaiting_pin_duration') or 
          context.user_data.get('awaiting_max_pins')):
        from Admin.PinSettings import handle_pin_settings_messages
        await handle_pin_settings_messages(update, context, text)
        return
    
    else:
        # إذا لم يكن هناك أمر معروف، تجاهل الرسالة
        logger.info("لم يتم التعرف على الأمر، تجاهل الرسالة")
        pass
