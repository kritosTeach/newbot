FROM python:3.11-slim

WORKDIR /app

# نسخ متطلبات التطبيق
COPY requirements.txt .

# تثبيت المكتبات
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي الملفات
COPY . .

# تشغيل البوت
CMD ["python", "bot.py"]
