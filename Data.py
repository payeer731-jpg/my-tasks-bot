# Data.py - الجزء 1/7 - محدث بنظام سهم الحظ
# الملف الكامل مع نظام الحجز والتوقيت + أكواد الهدايا + الدعوة + سهم الحظ
import json
import os
import random
import string
from datetime import datetime, timedelta
import threading
import time
import logging
import asyncio

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self, file_path='Data.json'):
        self.file_path = file_path
        self.data = self.load_data()
        self.task_reservations = {}
        self.proof_timeouts = {}
        
        # ✅ تهيئة هياكل البيانات الجديدة
        self.initialize_new_structures()
        self.initialize_luck_arrow_system()  # ✅ تهيئة نظام سهم الحظ
        
        self.start_auto_save()
        self.start_reservation_cleanup()
        self.start_proof_timeout_checker()
        self.start_pin_cleanup()
        self.start_arrow_cleanup()  # ✅ بدء تنظيف الأسهم اليومي
    
    def initialize_luck_arrow_system(self):
        """تهيئة نظام سهم الحظ"""
        if "luck_arrow_settings" not in self.data:
            self.data["luck_arrow_settings"] = {
                "total_arrows": 0,
                "used_arrows": 0,
                "box_open": True,
                "daily_spin_limit": 10,
                "invite_points": 1,
                "invite_arrows": 1,
                "prizes": [ ]
            }
        
        if "luck_arrows" not in self.data:
            self.data["luck_arrows"] = {}
    
    def initialize_new_structures(self):
        """تهيئة هياكل البيانات الجديدة للمستويات والإحصائيات"""
        if "level_system" not in self.data:
            self.data["level_system"] = {
                "enabled": True,
                "levels": {
                    0: {"name": "مبتدئ 🌱", "color": "#808080", "benefits": []},
                    100: {"name": "نشط ⭐", "color": "#00FF00", "benefits": ["خصم 5% على المهام"]},
                    500: {"name": "محترف 🏆", "color": "#0000FF", "benefits": ["خصم 10% على المهام", "أولوية في الدعم"]},
                    1000: {"name": "خبير 👑", "color": "#FFD700", "benefits": ["خصم 15% على المهام", "مهام حصرية", "دعم متميز"]},
                    5000: {"name": "أسطورة 🚀", "color": "#FF0000", "benefits": ["خصم 20% على المهام", "ميزانية تثبيت مجانية", "مدير فخري"]}
                }
            }
        
        if "user_stats" not in self.data:
            self.data["user_stats"] = {}
        
        # ✅ التأكد من وجود جميع الحقول في إحصائيات المستخدم
        for user_id, user_data in self.data.get("users", {}).items():
            if user_id not in self.data["user_stats"]:
                self.data["user_stats"][user_id] = {
                    "completed_tasks": 0,
                    "total_earned": 0,
                    "level_ups": 0,
                    "earning_transactions": 0,
                    "invites_count": len(user_data.get("invited_users", [])),
                    "tasks_created": len([t for t in self.data.get("tasks_new", []) if t.get("owner_id") == user_id])
                }
        
        # ✅ تهيئة جميع أنواع النصوص لضمان عدم وجود قيم فارغة
        text_types = [
            "welcome_message", "invite_message", "support_info", 
            "terms_info", "user_guide_text", "exchange_text"
        ]
        
        default_texts = {
            "welcome_message": "🎊 مرحباً بك في بوت المهام!\n\n👤 معلومات حسابك:\n├─ 🆔 ايدي الحساب: {user_id}\n├─ 💰 رصيد النقاط: {points} نقطة\n├─ 📊 المهام المتاحة: {active_tasks} مهمة\n└─ 🎯 المستوى: {level_name}\n\n🚀 ابدأ رحلتك الآن!",
            "invite_message": "🎉 تم دخولك عبر دعوة من {inviter_name}!\n\n💰 حصلت على {points} نقطة ترحيب!",
            "support_info": "📞 للاستفسارات والمساعدة: @E8EOE\n\n👤 ايدي حسابك: {user_id}\n💰 نقاطك: {points}",
            "terms_info": "📜 الشروط والأحكام:\n\n👤 المستخدم: {user_name}\n🆔 الايدي: {user_id}\n📅 تاريخ القبول: {current_date}",
            "user_guide_text": "📖 دليل الاستخدام:\n\n👤 مرحباً {user_name}!\n💰 نقاطك الحالية: {points}\n🎯 مستواك: {level_name}",
            "exchange_text": "💱 استبدال النقاط:\n\n👤 المستخدم: {user_name}\n💰 الرصيد: {points} نقطة\n🆔 الايدي: {user_id}"
        }
        
        for text_type in text_types:
            if text_type not in self.data:
                self.data[text_type] = default_texts.get(text_type, "أهلاً بك!")
        
        # ✅ ✅ ✅ إضافة نظام الأزرار الجديد هنا
        if "button_system" not in self.data:
            self.data["button_system"] = {
                "main_menu_buttons": [],
                "protected_buttons": {
                    "member_tasks_view": {"name": "📋 عرض المهام", "position": 0},
                    "search_tasks": {"name": "🔍 بحث سريع", "position": 1},
                    "show_task_types": {"name": "➕ إضافة مهمة", "position": 2},
                    "member_my_tasks": {"name": "📊 مهامي", "position": 3},
                    "member_invite_points": {"name": "💰 نقاطي", "position": 4},
                    "member_luck_arrow": {"name": "🎯 سهم الحظ", "position": 5},
                    "member_gift_code": {"name": "🎁 كود هدية", "position": 6},
                    "member_invite_link": {"name": "📨 رابط الدعوة", "position": 7},
                    "member_level_info": {"name": "🏆 مستواي", "position": 8}

                },
                "button_counter": 0,
                "button_categories": {}
            }
    
    def load_data(self):
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    defaults = {
                        "subscription_channels": [],
                        "captcha_enabled": False,
                        "verified_users": [],
                        "channel_tasks": {},
                        "user_tasks": {},
                        "invite_points": 5,
                        "invite_system_enabled": True,
                        "tasks": [],
                        "tasks_new": [],
                        "proofs": [],
                        "task_categories": ["telegram", "whatsapp", "instagram", "facebook", "youtube", "tiktok", "website"],
                        "activity_log": [],
                        "backup_count": 0,
                        "pending_task_moves": [],
                        "gift_codes": {},
                        "accepted_terms_users": [],
                        "pending_invites": {},
                        "terms_text": "شروط وأحكام استخدام البوت\n\nباستخدامك لهذا البوت، فإنك توافق على الالتزام بالشروط التالية:\n\n1. الالتزام بالأدب والاحترام في التعامل\n2. عدم نشر محتوى غير أخلاقي أو مسيء\n3. عدم استخدام البوت لأغراض غير قانونية\n4. الإدارة تحتفظ بالحق في حظر أي مستخدم يخالف الشروط\n5. النقاط غير قابلة للاسترداد أو التحويل بين الحسابات\n",
                        "pin_settings": {
                            "pin_price": 10,
                            "pin_duration": 24,
                            "max_pins": 5
                        },
                        "pinned_tasks": {},
                        # ✅ الإضافات الجديدة
                        "level_system": {
                            "enabled": True,
                            "levels": {
                                0: {"name": "مبتدئ 🌱", "color": "#808080", "benefits": []},
                                100: {"name": "نشط ⭐", "color": "#00FF00", "benefits": ["خصم 5% على المهام"]},
                                500: {"name": "محترف 🏆", "color": "#0000FF", "benefits": ["خصم 10% على المهام", "أولوية في الدعم"]},
                                1000: {"name": "خبير 👑", "color": "#FFD700", "benefits": ["خصم 15% على المهام", "مهام حصرية", "دعم متميز"]},
                                5000: {"name": "أسطورة 🚀", "color": "#FF0000", "benefits": ["خصم 20% على المهام", "ميزانية تثبيت مجانية", "مدير فخري"]}
                            }
                        },
                        "user_stats": {},
                        # ✅ نظام سهم الحظ الجديد
                        "luck_arrow_settings": {
                            "total_arrows": 10000,
                            "used_arrows": 0,
                            "box_open": True,
                            "daily_spin_limit": 10,
                            "invite_points": 1,
                            "invite_arrows": 1,
                            "prizes": [
                                {"type": "points", "value": 10, "probability": 30},
                                {"type": "points", "value": 25, "probability": 20},
                                {"type": "points", "value": 50, "probability": 10},
                                {"type": "gift_code", "value": 100, "probability": 5},
                                {"type": "arrow", "value": 1, "probability": 15},
                                {"type": "nothing", "value": 0, "probability": 20}
                            ]
                        },
                        "luck_arrows": {},
                        # ✅ تهيئة أنواع النصوص لضمان عدم وجود قيم فارغة
                        "welcome_message": "🎊 مرحباً بك في بوت المهام!\n\n👤 معلومات حسابك:\n├─ 🆔 ايدي الحساب: {user_id}\n├─ 💰 رصيد النقاط: {points} نقطة\n├─ 📊 المهام المتاحة: {active_tasks} مهمة\n└─ 🎯 المستوى: {level_name}\n\n🚀 ابدأ رحلتك الآن!",
                        "invite_message": "🎉 تم دخولك عبر دعوة من {inviter_name}!\n\n💰 حصلت على {points} نقطة ترحيب!",
                        "support_info": "📞 للاستفسارات والمساعدة: @E8EOE\n\n👤 ايدي حسابك: {user_id}\n💰 نقاطك: {points}",
                        "terms_info": "📜 الشروط والأحكام:\n\n👤 المستخدم: {user_name}\n🆔 الايدي: {user_id}\n📅 تاريخ القبول: {current_date}",
                        "user_guide_text": "📖 دليل الاستخدام:\n\n👤 مرحباً {user_name}!\n💰 نقاطك الحالية: {points}\n🎯 مستواك: {level_name}",
                        "exchange_text": "💱 استبدال النقاط:\n\n👤 المستخدم: {user_name}\n💰 الرصيد: {points} نقطة\n🆔 الايدي: {user_id}",
                        # ✅ ✅ ✅ إضافة نظام الأزرار إلى الافتراضيات
                        "button_system": {
                            "main_menu_buttons": [],
                            "protected_buttons": {
                                "member_tasks_view": {"name": "📋 عرض المهام", "position": 0},
                                "search_tasks": {"name": "🔍 بحث سريع", "position": 1},
                                "show_task_types": {"name": "➕ إضافة مهمة", "position": 2},
                                "member_my_tasks": {"name": "📊 مهامي", "position": 3},
                                "member_invite_points": {"name": "💰 نقاطي", "position": 4},
                    "member_luck_arrow": {"name": "🎯 سهم الحظ", "position": 5},
                                "member_gift_code": {"name": "🎁 كود هدية", "position": 6},
                                "member_invite_link": {"name": "📨 رابط الدعوة", "position": 7},
                                "member_level_info": {"name": "🏆 مستواي", "position": 8}
                            },
                            "button_counter": 0,
                            "button_categories": {}
                        }
                    }
                    
                    for key, default_value in defaults.items():
                        if key not in data:
                            data[key] = default_value
                    
                    return data
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        
        # في حالة الخطأ، نرجع البيانات الافتراضية
        defaults = {
            "users": {},
            "admins": [],
            "blocked_users": [],
            "tasks": [],
            "tasks_new": [],
            "proofs": [],
            "invite_points": 5,
            "invite_system_enabled": True,
            "subscription_channels": [],
            "captcha_enabled": False,
            "verified_users": [],
            "channel_tasks": {},
            "user_tasks": {},
            "task_categories": ["telegram", "whatsapp", "instagram", "facebook", "youtube", "tiktok", "website"],
            "activity_log": [],
            "backup_count": 0,
            "pending_task_moves": [],
            "gift_codes": {},
            "accepted_terms_users": [],
            "pending_invites": {},
            "terms_text": "شروط وأحكام استخدام البوت\n\nباستخدامك لهذا البوت، فإنك توافق على الالتزام بالشروط التالية:\n\n1. الالتزام بالأدب والاحترام في التعامل\n2. عدم نشر محتوى غير أخلاقي أو مسيء\n3. عدم استخدام البوت لأغراض غير قانونية\n4. الإدارة تحفظ بالحق في حظر أي مستخدم يخالف الشروط\n5. النقاط غير قابلة للاسترداد أو التحويل بين الحسابات\n",
            "pin_settings": {
                "pin_price": 10,
                "pin_duration": 24,
                "max_pins": 5
            },
            "pinned_tasks": {},
            "level_system": {
                "enabled": True,
                "levels": {
                    0: {"name": "مبتدئ 🌱", "color": "#808080", "benefits": []},
                    100: {"name": "نشط ⭐", "color": "#00FF00", "benefits": ["خصم 5% على المهام"]},
                    500: {"name": "محترف 🏆", "color": "#0000FF", "benefits": ["خصم 10% على المهام", "أولوية في الدعم"]},
                    1000: {"name": "خبير 👑", "color": "#FFD700", "benefits": ["خصم 15% على المهام", "مهام حصرية", "دعم متميز"]},
                    5000: {"name": "أسطورة 🚀", "color": "#FF0000", "benefits": ["خصم 20% على المهام", "ميزانية تثبيت مجانية", "مدير فخري"]}
                }
            },
            "user_stats": {},
            # ✅ نظام سهم الحظ الجديد
            "luck_arrow_settings": {
                "total_arrows": 10000,
                "used_arrows": 0,
                "box_open": True,
                "daily_spin_limit": 10,
                "invite_points": 1,
                "invite_arrows": 1,
                "prizes": [
                    {"type": "points", "value": 10, "probability": 30},
                    {"type": "points", "value": 25, "probability": 20},
                    {"type": "points", "value": 50, "probability": 10},
                    {"type": "gift_code", "value": 100, "probability": 5},
                    {"type": "arrow", "value": 1, "probability": 15},
                    {"type": "nothing", "value": 0, "probability": 20}
                ]
            },
            "luck_arrows": {},
            "welcome_message": "🎊 مرحباً بك في بوت المهام!\n\n👤 معلومات حسابك:\n├─ 🆔 ايدي الحساب: {user_id}\n├─ 💰 رصيد النقاط: {points} نقطة\n├─ 📊 المهام المتاحة: {active_tasks} مهمة\n└─ 🎯 المستوى: {level_name}\n\n🚀 ابدأ رحلتك الآن!",
            "invite_message": "🎉 تم دخولك عبر دعوة من {inviter_name}!\n\n💰 حصلت على {points} نقطة ترحيب!",
            "support_info": "📞 للاستفسارات والمساعدة: @E8EOE\n\n👤 ايدي حسابك: {user_id}\n💰 نقاطك: {points}",
            "terms_info": "📜 الشروط والأحكام:\n\n👤 المستخدم: {user_name}\n🆔 الايدي: {user_id}\n📅 تاريخ القبول: {current_date}",
            "user_guide_text": "📖 دليل الاستخدام:\n\n👤 مرحباً {user_name}!\n💰 نقاطك الحالية: {points}\n🎯 مستواك: {level_name}",
            "exchange_text": "💱 استبدال النقاط:\n\n👤 المستخدم: {user_name}\n💰 الرصيد: {points} نقطة\n🆔 الايدي: {user_id}",
            "button_system": {
                "main_menu_buttons": [],
                "protected_buttons": {
                    "member_tasks_view": {"name": "📋 عرض المهام", "position": 0},
                    "search_tasks": {"name": "🔍 بحث سريع", "position": 1},
                    "show_task_types": {"name": "➕ إضافة مهمة", "position": 2},
                    "member_my_tasks": {"name": "📊 مهامي", "position": 3},
                    "member_invite_points": {"name": "💰 نقاطي", "position": 4},
                    "member_luck_arrow": {"name": "🎯 سهم الحظ", "position": 5},
                    "member_gift_code": {"name": "🎁 كود هدية", "position": 6},
                    "member_invite_link": {"name": "📨 رابط الدعوة", "position": 7},
                    "member_level_info": {"name": "🏆 مستواي", "position": 8}

                },
                "button_counter": 0,
                "button_categories": {}
            }
        }
        return defaults

    def save_data(self):
        try:
            self.create_backup()
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
            self.log_activity("system", "data_saved", "تم حفظ البيانات بنجاح")
            return True
        except Exception as e:
            logger.error(f"Error saving data: {e}")
            return False

    # في Data.py - إضافة دالة للتحديث القسري
    def force_refresh_user_data(self, user_id):
        """تحديث قسري لبيانات المستخدم"""
        try:
            user_id = str(user_id)
            if user_id in self.data["users"]:
                # إعادة تحميل بيانات المستخدم من الملف
                self.data["users"][user_id] = self.load_data()["users"].get(user_id, self.data["users"][user_id])
            
                # تحديث الإحصائيات
                if user_id in self.data["user_stats"]:
                    self.data["user_stats"][user_id] = self.load_data()["user_stats"].get(user_id, self.data["user_stats"][user_id])
            
                self.save_data()
                return True
            return False
        except Exception as e:
            logger.error(f"Error in force_refresh_user_data: {e}")
            return False

    def get_level_info(self, level_points):
        """الحصول على معلومات مستوى معين"""
        return self.data.get("level_system", {}).get("levels", {}).get(str(level_points), {})

    def get_next_level_info(self, user_id):
        """الحصول على معلومات المستوى التالي"""
        current_level = self.get_user_level(user_id)
        levels = sorted([int(level) for level in self.data.get("level_system", {}).get("levels", {}).keys()])
        
        for level in levels:
            if level > current_level:
                return self.get_level_info(level)
        return None

    def add_user_stat(self, user_id, stat_type, value=1):
        """إضافة إحصائية للمستخدم"""
        user_id = str(user_id)
        if "user_stats" not in self.data:
            self.data["user_stats"] = {}
        
        if user_id not in self.data["user_stats"]:
            self.data["user_stats"][user_id] = {
                "completed_tasks": 0,
                "total_earned": 0,
                "level_ups": 0,
                "earning_transactions": 0,
                "invites_count": 0,
                "tasks_created": 0
            }
        
        if stat_type not in self.data["user_stats"][user_id]:
            self.data["user_stats"][user_id][stat_type] = 0
        
        self.data["user_stats"][user_id][stat_type] += value
        return self.save_data()

    # في Data.py - تحديث دالة add_points_to_user
    def add_points_to_user(self, user_id, points):
        """إضافة نقاط للمستخدم مع التحقق من تغيير المستوى - الإصدار المصحح"""
        try:
            user_id = str(user_id)
            points = int(points)
    
            # المستوى القديم
            old_level = self.get_user_level(user_id)
        
            # إضافة النقاط
            user_data = self.get_user(user_id)
            current_points = user_data.get("points", 0)
            user_data["points"] = current_points + points
            user_data["total_earned"] = user_data.get("total_earned", 0) + points
    
            # تحديث إحصائيات الكسب
            self.add_user_stat(user_id, "total_earned", points)
            self.add_user_stat(user_id, "earning_transactions", 1)
    
            # المستوى الجديد
            new_level = self.get_user_level(user_id)
        
            # التحقق من تغيير المستوى
            level_up = False
            if new_level != old_level:
                self.add_user_stat(user_id, "level_ups", 1)
                level_up = True
                old_level_info = self.get_level_info(old_level)
                new_level_info = self.get_level_info(new_level)
                logger.info(f"🎉 المستخدم {user_id} ارتقى من مستوى {old_level_info.get('name', 'مبتدئ 🌱')} إلى {new_level_info.get('name', 'مبتدئ 🌱')}")
    
            self.save_data()
    
            # إرجاع معلومات الترقية إذا حصلت
            if level_up:
                return True, new_level
            return True, None
    
        except Exception as e:
            logger.error(f"Error in add_points_to_user: {e}")
            return False, None

    def create_backup(self):
        """إنشاء نسخة احتياطية واحدة فقط"""
        try:
            backup_file = "Data_backup.json"
        
            # نسخ البيانات الحالية إلى ملف النسخة الاحتياطية
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
            
            logger.info(f"تم إنشاء نسخة احتياطية: {backup_file}")
            return True
        
        except Exception as e:
            logger.error(f"خطأ في إنشاء النسخة الاحتياطية: {e}")
            return False

    def start_auto_save(self):
        def auto_save():
            while True:
                time.sleep(300)
                try:
                    self.save_data()
                except Exception as e:
                    logger.error(f"خطأ في الحفظ التلقائي: {e}")
        try:
            auto_save_thread = threading.Thread(target=auto_save, daemon=True)
            auto_save_thread.start()
        except Exception as e:
            logger.error(f"خطأ في بدء الحفظ التلقائي: {e}")
    
    def log_activity(self, user_id, action, details=""):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            activity_entry = {
                "timestamp": timestamp,
                "user_id": str(user_id),
                "action": action,
                "details": details
            }
            self.data["activity_log"].append(activity_entry)
            if len(self.data["activity_log"]) > 1000:
                self.data["activity_log"] = self.data["activity_log"][-1000:]
            return True
        except Exception as e:
            logger.error(f"Error logging activity: {e}")
            return False

# Data.py - الجزء 2/7 - محدث بنظام سهم الحظ
    def reserve_task(self, user_id, task_id):
        try:
            task = self.get_task(task_id)
            if not task:
                return False, "المهمة غير موجودة"
            
            if task.get('completed_count', 0) >= task.get('count', 0):
                return False, "المهمة مكتملة بالفعل"
            
            for reservation in self.task_reservations.values():
                if reservation['user_id'] == user_id and reservation['task_id'] == task_id:
                    return False, "لديك حجز نشط لهذه المهمة بالفعل"
            
            user_data = self.get_user(user_id)
            banned_tasks = user_data.get('banned_tasks', {})
            if task_id in banned_tasks:
                ban_time = datetime.strptime(banned_tasks[task_id], "%Y-%m-%d %H:%M:%S")
                if datetime.now() < ban_time:
                    return False, "محظور من هذه المهمة لمدة 24 ساعة"
                else:
                    del banned_tasks[task_id]
                    user_data['banned_tasks'] = banned_tasks
            
            reservation_id = self.generate_reservation_id()
            expiry_time = (datetime.now() + timedelta(minutes=20)).strftime("%Y-%m-%d %H:%M:%S")
            
            self.task_reservations[reservation_id] = {
                'id': reservation_id,
                'user_id': user_id,
                'task_id': task_id,
                'reserved_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'expires_at': expiry_time,
                'status': 'active'
            }
            
            task['completed_count'] = task.get('completed_count', 0) + 1
            
            self.log_activity(user_id, "task_reserved", f"تم حجز المهمة: {task_id}")
            return True, reservation_id
            
        except Exception as e:
            logger.error(f"Error reserving task: {e}")
            return False, "حدث خطأ في حجز المهمة"
    
    def cancel_reservation(self, reservation_id, user_id):
        try:
            if reservation_id in self.task_reservations:
                reservation = self.task_reservations[reservation_id]
                
                if reservation['user_id'] != user_id:
                    return False, "ليس لديك صلاحية إلغاء هذا الحجز"
                
                task = self.get_task(reservation['task_id'])
                if task:
                    task['completed_count'] = max(0, task.get('completed_count', 0) - 1)
                
                del self.task_reservations[reservation_id]
                
                self.log_activity(user_id, "reservation_cancelled", f"تم إلغاء حجز المهمة: {reservation['task_id']}")
                return True, "تم إلغاء الحجز بنجاح"
            
            return False, "الحجز غير موجود"
            
        except Exception as e:
            logger.error(f"Error cancelling reservation: {e}")
            return False, "حدث خطأ في إلغاء الحجز"
    
    def complete_reservation(self, reservation_id, proof_id):
        try:
            if reservation_id in self.task_reservations:
                reservation = self.task_reservations[reservation_id]
                reservation['status'] = 'completed'
                reservation['completed_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                reservation['proof_id'] = proof_id
                return True
            return False
        except Exception as e:
            logger.error(f"Error completing reservation: {e}")
            return False
    
    def ban_user_from_task(self, user_id, task_id, hours=24):
        try:
            user_data = self.get_user(user_id)
            banned_tasks = user_data.get('banned_tasks', {})
            ban_until = (datetime.now() + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
            banned_tasks[task_id] = ban_until
            user_data['banned_tasks'] = banned_tasks
            
            self.log_activity("system", "user_banned_from_task", 
                            f"تم حظر المستخدم {user_id} من المهمة {task_id} لمدة {hours} ساعة")
            return self.save_data()
        except Exception as e:
            logger.error(f"Error banning user from task: {e}")
            return False
    
    def set_proof_timeout(self, proof_id, hours=12):
        try:
            expiry_time = (datetime.now() + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
            self.proof_timeouts[proof_id] = expiry_time
            return True
        except Exception as e:
            logger.error(f"Error setting proof timeout: {e}")
            return False
    
    def check_reservation_expiry(self):
        try:
            current_time = datetime.now()
            expired_reservations = []
            
            for reservation_id, reservation in self.task_reservations.items():
                if reservation['status'] == 'active':
                    expires_at = datetime.strptime(reservation['expires_at'], "%Y-%m-%d %H:%M:%S")
                    if current_time > expires_at:
                        user_id = reservation['user_id']
                        task_id = reservation['task_id']
                        
                        task = self.get_task(task_id)
                        if task:
                            task['completed_count'] = max(0, task.get('completed_count', 0) - 1)
                        
                        self.ban_user_from_task(user_id, task_id, 24)
                        self.remove_points_from_user(user_id, 10)
                        
                        expired_reservations.append(reservation_id)
                        
                        self.log_activity("system", "reservation_expired", 
                                        f"انتهت مهلة حجز المستخدم {user_id} للمهمة {task_id}")
            
            for reservation_id in expired_reservations:
                del self.task_reservations[reservation_id]
                
        except Exception as e:
            logger.error(f"Error checking reservation expiry: {e}")
    
    def check_proof_timeouts(self):
        try:
            current_time = datetime.now()
            expired_proofs = []
            
            for proof_id, expiry_time in self.proof_timeouts.items():
                expiry_time = datetime.strptime(expiry_time, "%Y-%m-%d %H:%M:%S")
                if current_time > expiry_time:
                    proof = self.get_proof(proof_id)
                    if proof and proof.get('status') == 'pending':
                        self.update_proof_status(proof_id, 'accepted', 'system_auto')
                        expired_proofs.append(proof_id)
            
            for proof_id in expired_proofs:
                if proof_id in self.proof_timeouts:
                    del self.proof_timeouts[proof_id]
                    
        except Exception as e:
            logger.error(f"Error checking proof timeouts: {e}")
    
    def start_reservation_cleanup(self):
        def cleanup():
            while True:
                time.sleep(60)
                self.check_reservation_expiry()
        
        try:
            cleanup_thread = threading.Thread(target=cleanup, daemon=True)
            cleanup_thread.start()
            logger.info("🚀 بدأ نظام تنظيف الحجوزات")
        except Exception as e:
            logger.error(f"Error starting reservation cleanup: {e}")
    
    def start_proof_timeout_checker(self):
        def checker():
            while True:
                time.sleep(300)
                self.check_proof_timeouts()
        
        try:
            checker_thread = threading.Thread(target=checker, daemon=True)
            checker_thread.start()
            logger.info("🚀 بدأ نظام التحقق من مهلات الإثباتات")
        except Exception as e:
            logger.error(f"Error starting proof timeout checker: {e}")
    
    def start_pin_cleanup(self):
        """بدء نظام تنظيف التثبيتات المنتهية"""
        def cleanup():
            while True:
                time.sleep(3600)  # كل ساعة
                try:
                    self.get_pinned_tasks()  # هذه الدالة تحذف التثبيتات المنتهية تلقائياً
                except Exception as e:
                    logger.error(f"خطأ في تنظيف التثبيتات: {e}")
        
        try:
            cleanup_thread = threading.Thread(target=cleanup, daemon=True)
            cleanup_thread.start()
            logger.info("🚀 بدأ نظام تنظيف التثبيتات")
        except Exception as e:
            logger.error(f"Error starting pin cleanup: {e}")
    
    def start_arrow_cleanup(self):
        """بدء نظام تنظيف الأسهم اليومي"""
        def cleanup():
            while True:
                time.sleep(3600)  # كل ساعة
                try:
                    self.reset_daily_arrows()
                except Exception as e:
                    logger.error(f"خطأ في تنظيف الأسهم اليومي: {e}")
        
        try:
            cleanup_thread = threading.Thread(target=cleanup, daemon=True)
            cleanup_thread.start()
            logger.info("🚀 بدأ نظام تنظيف الأسهم اليومي")
        except Exception as e:
            logger.error(f"Error starting arrow cleanup: {e}")
    
    def generate_reservation_id(self):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    
    def generate_task_code(self):
        """إنشاء كود مميز للمهمة مثال TSK5A3B"""
        letters = ''.join(random.choices(string.ascii_uppercase, k=2))
        numbers = ''.join(random.choices(string.digits, k=2))
        return f"TSK{numbers}{letters}"
    
    def get_user_reservations(self, user_id):
        user_id = str(user_id)
        return [r for r in self.task_reservations.values() if r['user_id'] == user_id and r['status'] == 'active']

    def get_user(self, user_id):
        user_id = str(user_id)
        if user_id not in self.data["users"]:
            self.data["users"][user_id] = {
                "points": 0,
                "invited_by": None,
                "invited_users": [],
                "daily_invites": {},
                "completed_tasks": [],
                "joined_date": "",  # ✅ تغيير من None إلى string فارغ
                "last_active": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_earned": 0,
                "total_spent": 0,
                "banned_tasks": {}
            }
        return self.data["users"][user_id]
    
    def update_user_activity(self, user_id):
        try:
            user_data = self.get_user(user_id)
            user_data["last_active"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return True
        except Exception as e:
            logger.error(f"Error updating user activity: {e}")
            return False
    
    def get_admins(self):
        return self.data["admins"]
    
    def get_blocked_users(self):
        return self.data["blocked_users"]
    
    def get_tasks(self):
        return self.data["tasks"]
    
    def get_invite_points(self):
        return self.data.get("invite_points", 5)
    
    def set_invite_points(self, points):
        try:
            points = int(points)
            self.data["invite_points"] = points
            return self.save_data()
        except:
            return False
    
    def add_admin(self, user_id):
        user_id = str(user_id)
        if user_id not in self.data["admins"]:
            self.data["admins"].append(user_id)
            return self.save_data()
        return False
    
    def remove_admin(self, user_id):
        user_id = str(user_id)
        if user_id in self.data["admins"]:
            self.data["admins"].remove(user_id)
            return self.save_data()
        return False

    def add_points_to_user(self, user_id, points):
        try:
            user_id = str(user_id)
            points = int(points)
            user_data = self.get_user(user_id)
            user_data["points"] += points
            user_data["total_earned"] = user_data.get("total_earned", 0) + points
            return self.save_data()
        except:
            return False

    def remove_points_from_user(self, user_id, points):
        try:
            user_id = str(user_id)
            points = int(points)
            user_data = self.get_user(user_id)
            user_data["points"] = max(0, user_data["points"] - points)
            user_data["total_spent"] = user_data.get("total_spent", 0) + points
            return self.save_data()
        except:
            return False

    def block_user(self, user_id):
        user_id = str(user_id)
        blocked_users = self.get_blocked_users()
        if user_id not in blocked_users:
            blocked_users.append(user_id)
            return self.save_data()
        return False

    def unblock_user(self, user_id):
        user_id = str(user_id)
        blocked_users = self.get_blocked_users()
        if user_id in blocked_users:
            blocked_users.remove(user_id)
            return self.save_data()
        return False

    def get_user_points(self, user_id):
        user_id = str(user_id)
        user_data = self.get_user(user_id)
        return user_data["points"]

    def get_tasks_by_type(self, task_type):
        try:
            if not self.data.get("tasks_new"):
                return []
            
            # الحصول على المهام النشطة
            if task_type == "all":
                tasks = [task for task in self.data["tasks_new"] if task.get("status") == "active"]
            else:
                tasks = [task for task in self.data["tasks_new"] if task.get("type") == task_type and task.get("status") == "active"]
            
            # ✅ الترتيب من الأحدث إلى الأقدم حسب التاريخ
            tasks.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            # ✅ الحصول على المهام المثبتة النشطة
            pinned_tasks = self.get_pinned_tasks()
            
            # فصل المهام المثبتة عن العادية مع الحفاظ على الترتيب الزمني
            pinned_list = []
            normal_list = []
            
            for task in tasks:
                if task['id'] in pinned_tasks:
                    pinned_list.append(task)
                else:
                    normal_list.append(task)
            
            # ✅ عرض المهام المثبتة أولاً ثم المهام الجديدة
            return pinned_list + normal_list
            
        except Exception as e:
            logger.error(f"Error in get_tasks_by_type: {e}")
            return []
    
    def get_task(self, task_id):
        for task in self.data["tasks_new"]:
            if str(task.get("id")) == str(task_id):
                task["total_views"] = task.get("total_views", 0) + 1
                return task
        return None
    
    def get_proof(self, proof_id):
        for proof in self.data["proofs"]:
            if str(proof.get("id")) == str(proof_id):
                return proof
        return None
    
    def get_user_tasks(self, owner_id):
        owner_id = str(owner_id)
        return [task for task in self.data["tasks_new"] if task.get("owner_id") == owner_id]
    
    def get_user_proofs(self, user_id):
        user_id = str(user_id)
        return [proof for proof in self.data["proofs"] if proof.get("executor_id") == user_id]

# Data.py - الجزء 3/7 - محدث بنظام سهم الحظ
# Data.py - الجزء 2/3

    def add_task(self, owner_id, task_type, name, description, photo, count, price, link, proof):
        try:
            # ✅ التحقق من الرابط قبل إضافة المهمة
            from LinkValidator import validate_task_link
            is_valid, message = validate_task_link(link, task_type)
            if not is_valid:
                logger.error(f"❌ رابط غير صالح: {message}")
                return False, None
            
            task_id = self.generate_task_id()
            task_code = self.generate_task_code()
            
            task_data = {
                "id": task_id,
                "code": task_code,
                "owner_id": str(owner_id),
                "type": task_type,
                "name": name,
                "description": description,
                "photo": photo,
                "count": int(count),
                "completed_count": 0,
                "price": int(price),
                "link": link,
                "proof": proof,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "active",
                "total_views": 0,
                "total_applications": 0,
                "channel_message_id": None
            }
            
            if "tasks_new" not in self.data:
                self.data["tasks_new"] = []
                
            self.data["tasks_new"].append(task_data)
            success = self.save_data()
            
            return success, task_id
            
        except Exception as e:
            logger.error(f"Error adding task: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False, None

    def add_proof(self, task_id, executor_id, text, photo):
        try:
            proof_id = self.generate_proof_id()
            proof_data = {
                "id": proof_id,
                "task_id": str(task_id),
                "executor_id": str(executor_id),
                "text": text,
                "photo": photo,
                "status": "pending",
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "reviewed_at": None,
                "reviewed_by": None
            }
            self.data["proofs"].append(proof_data)
            task = self.get_task(task_id)
            if task:
                task["total_applications"] = task.get("total_applications", 0) + 1
            return self.save_data(), proof_id
        except Exception as e:
            logger.error(f"Error adding proof: {e}")
            return False, None

    def update_proof_status(self, proof_id, status, reviewed_by=None, context=None):
        """
        تحديث حالة الإثبات مع نقل المهمة عند اكتمالها - الإصلاح النهائي
        """
        try:
            for proof in self.data["proofs"]:
                if str(proof.get("id")) == str(proof_id):
                    proof["status"] = status
                    proof["reviewed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    proof["reviewed_by"] = reviewed_by
                    
                    if status == "accepted":
                        task = self.get_task(proof["task_id"])
                        if task:
                            task["completed_count"] = task.get('completed_count', 0) + 1
                            
                            # ✅ حفظ المستوى القديم قبل الإضافة
                            old_level = self.get_user_level(proof["executor_id"])
                            
                            points_added = self.add_points_to_user(proof["executor_id"], task["price"])
                            
                            # ✅ التحقق من الترقية وإرسال الإشعار
                            if points_added and context:
                                new_level = self.get_user_level(proof["executor_id"])
                                if new_level != old_level:
                                    level_info = self.get_level_info(new_level)
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
                                    
                                    # ✅ استخدام دالة مساعدة غير متزامنة لإرسال الرسالة
                                    self._send_level_up_notification(context, proof["executor_id"], level_info, benefits_message)
                            
                            # ✅ التحقق إذا اكتملت المهمة ونقلها فوراً
                            if task["completed_count"] >= task["count"]:
                                task["status"] = "completed"
                                self.log_activity("system", "task_completed", 
                                                f"اكتملت المهمة {task['id']} - {task['name']}")
                                
                                # ✅ نقل المهمة إلى القناة المنتهية فوراً
                                if context is not None:
                                    self._move_completed_task_to_channel(task['id'], context)
                        
                    return self.save_data()
            
            return False
            
        except Exception as e:
            logger.error(f"خطأ في update_proof_status: {e}")
            return False

    def _send_level_up_notification(self, context, user_id, level_info, benefits_message):
        """دالة مساعدة لإرسال إشعار الترقية (يتم استدعاؤها من دوال أخرى)"""
        try:
            # إنشاء مهمة غير متزامنة لإرسال الرسالة
            async def send_message():
                try:
                    await context.bot.send_message(
                        chat_id=int(user_id),
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
                    logger.error(f"خطأ في إرسال إشعار الترقية: {e}")
            
            # تشغيل المهمة في الخلفية
            import asyncio
            asyncio.create_task(send_message())
            
        except Exception as e:
            logger.error(f"خطأ في _send_level_up_notification: {e}")

    def _move_completed_task_to_channel(self, task_id, context):
        """
        نقل المهمة المكتملة إلى القناة المنتهية
        """
        try:
            logger.info(f"🚀 بدء نقل المهمة {task_id} إلى القناة المنتهية")
            
            from Admin.TasksChannels import move_task_to_completed
            
            async def move_task():
                try:
                    logger.info(f"📤 جاري نقل المهمة {task_id}...")
                    success = await move_task_to_completed(task_id, context)
                    if success:
                        logger.info(f"✅ تم نقل المهمة {task_id} إلى القناة المنتهية")
                        self.log_activity("system", "task_moved", 
                                        f"تم نقل المهمة {task_id} إلى القناة المنتهية")
                    else:
                        logger.error(f"❌ فشل نقل الم任務 {task_id} إلى القناة المنتهية")
                except Exception as e:
                    logger.error(f"❌ خطأ في نقل المهمة: {e}")
            
            # تشغيل المهمة في الخلفية
            asyncio.create_task(move_task())
            
        except ImportError:
            logger.error("❌ لا يمكن استيراد TasksChannels")
        except Exception as e:
            logger.error(f"❌ خطأ في _move_completed_task_to_channel: {e}")

    def _schedule_task_move(self, task_id):
        """
        جدولة نقل المهمة للمعالجة لاحقاً
        """
        try:
            if 'pending_task_moves' not in self.data:
                self.data['pending_task_moves'] = []
            
            self.data['pending_task_moves'].append({
                'task_id': task_id,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            self.save_data()
            logger.info(f"⏰ تم جدولة نقل المهمة {task_id} للمعالجة لاحقاً")
            
        except Exception as e:
            logger.error(f"❌ خطأ في _schedule_task_move: {e}")

    def process_pending_task_moves(self, context):
        """
        معالجة المهام المعلقة للنقل
        """
        try:
            if 'pending_task_moves' not in self.data or not self.data['pending_task_moves']:
                return
            
            pending_tasks = self.data['pending_task_moves'].copy()
            self.data['pending_task_moves'] = []
            self.save_data()
            
            for task_move in pending_tasks:
                task_id = task_move['task_id']
                task = self.get_task(task_id)
                
                if task and task.get('status') == 'completed':
                    self._move_completed_task_to_channel(task_id, context)
                    
        except Exception as e:
            logger.error(f"❌ خطأ في process_pending_task_moves: {e}")

    def get_pending_proofs(self):
        return [proof for proof in self.data["proofs"] if proof.get("status") == "pending"]
    
    def generate_task_id(self):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    def generate_proof_id(self):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    def get_available_prize(self):
        """الحصول على جائزة عشوائية مع مراعاة الكمية المتاحة - إصدار فارغ"""
        try:
            settings = self.get_luck_arrow_settings()
            prizes = settings.get("prizes", [])
        
            # إذا لم توجد جوائز مضافة، إرجاع لا شيء
            if not prizes:
                return {"type": "nothing", "value": 0, "probability": 100}
        
            # تصفية الجوائز المتاحة فقط
            available_prizes = [p for p in prizes if p.get("remaining", 0) > 0]
        
            if not available_prizes:
                # إذا لم توجد جوائز متاحة، إرجاع لا شيء
                return {"type": "nothing", "value": 0, "probability": 100}
        
            # حساب الاحتمالات الإجمالية
            total_prob = sum(prize.get("probability", 0) for prize in available_prizes)
        
            # إذا كانت الاحتمالات صفر، توزيع متساوي
            if total_prob == 0:
                for prize in available_prizes:
                    prize["probability"] = 100 // len(available_prizes)
                total_prob = sum(prize.get("probability", 0) for prize in available_prizes)
        
            rand = random.randint(1, total_prob)
        
            current_prob = 0
            for prize in available_prizes:
                current_prob += prize.get("probability", 0)
                if rand <= current_prob:
                    # تقليل الكمية المتاحة
                    prize["remaining"] = prize.get("remaining", 0) - 1
                    self.save_data()
                
                    return {
                        "type": prize["type"],
                        "value": prize["value"],
                        "original_prize": prize
                    }
        
            return {"type": "nothing", "value": 0, "probability": 100}
        
        except Exception as e:
            logger.error(f"Error getting available prize: {e}")
            return {"type": "nothing", "value": 0, "probability": 100}

    # ✅ نظام أكواد الهدايا
    def generate_gift_code(self):
        """إنشاء كود هدية عشوائي"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    def add_gift_code(self, code_data):
        """إضافة كود هدية جديد"""
        try:
            code = code_data['code']
            self.data["gift_codes"][code] = code_data
            return self.save_data()
        except Exception as e:
            logger.error(f"Error adding gift code: {e}")
            return False

    def get_gift_code(self, code):
        """الحصول على بيانات كود الهدية"""
        return self.data["gift_codes"].get(code)

    def use_gift_code(self, code, user_id):
        """استخدام كود الهدية"""
        try:
            gift_code = self.get_gift_code(code)
            if not gift_code:
                return False, "الكود غير صحيح"
            
            if gift_code['used_count'] >= gift_code['max_uses']:
                return False, "تم استخدام هذا الكود بالكامل"
            
            if str(user_id) in gift_code['used_by']:
                return False, "لقد استخدمت هذا الكود مسبقاً"
            
            # تحديث البيانات
            gift_code['used_count'] += 1
            gift_code['used_by'].append(str(user_id))
            
            # منح النقاط للمستخدم
            self.add_points_to_user(user_id, gift_code['points'])
            
            self.save_data()
            self.log_activity(user_id, "gift_code_used", f"تم استخدام كود الهدية: {code}")
            return True, f"تم استلام {gift_code['points']} نقطة بنجاح!"
            
        except Exception as e:
            logger.error(f"Error using gift code: {e}")
            return False, "حدث خطأ في استخدام الكود"

    def get_all_gift_codes(self):
        """الحصول على جميع أكواد الهدايا"""
        return self.data["gift_codes"]

    # ✅ نظام الدعوة المحسن
    def is_invite_system_enabled(self):
        """التحقق من إذا كان نظام الدعوة مفعلاً"""
        return self.data.get("invite_system_enabled", True)

    def toggle_invite_system(self, enabled):
        """تفعيل أو إلغاء تفعيل نظام الدعوة"""
        try:
            self.data["invite_system_enabled"] = enabled
            return self.save_data()
        except Exception as e:
            logger.error(f"Error toggling invite system: {e}")
            return False

    def get_invite_link(self, user_id, bot_username):
        """إنشاء رابط دعوة صحيح"""
        if not self.is_invite_system_enabled():
            return None, "نظام الدعوة معطل حالياً"
        
        user_id = str(user_id)
        return f"https://t.me/{bot_username}?start={user_id}", None

# في Data.py - البحث عن دالة add_invite_usage وتعديلها
    def add_invite_usage(self, referrer_id, invited_id):
        """تسجيل استخدام رابط الدعوة مع منح النقاط والأسهم"""
        try:
            logger.info(f"🔍 معالجة دعوة: {referrer_id} دعا {invited_id}")
        
            referrer_id = str(referrer_id)
            invited_id = str(invited_id)
        
            # منع الاحتيال: لا يمكن دعوة النفس
            if referrer_id == invited_id:
                logger.warning(f"❌ محاولة دعوة النفس: {referrer_id}")
                return False, "لا يمكن دعوة نفسك"
        
            # التحقق إذا كان المدعو موجوداً بالفعل
            invited_user_data = self.get_user(invited_id)
        
            # التحقق إذا كان المستخدم جديداً حقاً
            joined_date = invited_user_data.get('joined_date')
            if joined_date and joined_date != "":
                logger.warning(f"❌ المستخدم مسجل مسبقاً: {invited_id} - تاريخ الانضمام: {joined_date}")
                return False, "المستخدم مسجل مسبقاً"
        
            # التحقق إذا تم الدعوة مسبقاً
            user_data = self.get_user(referrer_id)
            invited_users = user_data.get('invited_users', [])
        
            if invited_id in invited_users:
                logger.warning(f"❌ تم دعوة هذا المستخدم مسبقاً: {invited_id}")
                return False, "تم دعوة هذا المستخدم مسبقاً"
        
            # ✅ إزالة الحد اليومي للدعوات (يمكن دعوة عدد لا محدود)
            today = datetime.now().strftime("%Y-%m-%d")
            daily_invites = user_data.get('daily_invites', {})
            today_invites = daily_invites.get(today, 0)
        
            # ✅ تسجيل تاريخ الانضمام للمستخدم الجديد
            current_date = datetime.now().strftime("%Y-%m-%d")
            invited_user_data['joined_date'] = current_date
        
            # ✅ إلغاء منح 100 نقطة للمستخدم الجديد وجعل رصيده 0
            invited_user_data['points'] = 0
            logger.info(f"✅ تم تعيين رصيد المستخدم الجديد {invited_id} إلى 0 نقطة")
        
            # تسجيل الدعوة للمدعي
            if 'invited_users' not in user_data:
                user_data['invited_users'] = []
            user_data['invited_users'].append(invited_id)
        
            # تحديث الدعوات اليومية (بدون حد أقصى)
            if 'daily_invites' not in user_data:
                user_data['daily_invites'] = {}
            user_data['daily_invites'][today] = today_invites + 1
        
            logger.info(f"📊 عدد دعوات اليوم: {today_invites + 1} (لا يوجد حد أقصى)")
        
            # ✅ منح النقاط والأسهم للمدعي فقط
            invite_points = self.get_invite_points()
            luck_settings = self.get_luck_arrow_settings()
            invite_bonus_points = luck_settings.get("invite_points", 1)
            invite_arrows = luck_settings.get("invite_arrows", 1)
            
            logger.info(f"💰 محاولة منح {invite_points + invite_bonus_points} نقطة و{invite_arrows} سهم للمدعي {referrer_id}")
        
            # الحصول على نقاط المدعي الحالية قبل الإضافة
            current_points = user_data.get('points', 0)
            
            # ✅ حفظ المستوى القديم قبل الإضافة
            old_level = self.get_user_level(referrer_id)
            
            # منح النقاط
            success = self.add_points_to_user(referrer_id, invite_points + invite_bonus_points)
            
            # منح الأسهم (سهم الحظ)
            if success:
                # ✅ إضافة سهم حظ للمدعي
                arrow_success = self.add_arrows_to_user(referrer_id, invite_arrows)
                if not arrow_success:
                    logger.error(f"❌ فشل في منح الأسهم للمدعي {referrer_id}")
            
            if success:
                new_points = self.get_user_points(referrer_id)
                logger.info(f"✅ تم منح النقاط والأسهم بنجاح: {referrer_id} ({current_points} → {new_points}) + {invite_arrows} سهم")
                
                # ✅ التحقق من الترقية
                new_level = self.get_user_level(referrer_id)
                if new_level != old_level:
                    self.add_user_stat(referrer_id, "level_ups", 1)
                    logger.info(f"🎉 المستخدم {referrer_id} ارتقى إلى مستوى جديد بسبب الدعوة")
                
                self.save_data()
                return True, f"تم منح {invite_points + invite_bonus_points} نقطة و{invite_arrows} سهم لدعوة مستخدم جديد"
            else:
                logger.error(f"❌ فشل في منح النقاط للمدعي {referrer_id}")
                return False, "حدث خطأ في منح النقاط"
        
        except Exception as e:
            logger.error(f"❌ خطأ في add_invite_usage: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return False, "حدث خطأ في معالجة الدعوة"

    def pin_task(self, user_id, task_id, hours=None):
        """تثبيت مهمة لمدة محددة"""
        try:
            user_data = self.get_user(user_id)
            task = self.get_task(task_id)
        
            if not task:
                return False, "المهمة غير موجودة"
            
            if str(task.get('owner_id')) != str(user_id):
                return False, "ليس لديك صلاحية تثبيت هذه المهمة"
        
            # الحصول على إعدادات التثبيت
            pin_settings = self.data.get("pin_settings", {})
            pin_price = pin_settings.get("pin_price", 10)
            pin_duration = hours or pin_settings.get("pin_duration", 24)
            max_pins = pin_settings.get("max_pins", 5)
        
            # التحقق من الحد الأقصى للمهام المثبتة
            user_pinned_tasks = [p for p in self.get_pinned_tasks().values() if str(p['user_id']) == str(user_id)]
            if len(user_pinned_tasks) >= max_pins:
                return False, f"وصلت للحد الأقصى للمهام المثبتة ({max_pins})"
        
            # التحقق من رصيد النقاط
            if user_data["points"] < pin_price:
                return False, f"نقاطك غير كافية. تحتاج {pin_price} نقاط"
        
            # خصم النقاط
            self.remove_points_from_user(user_id, pin_price)
        
            # حساب وقت انتهاء التثبيت
            from datetime import datetime, timedelta
            pin_expiry = (datetime.now() + timedelta(hours=pin_duration)).strftime("%Y-%m-%d %H:%M:%S")
        
            # إضافة التثبيت
            if "pinned_tasks" not in self.data:
                self.data["pinned_tasks"] = {}
            
            # استخدام task_id ك string للتأكد من المقارنة الصحيحة
            task_id_str = str(task_id)
            self.data["pinned_tasks"][task_id_str] = {
                "user_id": str(user_id),
                "task_id": task_id_str,
                "pinned_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "expires_at": pin_expiry,
                "hours": pin_duration
            }
        
            self.save_data()
            self.log_activity(user_id, "task_pinned", f"تم تثبيت المهمة {task_id} لمدة {pin_duration} ساعة")
            return True, f"تم تثبيت المهمة بنجاح لمدة {pin_duration} ساعة"
        
        except Exception as e:
            logger.error(f"Error pinning task: {e}")
            return False, "حدث خطأ في تثبيت المهمة"

    def unpin_task(self, task_id):
        """إلغاء تثبيت مهمة"""
        try:
            if "pinned_tasks" in self.data and task_id in self.data["pinned_tasks"]:
                del self.data["pinned_tasks"][task_id]
                self.save_data()
                return True
            return False
        except Exception as e:
            logger.error(f"Error unpinning task: {e}")
            return False

    def get_pinned_tasks(self):
        """الحصول على المهام المثبتة النشطة"""
        try:
            from datetime import datetime
            active_pins = {}
        
            if "pinned_tasks" not in self.data:
                self.data["pinned_tasks"] = {}
            
            for task_id, pin_data in self.data["pinned_tasks"].items():
                try:
                    expires_at = datetime.strptime(pin_data["expires_at"], "%Y-%m-%d %H:%M:%S")
                    if datetime.now() < expires_at:
                        active_pins[str(task_id)] = pin_data
                    else:
                        # حذف التثبيت المنتهي
                        self.unpin_task(task_id)
                except Exception as e:
                    logger.error(f"Error processing pin for task {task_id}: {e}")
                    continue
                
            return active_pins
        except Exception as e:
            logger.error(f"Error getting pinned tasks: {e}")
            return {}

    def is_task_pinned(self, task_id):
        """التحقق إذا كانت المهمة مثبتة"""
        try:
            pinned_tasks = self.get_pinned_tasks()
            # التحقق إذا كانت task_id موجودة في المفاتيح (يجب أن تكون string)
            return str(task_id) in pinned_tasks
        except Exception as e:
            logger.error(f"Error in is_task_pinned: {e}")
            return False

    def update_pin_settings(self, settings):
        """تحديث إعدادات التثبيت"""
        try:
            self.data["pin_settings"] = settings
            return self.save_data()
        except Exception as e:
            logger.error(f"Error updating pin settings: {e}")
            return False

    # في Data.py - تحديث دالة get_user_discount
    def get_user_discount(self, user_id):
        """الحصول على نسبة الخصم حسب مستوى المستخدم - الإصدار المصحح"""
        user_level = self.get_user_level(user_id)
        level_info = self.get_level_info(user_level)
        level_name = level_info.get('name', 'مبتدئ 🌱')
    
        # خريطة الخصومات حسب المستوى
        discount_map = {
            "مبتدئ 🌱": 0,
            "نشط ⭐": 5,
            "محترف 🏆": 10,
            "خبير 👑": 15,
            "أسطورة 🚀": 20
        }
     
        return discount_map.get(level_name, 0)

    def get_user_level_name(self, user_id):
        """الحصول على اسم مستوى المستخدم الحالي"""
        try:
            user_id = str(user_id)
            user_data = self.get_user(user_id)
            points = user_data.get("points", 0)

            levels = sorted([
                int(level) for level in self.data.get("level_system", {}).get("levels", {}).keys()
            ], reverse=True)

            for level_points in levels:
                if points >= level_points:
                    level_info = self.get_level_info(level_points)
                    return level_info.get('name', 'مبتدئ 🌱')

            return "مبتدئ 🌱"
        
        except Exception as e:
            logger.error(f"❌ خطأ في get_user_level_name: {e}")
            return "مبتدئ 🌱"

    def can_user_pin_free(self, user_id):
        """التحقق إذا كان المستخدم يمكنه التثبيت مجاناً - الإصدار المصحح"""
        try:
            level_name = self.get_user_level_name(user_id)
            return level_name == "أسطورة 🚀"
        
        except Exception as e:
            logger.error(f"❌ خطأ في can_user_pin_free: {e}")
            return False

    def get_user_level(self, user_id):
        """الحصول على مستوى المستخدم الحالي (عدد النقاط المطلوبة)"""
        try:
            user_id = str(user_id)
            user_data = self.get_user(user_id)
            points = user_data.get("points", 0)

            levels = sorted([
                int(level) for level in self.data.get("level_system", {}).get("levels", {}).keys()
            ], reverse=True)

            for level_points in levels:
                if points >= level_points:
                    return level_points

            return 0
        
        except Exception as e:
            logger.error(f"❌ خطأ في get_user_level: {e}")
            return 0

    # تحديث دالة has_priority_support
    def has_priority_support(self, user_id):
        """التحقق إذا كان المستخدم لديه أولوية في الدعم - الإصدار المصحح"""
        user_level = self.get_user_level(user_id)
        level_info = self.get_level_info(user_level)
        benefits = level_info.get('benefits', [])
    
        # التحقق من وجود ميزة الأولوية في الدعم
        return "أولوية في الدعم" in benefits

    # ✅ نظام سهم الحظ - الدوال الجديدة
    def get_luck_arrow_settings(self):
        """الحصول على إعدادات سهم الحظ"""
        return self.data.get("luck_arrow_settings", {})
    
    def update_luck_arrow_settings(self, settings):
        """تحديث إعدادات سهم الحظ"""
        try:
            self.data["luck_arrow_settings"] = settings
            return self.save_data()
        except Exception as e:
            logger.error(f"Error updating luck arrow settings: {e}")
            return False
    
    def get_user_arrows(self, user_id):
        """الحصول على أسهم المستخدم"""
        user_id = str(user_id)
        if "luck_arrows" not in self.data:
            self.data["luck_arrows"] = {}
        
        if user_id not in self.data["luck_arrows"]:
            self.data["luck_arrows"][user_id] = {
                "total_arrows": 0,
                "used_today": 0,
                "last_used": None,
                "history": []
            }
        
        return self.data["luck_arrows"][user_id]
    
    def add_arrows_to_user(self, user_id, arrows_count):
        """إضافة أسهم للمستخدم"""
        try:
            user_id = str(user_id)
            user_data = self.get_user_arrows(user_id)
            user_data["total_arrows"] += arrows_count
            return self.save_data()
        except Exception as e:
            logger.error(f"Error adding arrows to user: {e}")
            return False
    
    def use_arrow(self, user_id):
        """استخدام سهم"""
        try:
            user_id = str(user_id)
            user_data = self.get_user_arrows(user_id)
            
            if user_data["total_arrows"] <= 0:
                return False
            
            user_data["total_arrows"] -= 1
            user_data["used_today"] += 1
            user_data["last_used"] = datetime.now().strftime("%Y-%m-%d")
            
            # تحديث استخدام الصندوق
            settings = self.get_luck_arrow_settings()
            settings["used_arrows"] = settings.get("used_arrows", 0) + 1
            
            # التحقق إذا انتهى الصندوق
            if settings["used_arrows"] >= settings.get("total_arrows", 10000):
                settings["box_open"] = False
            
            return self.save_data()
            
        except Exception as e:
            logger.error(f"Error using arrow: {e}")
            return False

# Data.py - الجزء 5/7 - محدث بنظام سهم الحظ
    def reset_daily_arrows(self):
        """إعادة تعيين العد اليومي للأسهم"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            for user_id, user_data in self.data.get("luck_arrows", {}).items():
                if user_data.get("last_used") != today:
                    user_data["used_today"] = 0
                    user_data["last_used"] = today
            
            return self.save_data()
        except Exception as e:
            logger.error(f"Error resetting daily arrows: {e}")
            return False
    
    def can_user_spin(self, user_id):
        """التحقق إذا كان يمكن للمستخدم الرمي"""
        try:
            user_id = str(user_id)
            user_data = self.get_user_arrows(user_id)
            settings = self.get_luck_arrow_settings()
            
            # التحقق من حالة الصندوق
            if not settings.get("box_open", True):
                return False
            
            # التحقق من الأسهم
            if user_data["total_arrows"] <= 0:
                return False
            
            # التحقق من الحد اليومي
            daily_limit = settings.get("daily_spin_limit", 10)
            
            # إعادة تعيين العد اليومي إذا كان تاريخ جديد
            today = datetime.now().strftime("%Y-%m-%d")
            if user_data.get("last_used") != today:
                user_data["used_today"] = 0
                user_data["last_used"] = today
                self.save_data()
            
            return user_data["used_today"] < daily_limit
            
        except Exception as e:
            logger.error(f"Error checking spin ability: {e}")
            return False
    
    def get_arrow_prize(self):
        """الحصول على جائزة عشوائية"""
        try:
            settings = self.get_luck_arrow_settings()
            prizes = settings.get("prizes", [])
            
            if not prizes:
                # جوائز افتراضية
                prizes = [
                    {"type": "points", "value": 10, "probability": 30},
                    {"type": "points", "value": 25, "probability": 20},
                    {"type": "points", "value": 50, "probability": 10},
                    {"type": "gift_code", "value": 100, "probability": 5},
                    {"type": "arrow", "value": 1, "probability": 15},
                    {"type": "nothing", "value": 0, "probability": 20}
                ]
            
            total_prob = sum(prize["probability"] for prize in prizes)
            rand = random.randint(1, total_prob)
            
            current_prob = 0
            for prize in prizes:
                current_prob += prize["probability"]
                if rand <= current_prob:
                    return prize
            
            return prizes[0]  # جائزة افتراضية إذا حدث خطأ
            
        except Exception as e:
            logger.error(f"Error getting prize: {e}")
            return {"type": "points", "value": 10, "probability": 100}
    
    def add_arrow_history(self, user_id, prize):
        """إضافة الرمية إلى السجل"""
        try:
            user_id = str(user_id)
            user_data = self.get_user_arrows(user_id)
            
            history_entry = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "prize": prize,
                "won": prize["value"] > 0 if prize["type"] != "nothing" else False
            }
            
            user_data["history"].append(history_entry)
            if len(user_data["history"]) > 10:
                user_data["history"] = user_data["history"][-10:]
            
            return self.save_data()
            
        except Exception as e:
            logger.error(f"Error adding arrow history: {e}")
            return False
    
    def get_arrow_history(self, user_id):
        """الحصول على سجل رميات المستخدم"""
        try:
            user_id = str(user_id)
            user_data = self.get_user_arrows(user_id)
            return user_data.get("history", [])
        except Exception as e:
            logger.error(f"Error getting arrow history: {e}")
            return []
    
    def get_box_status(self):
        """الحصول على حالة الصندوق"""
        try:
            settings = self.get_luck_arrow_settings()
            total_arrows = settings.get("total_arrows", 10000)
            used_arrows = settings.get("used_arrows", 0)
            
            return {
                "total": total_arrows,
                "used": used_arrows,
                "remaining": total_arrows - used_arrows,
                "is_open": settings.get("box_open", True)
            }
        except Exception as e:
            logger.error(f"Error getting box status: {e}")
            return {"total": 10000, "used": 0, "remaining": 10000, "is_open": True}
    
    def reset_arrow_box(self):
        """إعادة تعيين صندوق الأسهم"""
        try:
            settings = self.get_luck_arrow_settings()
            settings["used_arrows"] = 0
            settings["box_open"] = True
            return self.save_data()
        except Exception as e:
            logger.error(f"Error resetting arrow box: {e}")
            return False
    
    def set_box_capacity(self, capacity):
        """تعيين سعة الصندوق"""
        try:
            settings = self.get_luck_arrow_settings()
            settings["total_arrows"] = capacity
            
            # إذا كانت السعة الجديدة أقل من المستخدم، ضبط المستخدم
            if settings["used_arrows"] > capacity:
                settings["used_arrows"] = capacity
            
            # إذا انتهى الصندوق، إغلاقه
            if settings["used_arrows"] >= capacity:
                settings["box_open"] = False
            
            return self.save_data()
        except Exception as e:
            logger.error(f"Error setting box capacity: {e}")
            return False
    
    def toggle_box_status(self):
        """تبديل حالة الصندوق"""
        try:
            settings = self.get_luck_arrow_settings()
            settings["box_open"] = not settings.get("box_open", True)
            return self.save_data()
        except Exception as e:
            logger.error(f"Error toggling box status: {e}")
            return False
    
    def get_arrow_stats(self):
        """الحصول على إحصائيات الأسهم"""
        try:
            total_users = len(self.data.get("luck_arrows", {}))
            active_users = sum(1 for user_data in self.data.get("luck_arrows", {}).values() 
                             if user_data.get("total_arrows", 0) > 0)
            
            total_arrows = sum(user_data.get("total_arrows", 0) 
                             for user_data in self.data.get("luck_arrows", {}).values())
            
            total_spins = sum(user_data.get("used_today", 0) 
                            for user_data in self.data.get("luck_arrows", {}).values())
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "total_arrows": total_arrows,
                "total_spins": total_spins
            }
        except Exception as e:
            logger.error(f"Error getting arrow stats: {e}")
            return {"total_users": 0, "active_users": 0, "total_arrows": 0, "total_spins": 0}
    
    def give_arrows_to_user(self, user_id, arrows_count):
        """منح أسهم لمستخدم"""
        try:
            user_id = str(user_id)
            return self.add_arrows_to_user(user_id, arrows_count)
        except Exception as e:
            logger.error(f"Error giving arrows to user: {e}")
            return False
    
    def give_arrows_to_all(self, arrows_count):
        """منح أسهم لجميع المستخدمين"""
        try:
            success_count = 0
            for user_id in self.data.get("users", {}).keys():
                if self.add_arrows_to_user(user_id, arrows_count):
                    success_count += 1
            return success_count
        except Exception as e:
            logger.error(f"Error giving arrows to all: {e}")
            return 0

    def get_prize_text(self, prize):
        try:
            prize_type = prize.get("type", "")
            value = prize.get("value", 0)
        
            if prize_type == "points":
                return f"{value} نقطة"
            elif prize_type == "gift_code":
                return f"كود هدية {value} نقطة"
            elif prize_type == "arrow":
                return f"{value} سهم"
            elif prize_type == "nothing":
                return "لا شيء"
        
            return "جائزة"
        except Exception as e:
            logger.error(f"Error getting prize text: {e}")
            return "جائزة"

    def add_prize_with_quantity(self, prize_type, value, quantity, probability=None):
        """إضافة جائزة بكمية محددة"""
        try:
            settings = self.get_luck_arrow_settings()
        
            if "prizes" not in settings:
                settings["prizes"] = []
        
            # إذا كانت الجائزة موجودة مسبقاً، تحديث الكمية
            for prize in settings["prizes"]:
                if prize["type"] == prize_type and prize["value"] == value:
                    prize["quantity"] = prize.get("quantity", 0) + quantity
                    prize["remaining"] = prize.get("remaining", quantity) + quantity
                    return self.save_data()
        
            # إذا لم تكن موجودة، إضافة جائزة جديدة
            new_prize = {
                "type": prize_type,
                "value": value,
                "quantity": quantity,
                "remaining": quantity,
                "probability": probability or self.calculate_auto_probability(prize_type, value)
            }
        
            settings["prizes"].append(new_prize)
            return self.save_data()
        
        except Exception as e:
            logger.error(f"Error adding prize with quantity: {e}")
            return False

    def calculate_auto_probability(self, prize_type, value):
        """حساب الاحتمال التلقائي بناءً على نوع وقيمة الجائزة"""
        try:
            # قيم افتراضية بناءً على نوع وقيمة الجائزة
            if prize_type == "nothing":
                return 20  # 20% لعدم الفوز بأي شيء
        
            base_prob = {
                "points": {10: 30, 25: 20, 50: 10, 100: 5},
                "arrow": {1: 15, 3: 10, 5: 5, 10: 2},
                "gift_code": {50: 8, 100: 5, 200: 3, 500: 1}
            }
        
            # البحث عن أقرب قيمة
            if prize_type in base_prob:
                closest_value = min(base_prob[prize_type].keys(), key=lambda x: abs(x - value))
                return base_prob[prize_type][closest_value]
        
            return 10  # قيمة افتراضية
        
        except Exception as e:
            logger.error(f"Error calculating probability: {e}")
            return 10

    def get_available_prize(self):
        """الحصول على جائزة عشوائية مع مراعاة الكمية المتاحة"""
        try:
            settings = self.get_luck_arrow_settings()
            prizes = settings.get("prizes", [])
        
            # تصفية الجوائز المتاحة فقط
            available_prizes = [p for p in prizes if p.get("remaining", 0) > 0]
        
            if not available_prizes:
                # إذا لم توجد جوائز متاحة، إرجاع جائزة افتراضية
                return {"type": "nothing", "value": 0, "probability": 100}
        
            # حساب الاحتمالات الإجمالية
            total_prob = sum(prize.get("probability", 0) for prize in available_prizes)
            rand = random.randint(1, total_prob)
        
            current_prob = 0
            for prize in available_prizes:
                current_prob += prize.get("probability", 0)
                if rand <= current_prob:
                    # تقليل الكمية المتاحة
                    prize["remaining"] = prize.get("remaining", 0) - 1
                    self.save_data()
                
                    return {
                        "type": prize["type"],
                        "value": prize["value"],
                        "original_prize": prize
                    }
        
            return available_prizes[0]  # جائزة افتراضية إذا حدث خطأ
        
        except Exception as e:
            logger.error(f"Error getting available prize: {e}")
            return {"type": "points", "value": 10, "probability": 100}

    def create_gift_code_prizes(self, points_value, count):
        """إنشاء أكواد هدايا للجوائز"""
        try:
            created_codes = []
            for i in range(count):
                code_data = {
                    'code': self.generate_gift_code(),
                    'points': points_value,
                    'max_uses': 1,
                    'used_count': 0,
                    'used_by': [],
                    'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'created_by': 'system_prize'
                }
            
                if self.add_gift_code(code_data):
                    created_codes.append(code_data['code'])
        
            return created_codes
        
        except Exception as e:
            logger.error(f"Error creating gift code prizes: {e}")
            return []

# Data.py - الجزء 6/7 - محدث بنظام سهم الحظ

    # ✅ دوال مساعدة لنظام سهم الحظ
    def get_arrow_prize_distribution(self):
        """الحصول على توزيع الجوائز"""
        try:
            settings = self.get_luck_arrow_settings()
            prizes = settings.get("prizes", [])
            
            distribution = []
            for prize in prizes:
                distribution.append({
                    "type": prize["type"],
                    "value": prize["value"],
                    "probability": prize["probability"],
                    "text": self.get_prize_text(prize)
                })
            
            return distribution
        except Exception as e:
            logger.error(f"Error getting prize distribution: {e}")
            return []

    def update_prize_distribution(self, new_prizes):
        """تحديث توزيع الجوائز"""
        try:
            settings = self.get_luck_arrow_settings()
            settings["prizes"] = new_prizes
            return self.save_data()
        except Exception as e:
            logger.error(f"Error updating prize distribution: {e}")
            return False

    def get_user_arrow_info(self, user_id):
        """الحصول على معلومات أسهم المستخدم"""
        try:
            user_id = str(user_id)
            user_data = self.get_user_arrows(user_id)
            settings = self.get_luck_arrow_settings()
            
            return {
                "total_arrows": user_data.get("total_arrows", 0),
                "used_today": user_data.get("used_today", 0),
                "daily_limit": settings.get("daily_spin_limit", 10),
                "remaining_today": max(0, settings.get("daily_spin_limit", 10) - user_data.get("used_today", 0)),
                "last_used": user_data.get("last_used"),
                "history_count": len(user_data.get("history", []))
            }
        except Exception as e:
            logger.error(f"Error getting user arrow info: {e}")
            return {
                "total_arrows": 0,
                "used_today": 0,
                "daily_limit": 10,
                "remaining_today": 10,
                "last_used": None,
                "history_count": 0
            }

    def get_top_arrow_users(self, limit=10):
        """الحصول على أفضل المستخدمين في سهم الحظ"""
        try:
            users_data = []
            for user_id, arrow_data in self.data.get("luck_arrows", {}).items():
                if arrow_data.get("total_arrows", 0) > 0:
                    users_data.append({
                        "user_id": user_id,
                        "total_arrows": arrow_data.get("total_arrows", 0),
                        "total_spins": len(arrow_data.get("history", [])),
                        "last_used": arrow_data.get("last_used")
                    })
            
            # ترتيب حسب عدد الأسهم
            users_data.sort(key=lambda x: x["total_arrows"], reverse=True)
            return users_data[:limit]
        except Exception as e:
            logger.error(f"Error getting top arrow users: {e}")
            return []

    def get_recent_arrow_winners(self, limit=10):
        """الحصول على أحدث الفائزين"""
        try:
            winners = []
            for user_id, arrow_data in self.data.get("luck_arrows", {}).items():
                history = arrow_data.get("history", [])
                for entry in history[-5:]:  # آخر 5 رميات لكل مستخدم
                    if entry.get("won", False):
                        winners.append({
                            "user_id": user_id,
                            "prize": entry.get("prize", {}),
                            "timestamp": entry.get("timestamp"),
                            "prize_text": self.get_prize_text(entry.get("prize", {}))
                        })
            
            # ترتيب حسب الوقت
            winners.sort(key=lambda x: x["timestamp"], reverse=True)
            return winners[:limit]
        except Exception as e:
            logger.error(f"Error getting recent winners: {e}")
            return []

    def export_arrow_data(self):
        """تصدير بيانات سهم الحظ"""
        try:
            data = {
                "settings": self.get_luck_arrow_settings(),
                "total_users": len(self.data.get("luck_arrows", {})),
                "active_users": sum(1 for data in self.data.get("luck_arrows", {}).values() 
                                  if data.get("total_arrows", 0) > 0),
                "total_arrows": sum(data.get("total_arrows", 0) 
                                  for data in self.data.get("luck_arrows", {}).values()),
                "total_spins": sum(len(data.get("history", [])) 
                                 for data in self.data.get("luck_arrows", {}).values()),
                "box_status": self.get_box_status(),
                "prize_distribution": self.get_arrow_prize_distribution()
            }
            return data
        except Exception as e:
            logger.error(f"Error exporting arrow data: {e}")
            return {}

    def import_arrow_data(self, data):
        """استيراد بيانات سهم الحظ"""
        try:
            if "settings" in data:
                self.data["luck_arrow_settings"] = data["settings"]
            
            if "luck_arrows" in data:
                self.data["luck_arrows"] = data["luck_arrows"]
            
            return self.save_data()
        except Exception as e:
            logger.error(f"Error importing arrow data: {e}")
            return False

    # ✅ دوال للإحصائيات والتقارير
    def get_arrow_daily_stats(self):
        """الحصول على إحصائيات يومية لسهم الحظ"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            stats = {
                "date": today,
                "total_spins": 0,
                "successful_spins": 0,
                "points_won": 0,
                "arrows_won": 0,
                "gift_codes_won": 0,
                "nothing_count": 0
            }
            
            for user_data in self.data.get("luck_arrows", {}).values():
                for history_entry in user_data.get("history", []):
                    if history_entry.get("timestamp", "").startswith(today):
                        stats["total_spins"] += 1
                        prize = history_entry.get("prize", {})
                        
                        if history_entry.get("won", False):
                            stats["successful_spins"] += 1
                            
                            if prize["type"] == "points":
                                stats["points_won"] += prize["value"]
                            elif prize["type"] == "arrow":
                                stats["arrows_won"] += prize["value"]
                            elif prize["type"] == "gift_code":
                                stats["gift_codes_won"] += 1
                        else:
                            stats["nothing_count"] += 1
            
            return stats
        except Exception as e:
            logger.error(f"Error getting daily stats: {e}")
            return {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "total_spins": 0,
                "successful_spins": 0,
                "points_won": 0,
                "arrows_won": 0,
                "gift_codes_won": 0,
                "nothing_count": 0
            }

    def get_arrow_weekly_report(self):
        """الحصول على تقرير أسبوعي"""
        try:
            report = {
                "start_date": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
                "end_date": datetime.now().strftime("%Y-%m-%d"),
                "total_spins": 0,
                "successful_spins": 0,
                "points_distributed": 0,
                "arrows_distributed": 0,
                "gift_codes_distributed": 0,
                "unique_users": 0,
                "daily_average": 0
            }
            
            # حساب الإحصائيات للأسبوع الماضي
            for user_data in self.data.get("luck_arrows", {}).values():
                user_spins = 0
                for history_entry in user_data.get("history", []):
                    entry_date = history_entry.get("timestamp", "").split()[0]
                    if entry_date >= report["start_date"]:
                        report["total_spins"] += 1
                        user_spins += 1
                        
                        prize = history_entry.get("prize", {})
                        if history_entry.get("won", False):
                            report["successful_spins"] += 1
                            
                            if prize["type"] == "points":
                                report["points_distributed"] += prize["value"]
                            elif prize["type"] == "arrow":
                                report["arrows_distributed"] += prize["value"]
                            elif prize["type"] == "gift_code":
                                report["gift_codes_distributed"] += 1
                
                if user_spins > 0:
                    report["unique_users"] += 1
            
            report["daily_average"] = report["total_spins"] / 7 if report["total_spins"] > 0 else 0
            
            return report
        except Exception as e:
            logger.error(f"Error getting weekly report: {e}")
            return {
                "start_date": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
                "end_date": datetime.now().strftime("%Y-%m-%d"),
                "total_spins": 0,
                "successful_spins": 0,
                "points_distributed": 0,
                "arrows_distributed": 0,
                "gift_codes_distributed": 0,
                "unique_users": 0,
                "daily_average": 0
            }

# Data.py - الجزء 7/7 - محدث بنظام سهم الحظ
    # ✅ دوال للتحكم المتقدم في نظام سهم الحظ
    def set_daily_spin_limit(self, limit):
        """تعيين الحد اليومي للرميات"""
        try:
            settings = self.get_luck_arrow_settings()
            settings["daily_spin_limit"] = max(1, min(limit, 100))  # بين 1 و100
            return self.save_data()
        except Exception as e:
            logger.error(f"Error setting daily spin limit: {e}")
            return False

    def set_invite_rewards(self, points, arrows):
        """تعيين مكافآت الدعوة"""
        try:
            settings = self.get_luck_arrow_settings()
            settings["invite_points"] = max(0, points)
            settings["invite_arrows"] = max(0, arrows)
            return self.save_data()
        except Exception as e:
            logger.error(f"Error setting invite rewards: {e}")
            return False

    def reset_user_arrows(self, user_id):
        """إعادة تعيين أسهم مستخدم معين"""
        try:
            user_id = str(user_id)
            if user_id in self.data.get("luck_arrows", {}):
                self.data["luck_arrows"][user_id] = {
                    "total_arrows": 0,
                    "used_today": 0,
                    "last_used": None,
                    "history": []
                }
                return self.save_data()
            return False
        except Exception as e:
            logger.error(f"Error resetting user arrows: {e}")
            return False

    def clear_arrow_history(self, user_id):
        """مسح سجل رميات مستخدم"""
        try:
            user_id = str(user_id)
            if user_id in self.data.get("luck_arrows", {}):
                self.data["luck_arrows"][user_id]["history"] = []
                return self.save_data()
            return False
        except Exception as e:
            logger.error(f"Error clearing arrow history: {e}")
            return False

    def get_arrow_leaderboard(self, by='arrows'):
        """الحصول على لوحة المتصدرين"""
        try:
            leaderboard = []
            for user_id, arrow_data in self.data.get("luck_arrows", {}).items():
                if by == 'arrows':
                    score = arrow_data.get("total_arrows", 0)
                elif by == 'spins':
                    score = len(arrow_data.get("history", []))
                elif by == 'wins':
                    score = sum(1 for entry in arrow_data.get("history", []) 
                              if entry.get("won", False))
                else:
                    score = arrow_data.get("total_arrows", 0)
                
                if score > 0:
                    leaderboard.append({
                        "user_id": user_id,
                        "score": score,
                        "last_active": arrow_data.get("last_used", "غير معروف")
                    })
            
            leaderboard.sort(key=lambda x: x["score"], reverse=True)
            return leaderboard[:20]  # أفضل 20
        except Exception as e:
            logger.error(f"Error getting leaderboard: {e}")
            return []

    def backup_arrow_data(self):
        """إنشاء نسخة احتياطية لبيانات سهم الحظ"""
        try:
            backup_data = {
                "luck_arrow_settings": self.data.get("luck_arrow_settings", {}),
                "luck_arrows": self.data.get("luck_arrows", {}),
                "backup_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            backup_file = f"arrow_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=4)
            
            logger.info(f"تم إنشاء نسخة احتياطية لبيانات سهم الحظ: {backup_file}")
            return True
        except Exception as e:
            logger.error(f"Error backing up arrow data: {e}")
            return False

    def restore_arrow_data(self, backup_file):
        """استعادة بيانات سهم الحظ من نسخة احتياطية"""
        try:
            if not os.path.exists(backup_file):
                return False, "الملف غير موجود"
            
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            if "luck_arrow_settings" in backup_data:
                self.data["luck_arrow_settings"] = backup_data["luck_arrow_settings"]
            
            if "luck_arrows" in backup_data:
                self.data["luck_arrows"] = backup_data["luck_arrows"]
            
            self.save_data()
            logger.info(f"تم استعادة بيانات سهم الحظ من: {backup_file}")
            return True, "تم الاستعادة بنجاح"
        except Exception as e:
            logger.error(f"Error restoring arrow data: {e}")
            return False, f"خطأ في الاستعادة: {e}"

    # ✅ دوال للدمج مع الأنظمة الأخرى
    def add_arrows_on_task_completion(self, user_id, task_value):
        """إضافة أسهم عند إكمال المهمة"""
        try:
            # إضافة سهم واحد لكل 10 نقاط من قيمة المهمة
            arrows_to_add = max(1, task_value // 10)
            return self.add_arrows_to_user(user_id, arrows_to_add)
        except Exception as e:
            logger.error(f"Error adding arrows on task completion: {e}")
            return False

    def add_arrows_on_level_up(self, user_id, new_level):
        """إضافة أسهم عند الترقية لمستوى جديد"""
        try:
            # إضافة أسهم حسب المستوى
            arrows_map = {
                100: 5,    # مستوى نشط
                500: 10,   # مستوى محترف
                1000: 20,  # مستوى خبير
                5000: 50   # مستوى أسطورة
            }
            
            arrows_to_add = arrows_map.get(new_level, 0)
            if arrows_to_add > 0:
                return self.add_arrows_to_user(user_id, arrows_to_add)
            return False
        except Exception as e:
            logger.error(f"Error adding arrows on level up: {e}")
            return False

    def add_arrows_daily_login(self, user_id, streak):
        """إضافة أسهم للتسجيل اليومي المتواصل"""
        try:
            # إضافة أسهم حسب عدد الأيام المتواصلة
            arrows_to_add = min(streak, 7)  # حد أقصى 7 أسهم
            return self.add_arrows_to_user(user_id, arrows_to_add)
        except Exception as e:
            logger.error(f"Error adding arrows for daily login: {e}")
            return False

    # ✅ دوال للتحقق والصيانة
    def validate_arrow_data(self):
        """التحقق من صحة بيانات سهم الحظ"""
        try:
            issues = []
            
            # التحقق من الإعدادات
            settings = self.get_luck_arrow_settings()
            if not settings:
                issues.append("الإعدادات مفقودة")
            
            # التحقق من أن مجموع الاحتمالات = 100
            total_prob = sum(prize.get("probability", 0) for prize in settings.get("prizes", []))
            if total_prob != 100:
                issues.append(f"مجموع الاحتمالات ليس 100% (حاليًا: {total_prob}%)")
            
            # التحقق من بيانات المستخدمين
            for user_id, arrow_data in self.data.get("luck_arrows", {}).items():
                if not isinstance(arrow_data.get("total_arrows", 0), int):
                    issues.append(f"عدد الأسهم غير صحيح للمستخدم {user_id}")
                
                if len(arrow_data.get("history", [])) > 100:
                    issues.append(f"سجل المستخدم {user_id} كبير جدًا")
            
            return issues if issues else ["جميع البيانات صحيحة"]
        except Exception as e:
            logger.error(f"Error validating arrow data: {e}")
            return [f"خطأ في التحقق: {e}"]

    def cleanup_arrow_data(self):
        """تنظيف بيانات سهم الحظ"""
        try:
            cleaned_count = 0
            
            # إزالة المستخدمين الذين ليس لديهم أسهم ولا سجل
            users_to_remove = []
            for user_id, arrow_data in self.data.get("luck_arrows", {}).items():
                if (arrow_data.get("total_arrows", 0) == 0 and 
                    len(arrow_data.get("history", [])) == 0 and
                    arrow_data.get("used_today", 0) == 0):
                    users_to_remove.append(user_id)
            
            for user_id in users_to_remove:
                del self.data["luck_arrows"][user_id]
                cleaned_count += 1
            
            # تقليل حجم السجل للمستخدمين النشطين
            for user_id, arrow_data in self.data.get("luck_arrows", {}).items():
                history = arrow_data.get("history", [])
                if len(history) > 50:  # الاحتفاظ بآخر 50 رمية فقط
                    arrow_data["history"] = history[-50:]
                    cleaned_count += len(history) - 50
            
            if cleaned_count > 0:
                self.save_data()
            
            return cleaned_count
        except Exception as e:
            logger.error(f"Error cleaning arrow data: {e}")
            return 0

    # ✅ دالة مساعدة نهائية للحصول على اسم المستخدم
    async def get_referrer_name(self, user_id, context):
        """الحصول على اسم المدعو بشكل غير متزامن"""
        try:
            user = await context.bot.get_chat(user_id)
            return user.first_name or f"المستخدم {user_id}"
        except:
            return f"المستخدم {user_id}"

# إنشاء كائن قاعدة البيانات العالمي
db = Database()

