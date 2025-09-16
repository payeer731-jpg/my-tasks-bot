# Admin/Db.py
from Data import db
import logging

logger = logging.getLogger(__name__)

def admin_get_admins():
    return db.get_admins()

def admin_add_admin(user_id):
    return db.add_admin(user_id)

def admin_remove_admin(user_id):
    return db.remove_admin(user_id)

def admin_get_blocked_users():
    return db.get_blocked_users()

def admin_block_user(user_id):
    return db.block_user(user_id)

def admin_unblock_user(user_id):
    return db.unblock_user(user_id)

def admin_get_tasks():
    return db.get_tasks()

def admin_add_task(task):
    tasks = db.get_tasks()
    tasks.append(task)
    return db.save_data()

def admin_remove_task(index):
    tasks = db.get_tasks()
    if 0 <= index < len(tasks):
        tasks.pop(index)
        return db.save_data()
    return False

def admin_reset_tasks():
    db.data["tasks"] = []
    return db.save_data()

def admin_get_invite_points():
    return db.get_invite_points()

def admin_set_invite_points(points):
    return db.set_invite_points(points)

def admin_add_points_to_user(user_id, points):
    return db.add_points_to_user(user_id, points)

def admin_remove_points_from_user(user_id, points):
    return db.remove_points_from_user(user_id, points)

def admin_reset_all_points():
    for user_id in db.data["users"]:
        db.data["users"][user_id]["points"] = 0
    return db.save_data()

# ✅ الإضافة الجديدة
def admin_is_invite_system_enabled():
    return db.data.get("invite_system_enabled", True)

def admin_toggle_invite_system(enabled):
    try:
        db.data["invite_system_enabled"] = enabled
        return db.save_data()
    except Exception as e:
        logger.error(f"Error toggling invite system: {e}")
        return False