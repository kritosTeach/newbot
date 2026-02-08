import os
import sqlite3
import re
# استخدم telebot بدل python-telegram-bot (أسهل وأقل مشاكل)
import telebot
from telebot import types

# 🔥 ضع التوكن هنا مباشرة
TELEGRAM_TOKEN = "8322471161:AAEwthafhAceZSx-dAqHfO8Pzpegf9ppNEc"

# إنشاء كائن البوت
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# تهيئة قاعدة البيانات
def init_db():
    db_path = '/tmp/emails.db' if 'RENDER' in os.environ else 'emails.db'
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS emails
                 (email TEXT PRIMARY KEY, 
                  user_id INTEGER,
                  username TEXT,
                  description TEXT,
                  date TEXT DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()
    print(f"✅ قاعدة بيانات الإيميلات جاهزة في: {db_path}")
    return db_path

# التحقق من صحة الإيميل
def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# التحقق من وجود الإيميل
def check_email(email):
    db_path = '/tmp/emails.db' if 'RENDER' in os.environ else 'emails.db'
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT email, user_id, username, description, date FROM emails WHERE email=?", (email,))
    result = c.fetchone()
    conn.close()
    return result

# حجز الإيميل مع الوصف
def reserve_email(email, user_id, username, description):
    db_path = '/tmp/emails.db' if 'RENDER' in os.environ else 'emails.db'
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO emails (email, user_id, username, description) VALUES (?, ?, ?, ?)", 
                 (email, user_id, username, description))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    finally:
        conn.close()
    return success

# حذف الإيميل
def delete_email_from_db(email, user_id):
    db_path = '/tmp/emails.db' if 'RENDER' in os.environ else 'emails.db'
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("DELETE FROM emails WHERE email=? AND user_id=?", (email, user_id))
    deleted = c.rowcount
    conn.commit()
    conn.close()
    return deleted > 0

# أمر /start
@bot.message_handler(commands=['start'])
def start(message):
    user = message.from_user
    bot.reply_to(message,
        f'📧 مرحباً {user.first_name}!\n\n'
        'أنا بوت حجز الإيميلات مع الوصف\n\n'
        '🔹 /reserve <إيميل> <وصف> - لحجز إيميل مع وصف\n'
        '🔹 /reeserv <إيميل> <وصف> - نفس الأمر (بديل)\n'
        '🔹 /check <إيميل> - للتحقق من إيميل\n'
        '🔹 /my_emails - لعرض إيميلاتي مع زر الحذف\n'
        '🔹 /help - للمساعدة'
    )

# أمر /reserve لحجز إيميل مع وصف
@bot.message_handler(commands=['reserve', 'reeserv'])
def reserve(message):
    user = message.from_user
    text = message.text.split()
    
    if len(text) < 2:
        bot.reply_to(message,
            '❌ الرجاء إدخال إيميل ووصف\n'
            '📝 مثال: /reserve example@gmail.com هذا وصف للإيميل'
        )
        return
    
    # نأخذ أول كلمة بعد الأمر كإيميل والباقي كوصف
    email = text[1].strip().lower()
    description = ' '.join(text[2:]) if len(text) > 2 else "لا يوجد وصف"
    
    # التحقق من صحة الإيميل
    if not is_valid_email(email):
        bot.reply_to(message,
            '❌ صيغة الإيميل غير صحيحة\n'
            '📝 مثال صحيح: username@domain.com\n'
            '🔹 يجب أن يحتوي على @ ونقطة\n'
            '🔹 يجب أن يكون اسم النطاق صحيحاً'
        )
        return
    
    # التحقق من أن الإيميل غير محجوز
    if check_email(email):
        bot.reply_to(message, f'❌ الإيميل {email} محجوز بالفعل')
        return
    
    # حجز الإيميل
    if reserve_email(email, user.id, user.username, description):
        bot.reply_to(message,
            f'✅ تم حجز الإيميل بنجاح\n'
            f'📧 {email}\n'
            f'📝 الوصف: {description}\n'
            f'👤 بواسطة: @{user.username or user.first_name}'
        )
    else:
        bot.reply_to(message, '❌ فشل في حجز الإيميل')

# أمر /check للتحقق من الإيميل
@bot.message_handler(commands=['check'])
def check(message):
    text = message.text.split()
    
    if len(text) < 2:
        bot.reply_to(message, '❌ الرجاء إدخال إيميل\nمثال: /check example@gmail.com')
        return
    
    email = text[1].strip().lower()
    
    # التحقق من صحة الإيميل أولاً
    if not is_valid_email(email):
        bot.reply_to(message, '❌ صيغة الإيميل غير صحيحة')
        return
    
    result = check_email(email)
    
    if result:
        email_addr, user_id, username, description, date = result
        response = (
            f'📌 معلومات الإيميل:\n'
            f'📧 {email_addr}\n'
            f'📝 الوصف: {description}\n'
            f'👤 المستخدم: {username or "غير معروف"}\n'
            f'🆔 ID: {user_id}\n'
            f'📅 تاريخ الحجز: {date}'
        )
        bot.reply_to(message, response)
    else:
        bot.reply_to(message, f'✅ الإيميل {email} متاح للحجز')

# أمر /my_emails لعرض الإيميلات مع زر الحذف
@bot.message_handler(commands=['my_emails'])
def my_emails(message):
    user = message.from_user
    
    db_path = '/tmp/emails.db' if 'RENDER' in os.environ else 'emails.db'
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT email, description, date FROM emails WHERE user_id=? ORDER BY date DESC", (user.id,))
    emails = c.fetchall()
    conn.close()
    
    if emails:
        # إنشاء لوحة مفاتيح مع أزرار الحذف
        keyboard = types.InlineKeyboardMarkup()
        
        for email, description, date in emails:
            # إضافة زر الحذف لكل إيميل
            keyboard.add(
                types.InlineKeyboardButton(
                    text=f"🗑️ حذف {email[:15]}...",
                    callback_data=f"delete_{email}"
                )
            )
        
        # إعداد قائمة الإيميلات
        response = "📧 إيميلاتك المحجوزة:\n\n"
        for i, (email, description, date) in enumerate(emails, 1):
            response += f"{i}. {email}\n"
            response += f"   📝 {description}\n"
            response += f"   📅 {date}\n\n"
        
        response += f"📊 الإجمالي: {len(emails)} إيميل\n"
        response += "🔽 اضغط على الزر لحذف الإيميل"
        
        bot.send_message(message.chat.id, response, reply_markup=keyboard)
    else:
        bot.reply_to(message, "📭 ليس لديك إيميلات محجوزة بعد")

# معالجة زر الحذف
@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_'))
def delete_button_callback(call):
    user_id = call.from_user.id
    email = call.data.replace("delete_", "")
    
    # حذف الإيميل من قاعدة البيانات
    if delete_email_from_db(email, user_id):
        # إرسال رسالة تأكيد
        bot.answer_callback_query(call.id, "✅ تم حذف الإيميل!")
        
        # تحديث الرسالة
        bot.edit_message_text(
            f"✅ تم حذف الإيميل: {email}\n"
            f"🔄 يتم تحديث القائمة...",
            call.message.chat.id,
            call.message.message_id
        )
        
        # إعادة عرض الإيميلات المتبقية
        db_path = '/tmp/emails.db' if 'RENDER' in os.environ else 'emails.db'
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT email, description, date FROM emails WHERE user_id=? ORDER BY date DESC", (user_id,))
        emails = c.fetchall()
        conn.close()
        
        if emails:
            # إنشاء لوحة مفاتيح جديدة
            keyboard = types.InlineKeyboardMarkup()
            
            for email, description, date in emails:
                keyboard.add(
                    types.InlineKeyboardButton(
                        text=f"🗑️ حذف {email[:15]}...",
                        callback_data=f"delete_{email}"
                    )
                )
            
            # إعداد قائمة الإيميلات المحدثة
            response = "📧 إيميلاتك المحجوزة:\n\n"
            for i, (email, description, date) in enumerate(emails, 1):
                response += f"{i}. {email}\n"
                response += f"   📝 {description}\n"
                response += f"   📅 {date}\n\n"
            
            response += f"📊 الإجمالي: {len(emails)} إيميل\n"
            response += "🔽 اضغط على الزر لحذف الإيميل"
            
            bot.edit_message_text(
                response,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=keyboard
            )
        else:
            bot.edit_message_text(
                "✅ تم حذف جميع الإيميلات\n📭 ليس لديك إيميلات محجوزة حالياً",
                call.message.chat.id,
                call.message.message_id
            )
    else:
        bot.answer_callback_query(call.id, "❌ فشل في حذف الإيميل!")

# أمر /help
@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
📚 أوامر بوت حجز الإيميلات:

🔹 /start - بدء البوت
🔹 /reserve <إيميل> <وصف> - لحجز إيميل مع وصف
🔹 /reeserv <إيميل> <وصف> - نفس الأمر (بديل)
🔹 /check <إيميل> - التحقق من حالة إيميل
🔹 /my_emails - عرض إيميلاتك مع زر الحذف
🔹 /help - عرض هذه الرسالة

📝 صيغة الإيميل الصحيحة:
- مثال: username@domain.com
- يجب أن يحتوي على @ ونقطة

📋 مثال لحجز إيميل مع وصف:
/reserve example@gmail.com هذا إيميل للعمل الرسمي

🗑️ لحذف إيميل:
1. استخدم /my_emails
2. اضغط على زر الحذف بجانب الإيميل
3. سيتم حذفه فوراً

⚠️ ملاحظات:
- الحجز دائم حتى تقوم بحذفه
- كل مستخدم يمكنه حذف إيميلاته فقط
- الإيميلات مخزنة بشكل آمن
"""
    bot.reply_to(message, help_text)

# الدالة الرئيسية
def main():
    print("✅" * 50)
    print("🤖 بوت حجز الإيميلات يبدأ التشغيل...")
    print(f"📧 البوت ID: {TELEGRAM_TOKEN.split(':')[0]}")
    print(f"🌍 البيئة: {'Render' if 'RENDER' in os.environ else 'Local'}")
    print("✅" * 50)
    
    # تهيئة قاعدة البيانات
    init_db()
    
    # بدء البوت
    print("🔹 البوت يبدأ الاستماع للرسائل...")
    bot.polling(none_stop=True, interval=0, timeout=20)

if __name__ == '__main__':
    main()
