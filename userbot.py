import os
import sqlite3
import asyncio
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession

# إعداد المتغيرات الأساسية من البيئة أو القيم الافتراضية
API_ID = int(os.environ.get("API_ID", 2040))
API_HASH = os.environ.get("API_HASH", "b18441a1ff607e10a989891a5462e627")
STRING_SESSION = os.environ.get("STRING_SESSION", "")

PHONE_NUMBER = "+9647721606233"
USER_ID = 8164462667

# إنشاء العميل والاتصال بقاعدة البيانات
client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
db = sqlite3.connect("database.db", check_same_thread=False)
cursor = db.cursor()

# إنشاء الجدول إذا لم يكن موجوداً
cursor.execute("""
CREATE TABLE IF NOT EXISTS groups (
    key TEXT UNIQUE,
    chat_id INTEGER,
    msg_id INTEGER
)
""")
db.commit()

# --- دالات التعامل مع قاعدة البيانات ---
def save_group(key, chat_id, msg_id):
    try:
        with db:
            cursor.execute(
                "INSERT OR REPLACE INTO groups (key, chat_id, msg_id) VALUES (?, ?, ?)",
                (key, chat_id, msg_id)
            )
        return True
    except Exception as e:
        print(f"Error saving to DB: {e}")
        return False

def get_all_groups():
    cursor.execute("SELECT key, chat_id, msg_id FROM groups")
    return cursor.fetchall()

# --- مستمع الأحداث والرسائل ---

# 1. أمر حفظ المجموعة الحالية
@client.on(events.NewMessage(outgoing=True, pattern=r'\.save (.+)'))
async def handle_save(event):
    key = event.pattern_match.group(1).strip()
    chat_id = event.chat_id
    msg_id = event.id
    
    if save_group(key, chat_id, msg_id):
        await event.edit(f"✅ تم حفظ هذه المجموعة بنجاح تحت مفتاح: **{key}**")
    else:
        await event.edit("❌ حدث خطأ أثناء محاولة الحفظ في قاعدة البيانات.")

# 2. أمر عرض القائمة مع أزرار تفاعلية
@client.on(events.NewMessage(outgoing=True, pattern=r'\.list'))
async def handle_list(event):
    saved_items = get_all_groups()
    
    if not saved_items:
        await event.edit("📭 لا توجد أي مجموعات محفوظة حالياً.")
        return
    
    buttons = []
    text = "📂 **قائمة المجموعات المحفوظة:**\n\n"
    
    for index, (key, chat_id, msg_id) in enumerate(saved_items, start=1):
        text += f"{index}. **{key}** (Chat ID: `{chat_id}`)\n"
        # إنشاء رابط تليجرام مباشر للرسالة المحفوظة داخل المجموعة
        # المجموعات الخارقة (Supergroups) تبدأ معرفاتها غالباً بـ -100
        clean_chat_id = str(chat_id).replace("-100", "")
        msg_url = f"https://t.me{clean_chat_id}/{msg_id}"
        
        buttons.append([Button.url(f"🔗 انتقال إلى {key}", msg_url)])
        
    await event.edit(text, buttons=buttons)

# --- تشغيل البوت ---
async def main():
    print("جاري تشغيل البوت والاتصال بتليجرام...")
    # إذا كانت الجلسة فارغة، سيطلب الكود التحقق عبر رقم الهاتف في الترمينال
    await client.start(phone=PHONE_NUMBER)
    print("Bot ready... البوت يعمل الآن بنجاح!")
    await client.run_until_disconnected()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
    
