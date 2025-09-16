# LinkValidator.py
import re
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class LinkValidator:
    @staticmethod
    def validate_link(link, task_type):
        """
        التحقق من صحة الرابط حسب نوع المهمة
        """
        if not link or not task_type:
            return False, "❌ الرابط أو نوع المهمة غير صالح"
        
        # تنظيف الرابط وإزالة المسافات
        link = link.strip()
        
        # التحقق من أن الرابط يبدأ بـ http أو https
        if not link.startswith(('http://', 'https://')):
            link = 'https://' + link
        
        # التحقق من الصيغة العامة للرابط
        if not LinkValidator._is_valid_url(link):
            return False, "❌ صيغة الرابط غير صحيحة"
        
        # التحقق حسب نوع المهمة
        validation_result = LinkValidator._validate_by_type(link, task_type)
        if not validation_result[0]:
            return validation_result
        
        return True, "✅ الرابط صالح"
    
    @staticmethod
    def _is_valid_url(url):
        """التحقق من صيغة الرابط"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    @staticmethod
    def _validate_by_type(link, task_type):
        """التحقق من الرابط حسب نوع المهمة"""
        domain = urlparse(link).netloc.lower()
        
        validation_rules = {
            "telegram": [
                r"(t\.me|telegram\.me|telegram\.org)",
                "❌ روابط تليجرام فقط مسموحة (t.me أو telegram.me)"
            ],
            "whatsapp": [
                r"(wa\.me|whatsapp\.com|chat\.whatsapp\.com)",
                "❌ روابط واتساب فقط مسموحة (wa.me أو whatsapp.com)"
            ],
            "instagram": [
                r"(instagram\.com|instagr\.am)",
                "❌ روابط انستجرام فقط مسموحة (instagram.com)"
            ],
            "facebook": [
                r"(facebook\.com|fb\.com|fb\.me)",
                "❌ روابط فيسبوك فقط مسموحة (facebook.com)"
            ],
            "youtube": [
                r"(youtube\.com|youtu\.be)",
                "❌ روابط يوتيوب فقط مسموحة (youtube.com)"
            ],
            "tiktok": [
                r"(tiktok\.com|vm\.tiktok\.com)",
                "❌ روابط تيك توك فقط مسموحة (tiktok.com)"
            ],
            "website": [
                r".*",  # جميع الروابط مسموحة
                "✅ رابط الموقع صالح"
            ]
        }
        
        if task_type not in validation_rules:
            return False, "❌ نوع المهمة غير معروف"
        
        pattern, error_message = validation_rules[task_type]
        
        if not re.search(pattern, domain):
            return False, error_message
        
        return True, "✅ الرابط صالح للنوع المحدد"

# دالة مساعدة للاستخدام السريع
def validate_task_link(link, task_type):
    """دالة مساعدة للتحقق من الرابط"""
    return LinkValidator.validate_link(link, task_type)