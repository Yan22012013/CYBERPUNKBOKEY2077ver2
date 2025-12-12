import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import imaplib
import email
from email.header import decode_header
import re
import time
import json
import os
from datetime import datetime
from flask import Flask, request, render_template_string, session
from threading import Thread
import requests

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'rnd_i8JrgNvTYWqSDZqTjYKaH6GwmGS6')

# === НАСТРОЙКИ ===
SMTP_EMAIL = os.environ.get('SMTP_EMAIL', 'theforest1981@gmail.com')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', 'rhrq jdnj lupx ljiu')
IMAP_EMAIL = os.environ.get('IMAP_EMAIL', 'theforest1981@gmail.com')
IMAP_PASSWORD = os.environ.get('IMAP_PASSWORD', 'rhrq jdnj lupx ljiu')
DA_WIDGET_ID = os.environ.get('DA_WIDGET_ID', 'el_i_x1981')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
GAME_PRICE = 499

# Render persistent storage
DATA_DIR = '/tmp/data' if os.environ.get('PORT') else './data'
orders_file = os.path.join(DATA_DIR, 'orders.json')
logs_file = os.path.join(DATA_DIR, 'logs.txt')

os.makedirs(DATA_DIR, exist_ok=True)

orders = {}

KEYWORDS = [
    'ключ', 'ключик', 'код', 'код активации', 'код игры', 'код лицензии',
    'активация', 'активационный', 'лицензия', 'лицензионный', 'лицензионный ключ',
    'сирийный', 'серийный', 'серийник', 'серийный номер', 'код продукта',
    'key', 'steam key', 'gog key', 'cdkey', 'cd-key', 'product key',
    'activation code', 'activation key', 'license key', 'license code',
    'serial', 'serial number', 'serial key', 'code', 'game key',
    'cyberpunk', 'cyberpunk 2077', 'gog', 'steam', 'uplay', 'origin', 
    'epic', 'battle.net', 'ea app', 'ubisoft connect',
    'plati', 'plati.market', 'playerok', 'g2a', 'kinguin', 'eneba',
    'steam', 'gog', 'uplay', 'origin', 'epic games', 'battle.net'
]

def log_message(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log = f"[{timestamp}] {message}\n"
    try:
        with open(logs_file, 'a', encoding='utf-8') as f:
            f.write(log)
    except:
        pass
    print(log.strip())

def load_orders():
    global orders
    try:
        if os.path.exists(orders_file):
            with open(orders_file, 'r', encoding='utf-8') as f:
                orders.update(json.load(f))
            log_message(f"Загружено {len(orders)} заказов")
    except:
        orders = {}

def save_orders():
    try:
        with open(orders_file, 'w', encoding='utf-8') as f:
            json.dump(orders, f, ensure_ascii=False, indent=2)
    except:
        pass

load_orders()

def keep_alive():
    while True:
        try:
            time.sleep(840)
            requests.get(f"http://localhost:{os.environ.get('PORT', 5000)}/health", timeout=5)
            log_message("❤️ Keep-alive пинг отправлен (Render не уснет)")
        except:
            pass

@app.route('/')
def index():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>🎮 Cyberpunk 2077 — Автодоставка</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: system-ui, sans-serif; 
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh; padding: 20px; color: white;
        }
        .container { max-width: 500px; margin: 0 auto; padding: 40px 20px; }
        .card { 
            background: rgba(255,255,255,0.1); 
            backdrop-filter: blur(20px); border-radius: 24px; 
            padding: 50px 40px; border: 1px solid rgba(255,255,255,0.2);
            text-align: center; box-shadow: 0 25px 50px rgba(0,0,0,0.3);
        }
        h1 { font-size: 2.8em; color: #ff6b35; margin-bottom: 20px; }
        .price { 
            font-size: 3.5em; font-weight: 900; 
            background: linear-gradient(45deg, #28a745, #20c997);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            margin: 30px 0;
        }
        input { 
            width: 100%; padding: 20px; border: 2px solid rgba(255,255,255,0.3); 
            border-radius: 16px; background: rgba(255,255,255,0.9);
            font-size: 18px; color: #333; margin: 30px 0; box-sizing: border-box;
        }
        .btn { 
            width: 100%; padding: 25px; 
            background: linear-gradient(135deg, #ff6b35, #f7931e); 
            color: white; border: none; border-radius: 50px; 
            font-size: 22px; font-weight: 700; cursor: pointer; 
            transition: all 0.3s; margin: 10px 0;
        }
        .btn:hover { transform: translateY(-5px); box-shadow: 0 20px 40px rgba(255,107,53,0.4); }
        .status { padding: 20px; margin: 20px 0; border-radius: 16px; background: rgba(255,255,255,0.1); }
        .live-status { background: #28a745 !important; color: white; font-weight: 700; font-size: 1.3em; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1>🎮 Cyberpunk 2077</h1>
            <div class="price">3146 ₽</div>
            <div class="status live-status">
                ✅ Автоматическая доставка Steam/GOG ключей<br>
                ⚡ Ключ через 10-30 минут после оплаты
            </div>
            <input id="email" placeholder="📧 Email для получения ключа">
            <br>
            <button onclick="pay()" class="btn">💳 Оплатить 3146₽</button>
            <div class="status">
                <strong>⚡ Процесс:</strong><br>
                1️⃣ Оплатите 3146₽ в DonationAlerts<br>
                2️⃣ Ключ придет на указанную почту автоматически<br>
                3️⃣ Когда будете оплачивать ведите ту сумму которая указана на странице (3146)
            </div>
        </div>
    </div>
    <script>
        function pay() {
            const email = document.getElementById('email').value.trim();
            if (!email.includes('@')) {
                alert('❌ Введите корректный email!');
                return;
            }
            const url = `https://www.donationalerts.com/r/el_i_x1981?amount=499&message=${encodeURIComponent(email)}`;
            window.open(url, '_blank');
            alert('✅ Перейдите в DonationAlerts и оплатите 499₽\\nКлюч придет автоматически!');
        }
    </script>
</body>
</html>
    ''')

@app.route('/health')
def health():
    return "OK"

def login_page(error=''):
    return f'''
    <html><body style="background:black;color:lime;padding:50px;text-align:center;font-family:monospace">
        <h2 style="color:yellow">🔐 АДМИН ПАНЕЛЬ</h2>
        <p>{error}</p>
        <form method="post" style="margin:40px 0">
            <input name="password" type="password" placeholder="Пароль" 
                   style="width:350px;padding:20px;font-size:18px;margin:20px;border:2px solid lime;border-radius:10px;font-family:monospace">
            <br>
            <button type="submit" style="padding:20px 50px;background:lime;color:black;font-size:18px;border-radius:10px;font-weight:700">
                ВОЙТИ
            </button>
        </form>
        <p><a href="/" style="color:cyan">🏪 Главная страница</a></p>
    </body></html>
    '''

# ✅ ИСПРАВЛЕННЫЙ РОУТ /orders
@app.route('/orders', methods=['GET', 'POST'])
def admin_orders():
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == ADMIN_PASSWORD:
            session['admin'] = True
            return show_orders_page()
        else:
            return login_page('❌ Неверный пароль!')
    
    if session.get('admin'):
        return show_orders_page()
    return login_page()

# ✅ ИСПРАВЛЕННЫЙ РОУТ /logs
@app.route('/logs', methods=['GET', 'POST'])
def admin_logs():
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == ADMIN_PASSWORD:
            session['admin'] = True
            return show_logs_page()
        else:
            return login_page('❌ Неверный пароль!')
    
    if session.get('admin'):
        return show_logs_page()
    return login_page()

def show_orders_page():
    paid_count = len([o for o in orders.values() if o['status'] == 'paid'])
    return f'''
    <html><body style="background:black;color:lime;padding:30px;font-family:monospace">
        <h2 style="color:cyan">📋 ЗАКАЗЫ ({len(orders)} всего, {paid_count} PAID)</h2>
        <div style="background:#ff6b35;color:white;padding:25px;border-radius:15px;margin:20px 0;text-align:center">
            <h3>💰 Прибыль: <strong>{paid_count * 199}₽</strong> ({paid_count} × 199₽)</h3>
            <a href="https://plati.market/search/cyberpunk%202077?type=1" target="_blank" 
               style="padding:20px 40px;background:#28a745;color:white;text-decoration:none;border-radius:12px;font-weight:700;font-size:18px;display:inline-block">
                🛒 Plati.Market (250-320₽/ключ)
            </a><br><br>
            <small style="color:#ddd">📧 Почта для ключей: <strong>{SMTP_EMAIL}</strong></small>
        </div>
        <h3 style="color:yellow">📊 Список заказов:</h3>
        <pre style="background:#111;padding:20px;border-radius:10px;overflow:auto;max-height:500px;font-size:13px">{json.dumps(orders, indent=2, ensure_ascii=False)}</pre>
        <div style="margin-top:30px;padding:20px;background:#1a1a2e;border-radius:10px">
            <p><a href="/" style="color:cyan;font-size:18px">🏪 Публичная страница</a></p>
            <p><a href="/logs" style="color:yellow;font-size:18px">📝 Логи сервера (автообновление)</a> | 
            <a href="/logout" style="color:#ff6b35;font-size:18px">🚪 Выход</a></p>
        </div>
    </body></html>
    '''

def show_logs_page():
    try:
        with open(logs_file, 'r', encoding='utf-8') as f:
            logs = f.read()
        return f'''
        <html><body style="background:black;color:lime;padding:30px;font-family:monospace">
            <h2 style="color:cyan">📝 ЛОГИ СЕРВЕРА <span id="status" style="color:#28a745">🔄 Обновление каждые 3 сек (БЕЗ ЛИМИТОВ)</span></h2>
            <pre id="logs" style="background:#111;padding:20px;border-radius:10px;height:600px;overflow:auto;font-size:12px;white-space:pre-wrap">{logs}</pre>
            <script>
                setInterval(() => {{
                    fetch('/logs_data').then(r=>r.text()).then(data => {{
                        document.getElementById('logs').textContent = data;
                        document.getElementById('logs').scrollTop = document.getElementById('logs').scrollHeight;
                        document.getElementById('status').textContent = '✅ Обновлено ' + new Date().toLocaleTimeString();
                    }});
                }}, 3000);
            </script>
            <p><a href="/orders" style="color:lime;font-size:16px">📋 Заказы</a> | 
            <a href="/" style="color:cyan;font-size:16px">🏪 Главная</a></p>
        </body></html>
        '''
    except:
        return "Логи недоступны"

@app.route('/logs_data', methods=['GET', 'POST'])
def logs_data():
    if not session.get('admin'):
        return "Unauthorized", 401
    try:
        with open(logs_file, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return ""

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return '<script>window.location="/"</script>'

def extract_key_from_email(body):
    patterns = [
        r'([A-Z0-9]{5}-[A-Z0-9]{5}-[A-Z0-9]{5})',
        r'([0-9A-Z]{15})',
        r'([A-Z0-9]{5}-[A-Z0-9]{5}-[A-Z0-9]{5}-[A-Z0-9]{5})',
        r'([A-Z0-9]{20})',
        r'GOG[:\s]*([A-Z0-9-]{15,25})',
        r'Steam[:\s]*([A-Z0-9-]{15,25})',
        r'GAME KEY[:\s]*([A-Z0-9-]{15,25})',
        r'PRODUCT KEY[:\s]*([A-Z0-9-]{15,25})',
        r'([A-Z0-9]{3,5}-?){3,5}[A-Z0-9]{3,5}',
        r'[A-Z0-9-]{15,25}'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, body, re.IGNORECASE)
        if matches:
            key = matches[0].replace('-', '').upper()
            if 15 <= len(key) <= 25:
                log_message(f"🔑 НАЙДЕН КЛЮЧ: {key} (длина: {len(key)})")
                return key
    log_message("❌ Ключ не найден в письме")
    return None

def check_incoming_keys():
    log_message("🔍 НАЧАТА ПРОВЕРКА IMAP (подключение к почте...)")
    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(IMAP_EMAIL, IMAP_PASSWORD)
        mail.select('inbox')
        
        status, messages = mail.search(None, '(UNSEEN)')
        if status == 'OK':
            email_ids = messages[0].split()[-5:]
            
            for email_id in email_ids:
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                subject = decode_header(msg['Subject'])[0][0]
                if isinstance(subject, bytes):
                    subject = subject.decode(errors='ignore')
                
                if any(kw in subject.lower() for kw in KEYWORDS):
                    log_message(f"📧 Обработка письма: {subject[:50]}...")
                    
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == 'text/plain':
                                body = part.get_payload(decode=True).decode(errors='ignore')
                                break
                    else:
                        body = msg.get_payload(decode=True).decode(errors='ignore')
                    
                    key = extract_key_from_email(body)
                    if key:
                        for order_id, order in list(orders.items()):
                            if order['status'] == 'paid' and not order.get('key'):
                                if send_key_to_buyer(order['email'], key):
                                    orders[order_id]['key'] = key
                                    orders[order_id]['status'] = 'delivered'
                                    save_orders()
                                    log_message(f"✅ АВТООТПРАВКА {order['email']}: {key}")
                                break
        
        mail.close()
        mail.logout()
        log_message("✅ ✅ ПРОВЕРКА IMAP ЗАВЕРШЕНА УСПЕШНО!")
    except Exception as e:
        log_message(f"❌ IMAP ошибка: {str(e)[:100]}")

def send_key_to_buyer(buyer_email, key):
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_EMAIL
        msg['To'] = buyer_email
        msg['Subject'] = '🎮 Cyberpunk 2077 — Ваш ключ доставлен!'
        
        body = f"""🔑 CYBERPUNK 2077 КЛЮЧ АКТИВАЦИИ:

{key}

✅ Скопируйте ТОЛЬКО текст ключа (без пробелов)!
✅ Активируйте в Steam или GOG!
⏰ Доставлено: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}

Спасибо за покупку! 🚀"""
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        log_message(f"📤 Ключ отправлен: {buyer_email}")
        return True
    except Exception as e:
        log_message(f"❌ SMTP ошибка: {str(e)[:100]}")
        return False

def monitor_loop():
    log_message("🚀 Мониторинг ключей запущен (КАЖДЫЕ 3 СЕКУНДЫ ⚡)")
    while True:
        try:
            check_incoming_keys()
            time.sleep(3)
        except Exception as e:
            log_message(f"❌ Мониторинг: {e}")
            time.sleep(3)

if __name__ == '__main__':
    log_message("🚀 CYBERPUNK BOT v2.4 (ИСПРАВЛЕНЫ РОУТЫ /logs /orders)")
    log_message(f"📧 Почта: {SMTP_EMAIL}")
    log_message(f"🔑 Словарь ключей: {len(KEYWORDS)} слов")
    log_message("⚡ Мониторинг почты: каждые 3 секунды")
    log_message("📊 Логи: автообновление каждые 3 сек")
    log_message("✅ ИЩИТЕ: 'ПРОВЕРКА IMAP ЗАВЕРШЕНА УСПЕШНО!'")
    log_message("❤️ Render: keep-alive каждые 14 мин")
    
    Thread(target=monitor_loop, daemon=True).start()
    Thread(target=keep_alive, daemon=True).start()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
