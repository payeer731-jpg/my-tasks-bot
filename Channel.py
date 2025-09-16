# Admin/Channel.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from Data import db
from Decorators import admin_only
import logging

logger = logging.getLogger(__name__)

@admin_only
async def channel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if data == "channel_menu":
        await channel_menu(update, context)
    elif data == "channel_add":
        await add_channel_prompt(update, context)
    elif data == "channel_remove":
        await remove_channel_prompt(update, context)
    elif data == "check_channels":
        await check_channels_status(update, context)
    elif data.startswith("remove_channel_"):
        channel_index = int(data.split("_")[2])
        await remove_channel(update, context, channel_index)

@admin_only
async def channel_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض قائمة قنوات الاشتراك الإجباري"""
    try:
        channels = db.data.get("subscription_channels", [])
        message = "📢 **إدارة قنوات الاشتراك الإجباري:**\n\n"
        
        if channels:
            for i, channel in enumerate(channels, 1):
                # التحقق من حالة القناة
                try:
                    chat = await context.bot.get_chat(channel)
                    status = "✅ نشطة"
                except:
                    status = "❌ غير متاحة"
                
                message += f"{i}. {channel} - {status}\n"
        else:
            message += "📭 لا توجد قنوات حالياً\n"
        
        message += f"\n🔍 **الحالة:** {'✅ مفعل' if channels else '❌ معطل'}"
        message += "\n\n📝 المستخدمون يجب أن يشتركوا في جميع القنوات قبل استخدام البوت"
        
        keyboard = [
            [InlineKeyboardButton("➕ إضافة قناة", callback_data="channel_add")],
            [InlineKeyboardButton("➖ حذف قناة", callback_data="channel_remove")],
            [InlineKeyboardButton("🔄 فحص القنوات", callback_data="check_channels")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"خطأ في channel_menu: {e}")
        await update.callback_query.answer("❌ حدث خطأ في عرض القائمة")

@admin_only
async def add_channel_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مطالبة بإضافة قناة جديدة"""
    try:
        await update.callback_query.edit_message_text(
            "📝 أرسل معرف القناة لإضافتها:\n\n"
            "📋 الأمثلة:\n"
            "• @channel_name\n"
            "• -1001234567890 (للقنوات الخاصة)\n\n"
            "⚙️ تأكد من:\n"
            "• إضافة البوت كمدير في القناة\n"
            "• منح البوت صلاحية رؤية المشتركين",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="channel_menu")]])
        )
        context.user_data['awaiting_channel'] = True
        
    except Exception as e:
        logger.error(f"خطأ في add_channel_prompt: {e}")
        await update.callback_query.answer("❌ حدث خطأ في المعالجة")

@admin_only
async def remove_channel_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مطالبة بحذف قناة"""
    try:
        channels = db.data.get("subscription_channels", [])
        if not channels:
            await update.callback_query.edit_message_text(
                "❌ لا توجد قنوات حالياً",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="channel_menu")]])
            )
            return
        
        keyboard = []
        for i, channel in enumerate(channels):
            try:
                chat = await context.bot.get_chat(channel)
                channel_name = chat.title or channel
                keyboard.append([InlineKeyboardButton(f"🗑️ حذف {channel_name}", callback_data=f"remove_channel_{i}")])
            except:
                keyboard.append([InlineKeyboardButton(f"🗑️ حذف {channel}", callback_data=f"remove_channel_{i}")])
        
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="channel_menu")])
        
        await update.callback_query.edit_message_text(
            "👥 اختر القناة التي تريد حذفها:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        logger.error(f"خطأ في remove_channel_prompt: {e}")
        await update.callback_query.answer("❌ حدث خطأ في المعالجة")

@admin_only
async def remove_channel(update: Update, context: ContextTypes.DEFAULT_TYPE, channel_index):
    """حذف قناة من القائمة"""
    try:
        channels = db.data.get("subscription_channels", [])
        if 0 <= channel_index < len(channels):
            removed_channel = channels.pop(channel_index)
            db.save_data()
            
            # إرسال رسالة تأكيد
            await update.callback_query.answer(f"✅ تم حذف القناة: {removed_channel}")
            
            # تحديث القائمة
            await channel_menu(update, context)
        else:
            await update.callback_query.answer("❌ خطأ في حذف القناة")
            
    except Exception as e:
        logger.error(f"خطأ في remove_channel: {e}")
        await update.callback_query.answer("❌ حدث خطأ في الحذف")

@admin_only
async def check_channels_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فحص حالة جميع القنوات"""
    try:
        channels = db.data.get("subscription_channels", [])
        message = "🔍 **نتائج فحص القنوات:**\n\n"
        
        working_channels = 0
        broken_channels = 0
        
        for channel in channels:
            try:
                chat = await context.bot.get_chat(channel)
                # التحقق من أن البوت مدير في القناة
                try:
                    bot_member = await context.bot.get_chat_member(chat.id, context.bot.id)
                    if bot_member.status in ['administrator', 'creator']:
                        message += f"✅ {channel} - نشطة (البوت مدير)\n"
                        working_channels += 1
                    else:
                        message += f"⚠️ {channel} - البوت ليس مديراً\n"
                        broken_channels += 1
                except:
                    message += f"❌ {channel} - البوت ليس عضوًا\n"
                    broken_channels += 1
                    
            except Exception as e:
                message += f"❌ {channel} - غير متاحة ({str(e)})\n"
                broken_channels += 1
        
        message += f"\n📊 **الإحصائية:**\n✅ نشطة: {working_channels}\n❌ معطلة: {broken_channels}"
        
        await update.callback_query.answer(message, show_alert=True)
        
    except Exception as e:
        logger.error(f"خطأ في check_channels_status: {e}")
        await update.callback_query.answer("❌ حدث خطأ في فحص القنوات")

async def handle_channel_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """معالجة إضافة قناة جديدة"""
    try:
        if context.user_data.get('awaiting_channel'):
            channel_username = text.strip()
            
            # تنظيف المعرف
            if channel_username.startswith('https://t.me/'):
                channel_username = channel_username.replace('https://t.me/', '@')
            elif not channel_username.startswith('@') and not channel_username.startswith('-100'):
                channel_username = '@' + channel_username
            
            # التحقق من صحة القناة
            try:
                chat = await context.bot.get_chat(channel_username)
                
                # التحقق من أن البوت مدير في القناة
                try:
                    bot_member = await context.bot.get_chat_member(chat.id, context.bot.id)
                    if bot_member.status not in ['administrator', 'creator']:
                        await update.message.reply_text(
                            f"❌ البوت ليس مديراً في القناة {channel_username}\n\n"
                            "⚙️ يرجى إضافة البوت كمدير أولاً",
                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="channel_menu")]])
                        )
                        return
                except:
                    await update.message.reply_text(
                        f"❌ البوت ليس عضوًا في القناة {channel_username}\n\n"
                        "⚙️ يرجى إضافة البوت إلى القناة أولاً",
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="channel_menu")]])
                    )
                    return
                
                # إضافة القناة للقائمة إذا لم تكن موجودة
                if 'subscription_channels' not in db.data:
                    db.data['subscription_channels'] = []
                
                channel_id = f"@{chat.username}" if chat.username else f"{-chat.id}"
                
                if channel_id not in db.data['subscription_channels']:
                    db.data['subscription_channels'].append(channel_id)
                    db.save_data()
                    
                    await update.message.reply_text(
                        f"✅ تم إضافة قناة الاشتراك الإجباري: {channel_id}\n\n"
                        f"📋 العنوان: {chat.title}\n"
                        f"👥 عدد الأعضاء: {chat.member_count if hasattr(chat, 'member_count') else 'غير معروف'}",
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📊 العودة للقائمة", callback_data="channel_menu")]])
                    )
                else:
                    await update.message.reply_text(
                        "⚠️ هذه القناة مضافه بالفعل",
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="channel_menu")]])
                    )
                    
            except Exception as e:
                logger.error(f"خطأ في التحقق من القناة: {e}")
                await update.message.reply_text(
                    f"❌ لا يمكن الوصول إلى القناة {channel_username}\n\n"
                    "📋 تأكد من:\n"
                    "• صحة معرف القناة\n"
                    "• أن القناة عامة أو البوت عضو فيها\n"
                    "• أن البوت لديه صلاحية رؤية المشتركين",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="channel_menu")]])
                )
            
            # مسح حالة الانتظار
            context.user_data.pop('awaiting_channel', None)
            
    except Exception as e:
        logger.error(f"خطأ في handle_channel_subscription: {e}")
        await update.message.reply_text(
            "❌ حدث خطأ في إضافة القناة",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="channel_menu")]])
        )

async def check_user_subscription(user_id, context: ContextTypes.DEFAULT_TYPE):
    """التحقق من اشتراك المستخدم في جميع القنوات"""
    try:
        channels = db.data.get("subscription_channels", [])
        
        if not channels:
            return []  # لا توجد قنوات اشتراك إجباري
            
        missing_channels = []
        
        for channel in channels:
            try:
                member = await context.bot.get_chat_member(channel, user_id)
                if member.status in ['left', 'kicked']:
                    missing_channels.append(channel)
            except Exception as e:
                logger.error(f"خطأ في التحقق من الاشتراك في {channel}: {e}")
                # نعتبر القناة غير متاحة ونستمر في التحقق من الباقي
                missing_channels.append(channel)
        
        return missing_channels
        
    except Exception as e:
        logger.error(f"خطأ في check_user_subscription: {e}")
        return []  # في حالة الخطأ، نعتبر أن المستخدم مشترك

async def send_subscription_required_message(update: Update, context: ContextTypes.DEFAULT_TYPE, missing_channels):
    """إرسال رسالة طلب الاشتراك في القنوات بشكل محسن"""
    try:
        message = "📢 **عذراً، يجب الاشتراك في قنوات البوت لتتمكن من استخدامه:**\n\n"
        
        keyboard = []
        for channel in missing_channels:
            try:
                # التحقق من حالة الاشتراك لكل قناة
                chat = await context.bot.get_chat(channel)
                channel_name = chat.title or channel
                
                try:
                    if hasattr(update, 'effective_user'):
                        member = await context.bot.get_chat_member(channel, update.effective_user.id)
                        status = "✅" if member.status not in ['left', 'kicked'] else "❌"
                    else:
                        status = "❌"
                except:
                    status = "❌"
                
                message += f"{status} {channel_name}\n"
                keyboard.append([InlineKeyboardButton(f"{status} اشترك في {channel_name}", url=f"https://t.me/{channel[1:]}")])
                
            except Exception as e:
                logger.error(f"خطأ في التحقق من القناة {channel}: {e}")
                message += f"❌ {channel}\n"
                keyboard.append([InlineKeyboardButton(f"❌ اشترك في {channel}", url=f"https://t.me/{channel[1:]}")])
        
        message += "\n✅ بعد الاشتراك في جميع القنوات، اضغط على زر التحقق أدناه"
        
        keyboard.append([InlineKeyboardButton("🔄 تحقق من الاشتراك", callback_data="check_subscription")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"خطأ في send_subscription_required_message: {e}")

# دالة مساعدة للاستخدام في Admin/Menu.py
async def handle_channel_messages(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """معالجة رسائل إضافة القنوات"""
    await handle_channel_subscription(update, context, text)