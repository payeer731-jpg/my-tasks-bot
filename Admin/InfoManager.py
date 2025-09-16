# Admin/InfoManager.py
from Data import db
from datetime import datetime

def format_dynamic_text(text, user_data=None):
    """تنسيق النص مع المتغيرات الديناميكية"""
    if not user_data:
        user_data = {}
    
    variables = {
        '{user_id}': user_data.get('user_id', ''),
        '{user_name}': user_data.get('user_name', ''),
        '{points}': user_data.get('points', 0),
        '{level_name}': user_data.get('level_name', 'مبتدئ 🌱'),
        '{active_tasks}': user_data.get('active_tasks', 0),
        '{current_date}': user_data.get('current_date', datetime.now().strftime("%Y-%m-%d")),
        '{total_earned}': user_data.get('total_earned', 0),
        '{invites_count}': user_data.get('invites_count', 0)
    }
    
    for var, value in variables.items():
        text = text.replace(var, str(value))
    
    return text

def get_welcome_message(user_id=None):
    """الحصول على رسالة الترحيب"""
    welcome_text = db.data.get("welcome_message", "🎊 مرحباً بك في بوت المهام!")
    
    if user_id:
        user_data = db.get_user(user_id)
        return format_dynamic_text(welcome_text, {
            'user_id': user_id,
            'user_name': '',  # سيتم ملؤه لاحقاً
            'points': user_data.get('points', 0),
            'level_name': db.get_user_level_name(user_id),
            'active_tasks': len([t for t in db.get_user_tasks(user_id) if t.get("status") == "active"])
        })
    
    return welcome_text