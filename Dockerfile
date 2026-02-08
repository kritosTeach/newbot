FROM python:3.11-slim

WORKDIR /app

# تثبيت المكتبات النظامية
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# نسخ متطلبات التطبيق
COPY requirements.txt .

# تثبيت مكتبات Python
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي الملفات
COPY . .

# تشغيل البوت
CMD ["python", "bot.py"]
