from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
import os
import json
import sys
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# ── Gemini AI (new google-genai package) ──
try:
    from google import genai as genai_client
    from google.genai import types as genai_types
    GEMINI_AVAILABLE = True
except ImportError:
    try:
        import google.generativeai as genai
        GEMINI_AVAILABLE = True
        _use_old_sdk = True
    except ImportError:
        GEMINI_AVAILABLE = False
        print("[AI] Install: pip install google-genai")

app = Flask(__name__)
CORS(app)
app.secret_key = "secret123"

# ================================================================
#Auto setup For DB
# ================================================================
CONFIG_FILE   = 'db_config.json'
PRODUCTS_FILE = 'products.json'
PRICES_FILE   = 'market_prices.json'

DB_NAME = 'bakery_market'   # database name

app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ----------------------------------------------------------------
def load_config():
    """Load DB password from db_config.json"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {}

def save_config(data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# ----------------------------------------------------------------
def try_connect(password, database=None):
    """Try connecting with given password. Returns connection or None."""
    try:
        kwargs = dict(host='localhost', user='root', password=password,
                      cursorclass=pymysql.cursors.Cursor, connect_timeout=4)
        if database:
            kwargs['database'] = database
        return pymysql.connect(**kwargs)
    except Exception:
        return None

def find_password():
    """
    1. Try saved password from db_config.json
    2. Try common passwords
    Returns (connection_without_db, password) or (None, None)
    """
    cfg = load_config()
    saved_pw = cfg.get('password')

    candidates = []
    if saved_pw is not None:
        candidates.append(saved_pw)          # saved one first
    candidates += ['', 'root', 'root123', '1234', 'admin',
                   'mysql', 'password', 'toor', 'xampp', '12345']

    for pw in candidates:
        conn = try_connect(pw)
        if conn:
            print(f"[DB] Connected with password: {'(empty)' if pw == '' else repr(pw)}")
            save_config({'password': pw})    # save for next run
            return conn, pw
    return None, None

# ----------------------------------------------------------------
# ----------------------------------------------------------------
# DEFAULT ADMIN CREDENTIALS
# Email   : admin@market.com
# Password: admin123
# Change these after first login from admin panel.
ADMIN_EMAIL    = 'admin@market.com'
ADMIN_PASSWORD = 'admin123'

def _seed_admin(conn):
    """Create the admins table and insert default admin if not exists."""
    cur = conn.cursor()
    cur.execute(f"USE `{DB_NAME}`")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id         INT AUTO_INCREMENT PRIMARY KEY,
            email      VARCHAR(150) UNIQUE NOT NULL,
            password   TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    # Insert default admin only if table empty
    cur.execute("SELECT COUNT(*) FROM admins")
    count = cur.fetchone()[0]
    if count == 0:
        hashed = generate_password_hash(ADMIN_PASSWORD)
        cur.execute("INSERT INTO admins (email, password) VALUES (%s, %s)",
                    (ADMIN_EMAIL, hashed))
        conn.commit()
        print(f"[ADMIN] Default admin created → {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
    cur.close()

# ── Admin auth decorator ──
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('admin_login_page'))
        return f(*args, **kwargs)
    return decorated

def setup_database(conn):
    """
    Auto-create database + all tables if they don't exist.
    Safe to run every startup (uses IF NOT EXISTS).
    """
    cur = conn.cursor()

    # Create database
    cur.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
                f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    cur.execute(f"USE `{DB_NAME}`")

    # users table — drop and recreate if schema is outdated
    cur.execute("SHOW COLUMNS FROM users LIKE 'username'") if True else None
    try:
        cur.execute("SHOW COLUMNS FROM users LIKE 'username'")
        has_username = cur.fetchone()
        if not has_username:
            # Old schema — drop and recreate
            cur.execute("DROP TABLE users")
            print("[DB] Dropped old users table — recreating with new schema")
    except Exception:
        pass  # table doesn't exist yet — will be created below

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         INT AUTO_INCREMENT PRIMARY KEY,
            username   VARCHAR(100) UNIQUE NOT NULL,
            password   TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # orders table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id             INT AUTO_INCREMENT PRIMARY KEY,
            product_name   VARCHAR(150),
            weight         VARCHAR(50),
            quantity       INT,
            payment_method VARCHAR(50)  DEFAULT 'Cash on Delivery',
            customer_name  VARCHAR(100),
            email          VARCHAR(150),
            phone          VARCHAR(20),
            address        TEXT,
            note           TEXT,
            total_price    DECIMAL(10,2),
            order_date     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # contact table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS contact (
            id         INT AUTO_INCREMENT PRIMARY KEY,
            name       VARCHAR(100),
            email      VARCHAR(150),
            phone      VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.commit()
    cur.close()
    print(f"[DB] Database '{DB_NAME}' and tables are ready ✅")

    # ── Seed default admin account (only if table is empty) ──
    _seed_admin(conn)
# ================================================================
#  STARTUP — find password → create DB → connect
# ================================================================
connection   = None
DB_AVAILABLE = False

_base_conn, _found_pw = find_password()

if _base_conn:
    try:
        setup_database(_base_conn)
        # Now connect directly to our database
        connection = try_connect(_found_pw, database=DB_NAME)
        if connection:
            DB_AVAILABLE = True
            print(f"[DB] Ready — connected to '{DB_NAME}' ✅")
        _base_conn.close()
    except Exception as e:
        print(f"[DB] Setup error: {e}")
        DB_AVAILABLE = False
else:
    print("[DB] ❌ Could not connect to MySQL.")
    print("     → Open phpMyAdmin and note your root password.")
    print(f"     → Add it to '{CONFIG_FILE}': {{\"password\": \"YOUR_PASSWORD\"}}")

# ----------------------------------------------------------------
def get_cursor():
    """Return a live cursor, reconnect if dropped."""
    global connection
    if not DB_AVAILABLE or connection is None:
        return None
    try:
        connection.ping(reconnect=True)
        return connection.cursor()
    except Exception:
        try:
            cfg = load_config()
            connection = try_connect(cfg.get('password',''), database=DB_NAME)
            return connection.cursor() if connection else None
        except Exception:
            return None

# ================================================================
#  JSON HELPERS
# ================================================================
def load_products():
    if os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE) as f:
            return json.load(f)
    return []

def save_products(products):
    with open(PRODUCTS_FILE, 'w') as f:
        json.dump(products, f, indent=2)

def load_prices():
    if os.path.exists(PRICES_FILE):
        with open(PRICES_FILE) as f:
            return json.load(f)
    return {}

def save_prices(prices):
    with open(PRICES_FILE, 'w') as f:
        json.dump(prices, f, indent=2)

# ================================================================
#  ROUTES — PAGES
# ================================================================

@app.route('/')
def index():
    return render_template('index.html',
                           products=load_products(),
                           user=session.get('user'))

@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    try:
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            return render_template('login.html', error="Username and password are required.")
        if len(password) < 4:
            return render_template('login.html', error="Password must be at least 4 characters.")

        hashed = generate_password_hash(password)
        cur = get_cursor()
        if cur is None:
            return render_template('login.html', error="Database not available.")
        cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed))
        connection.commit()
        cur.close()
        return render_template('login.html', success="Account created! Please sign in.")
    except pymysql.err.IntegrityError:
        return render_template('login.html', error="Username already taken. Try another.")
    except Exception as e:
        return render_template('login.html', error=f"Error: {e}")

@app.route('/login', methods=['POST'])
def login():
    try:
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            return render_template('login.html', error="Username and password are required.")

        cur = get_cursor()
        if cur is None:
            return render_template('login.html', error="Database not available.")
        cur.execute("SELECT id, username, password FROM users WHERE username=%s", (username,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user[2], password):
            session['user']    = user[1]
            session['user_id'] = user[0]
            return render_template('index.html',
                                   products=load_products(),
                                   user=session.get('user'),
                                   login_success=True)
        return render_template('login.html', error="Invalid username or password.")
    except Exception as e:
        return render_template('login.html', error=f"Error: {e}")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

# ── Category pages ──
@app.route('/vegetables')
def vegetables():
    return render_template('vegetables.html', prices=load_prices(), active_page='vegetables')

@app.route('/seeds')
@app.route('/seed')
def seeds():
    return render_template('seed.html', prices=load_prices(), active_page='seeds')

@app.route('/nuts')
def nuts():
    return render_template('nuts.html', prices=load_prices(), active_page='nuts')

@app.route('/fragrant')
def fragrant():
    return render_template('fragrant.html', prices=load_prices(), active_page='fragrant')

@app.route('/spice')
def spice():
    return render_template('spice.html', prices=load_prices(), active_page='spice')

@app.route('/oil')
def oil():
    return render_template('oil.html', prices=load_prices(), active_page='oil')

@app.route('/groceries')
def groceries():
    return render_template('groceries.html', prices=load_prices(), active_page='groceries')

@app.route('/order')
def order():
    return render_template('order.html')

@app.route('/cart')
def cart():
    return render_template('addtocart.html')

@app.route('/history')
def history():
    return render_template('history.html')

# ================================================================
#  ORDER SUCCESS PAGE
# ================================================================
@app.route('/order_success')
def order_success():
    return render_template('order_success.html')

# ================================================================
#  ADMIN AUTH
# ================================================================
@app.route('/admin/login', methods=['GET'])
def admin_login_page():
    if session.get('admin'):
        return redirect(url_for('admin'))
    return render_template('admin_login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login():
    email    = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    try:
        cur = get_cursor()
        if cur is None:
            # DB offline — check against hardcoded default
            if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
                session['admin'] = email
                return redirect(url_for('admin'))
            return render_template('admin_login.html', error="Invalid credentials.")

        cur.execute("SELECT password FROM admins WHERE email=%s", (email,))
        row = cur.fetchone()
        cur.close()

        if row and check_password_hash(row[0], password):
            session['admin'] = email
            return redirect(url_for('admin'))
        return render_template('admin_login.html', error="Invalid email or password.")
    except Exception as e:
        return render_template('admin_login.html', error=f"Error: {e}")

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login_page'))

# ================================================================
#  PLACE ORDER
# ================================================================
@app.route('/place_order', methods=['POST'])
def place_order():
    try:
        data = request.json
        cur  = get_cursor()
        if cur is None:
            # DB இல்லாமலும் frontend-ல order confirm ஆகும்
            return jsonify({"status": "success", "note": "saved locally"})
        cur.execute("""
            INSERT INTO orders
              (product_name, weight, quantity, payment_method,
               customer_name, email, phone, address, note, total_price)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data.get('product',  ''),
            data.get('weight',   ''),
            data.get('quantity', 1),
            data.get('payment',  'Cash on Delivery'),
            data.get('name',     ''),
            data.get('email',    ''),
            data.get('phone',    ''),
            data.get('address',  ''),
            data.get('note',     ''),
            data.get('price',    0),
        ))
        connection.commit()
        cur.close()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ================================================================
#  CONTACT
# ================================================================
@app.route('/contact', methods=['POST'])
def contact():
    try:
        cur = get_cursor()
        if cur:
            cur.execute("INSERT INTO contact (name,email,phone) VALUES (%s,%s,%s)",
                        (request.form['name'],
                         request.form['email'],
                         request.form['phone']))
            connection.commit()
            cur.close()
    except Exception as e:
        print(f"[Contact] Error: {e}")
    return redirect(url_for('index'))

# ================================================================
#  ADMIN
# ================================================================
@app.route('/admin')
@admin_required
def admin():
    # Get order stats from DB
    stats = {'total_orders': 0, 'total_revenue': 0}
    try:
        cur = get_cursor()
        if cur:
            cur.execute("SELECT COUNT(*), COALESCE(SUM(total_price),0) FROM orders")
            row = cur.fetchone()
            stats['total_orders']   = row[0] or 0
            stats['total_revenue']  = float(row[1] or 0)
            cur.close()
    except Exception:
        pass

    # Get recent orders
    recent_orders = []
    try:
        cur = get_cursor()
        if cur:
            cur.execute("""
                SELECT customer_name, product_name, total_price, order_date
                FROM orders ORDER BY order_date DESC LIMIT 10
            """)
            recent_orders = cur.fetchall()
            cur.close()
    except Exception:
        pass

    return render_template('admin.html',
                           products=load_products(),
                           prices=load_prices(),
                           stats=stats,
                           recent_orders=recent_orders,
                           db_status=DB_AVAILABLE)

# ── Add product ──
@app.route('/admin/add_product', methods=['POST'])
@admin_required
def add_product():
    name  = request.form.get('prodName', '').strip()
    price = request.form.get('prodPrice', '').strip()
    image = request.files.get('prodImage')

    # Validate name
    if not name:
        return redirect(url_for('admin') + '?err=Product+name+is+required')
    if name.isdigit():
        return redirect(url_for('admin') + '?err=Product+name+cannot+be+only+numbers')

    # Validate price
    try:
        float(price)
    except (ValueError, TypeError):
        return redirect(url_for('admin') + '?err=Price+must+be+a+valid+number')

    products = load_products()

    # Duplicate check — case-insensitive
    if any(p['name'].strip().lower() == name.lower() for p in products):
        return redirect(url_for('admin') + '?err=Product+already+exists:+"' + name + '"')

    image_filename = ''
    if image and image.filename:
        image_filename = image.filename
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

    products.append({'name': name, 'price': price, 'image': image_filename})
    save_products(products)
    return redirect(url_for('admin') + '?success=Product+"' + name + '"+added+successfully')

# ── Edit product ──
@app.route('/admin/edit_product', methods=['POST'])
@admin_required
def edit_product():
    idx   = int(request.form['prodIndex'])
    image = request.files.get('prodImage')
    products = load_products()
    if 0 <= idx < len(products):
        products[idx]['name']  = request.form['prodName'].strip()
        products[idx]['price'] = request.form['prodPrice'].strip()
        if image and image.filename:
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image.filename))
            products[idx]['image'] = image.filename
    save_products(products)
    return redirect(url_for('admin'))

# ── Delete product ──
@app.route('/admin/delete_product', methods=['POST'])
@admin_required
def delete_product():
    idx = int(request.form['prodIndex'])
    products = load_products()
    if 0 <= idx < len(products):
        products.pop(idx)
    save_products(products)
    return redirect(url_for('admin'))

# ── Update daily price ──
@app.route('/admin/update_price', methods=['POST'])
@admin_required
def update_price():
    data   = request.json
    name   = data.get('name', '').strip()
    price  = data.get('price', '')
    if not name:
        return jsonify({"status": "error", "msg": "no name"}), 400
    prices = load_prices()
    if price == '__DELETE__':
        prices.pop(name, None)   # remove from price list
    else:
        prices[name] = price
    save_prices(prices)
    return jsonify({"status": "ok"})

# ── API: all prices ──
@app.route('/api/prices')
def api_prices():
    return jsonify(load_prices())

# ── API: Save Gemini key (from admin panel) ──
@app.route('/admin/save_gemini_key', methods=['POST'])
@admin_required
def save_gemini_key():
    global _gemini_client, GEMINI_API_KEY
    key = request.json.get('key', '').strip()
    if not key:
        return jsonify({"status": "error", "msg": "Empty key"}), 400
    # Save to db_config.json
    cfg = load_config()
    cfg['gemini_key'] = key
    save_config(cfg)
    # Reset client so it reconnects with new key
    _gemini_client  = None
    GEMINI_API_KEY  = key
    # Test the key
    client = get_gemini_client()
    if client:
        try:
            # New SDK: pass simple string
            test_resp = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents="Say OK"
            )
            _ = test_resp.text
            return jsonify({"status": "ok", "msg": "Gemini API key saved and verified!"})
        except Exception as e:
            return jsonify({"status": "error", "msg": f"Key saved but test failed: {e}"}), 400
    return jsonify({"status": "error", "msg": "Could not initialize Gemini client."}), 400

# ── API: Get Gemini key status ──
@app.route('/api/ai_status')
def ai_status():
    key = get_gemini_api_key()
    return jsonify({
        "configured": bool(key),
        "key_preview": f"{key[:8]}...{key[-4:]}" if key and len(key) > 12 else None
    })
@app.route('/api/db_status')
def db_status():
    return jsonify({"connected": DB_AVAILABLE, "database": DB_NAME})

# ================================================================
#  AI — GEMINI INTEGRATION
# ================================================================

# ── Gemini API key — db_config.json-ல store ஆகும் ──
# முதல் முறை: db_config.json-ல { "gemini_key": "YOUR_KEY" } போடு
# அல்லது admin panel-ல போடு → automatically save ஆகும்
def get_gemini_api_key():
    """Load Gemini key from db_config.json or environment variable."""
    # 1. Environment variable (most secure for production)
    env_key = os.environ.get('GEMINI_API_KEY', '')
    if env_key and env_key != 'YOUR_GEMINI_API_KEY_HERE':
        return env_key
    # 2. db_config.json
    cfg = load_config()
    stored_key = cfg.get('gemini_key', '')
    if stored_key and stored_key != 'YOUR_GEMINI_API_KEY_HERE':
        return stored_key
    return None

GEMINI_API_KEY = get_gemini_api_key()  # loaded at startup

_gemini_client = None

def get_gemini_client():
    global _gemini_client, GEMINI_API_KEY
    if not GEMINI_AVAILABLE:
        return None
    # Reload key every time in case admin just saved it
    current_key = get_gemini_api_key()
    if not current_key:
        return None
    if _gemini_client is None or GEMINI_API_KEY != current_key:
        GEMINI_API_KEY = current_key
        try:
            _gemini_client = genai_client.Client(api_key=current_key)
            print("[AI] Gemini client ready ✅")
        except Exception as e:
            print(f"[AI] Gemini init error: {e}")
    return _gemini_client

# keep alias
def get_gemini_model():
    return get_gemini_client()

# Market context for AI — tells Gemini about our shop
MARKET_CONTEXT = """
You are a helpful AI assistant for "Market" — a fresh produce online shop in Tamil Nadu, India.
The shop sells: Vegetables (Carrot, Cucumber, Onion, Cauliflower, Mint Leaves, Coriander Leaves),
Seeds (Sunflower, Chia, Fennel, Fenugreek, Coriander, Mustard, Pumpkin, Sesame, Flax),
Nuts (Hazelnut, Pista, Walnuts, Dates, Groundnut),
Oils (Sunflower Oil, Groundnut Oil, Coconut Oil, Olive Oil, Sesame Oil, Mustard Oil),
Fragrant items, Mixed Spice Powders, Eggs, Chicken, Mutton.
Payment: Cash on Delivery only.
Location: Tirunelveli, TamilNadu.
Always respond in English. Be helpful, concise, and friendly.
If asked about prices, mention that prices are updated daily by the admin.
If asked to compare prices, give honest advice about value for money.
"""

# ── Chatbot endpoint ──
@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data    = request.json
        message = data.get('message', '').strip()
        history = data.get('history', [])

        if not message:
            return jsonify({"error": "Empty message"}), 400

        client = get_gemini_client()
        if client is None:
            return jsonify({
                "reply": "AI assistant is not configured yet. Please add your Gemini API key in Admin → AI Settings.",
                "ai_ready": False
            })

        # Build prompt as plain string (works reliably with google-genai 2.x)
        if not history:
            full_prompt = MARKET_CONTEXT + "\n\nUser: " + message
        else:
            # Build conversation as readable text
            conv = MARKET_CONTEXT + "\n\nConversation so far:\n"
            for h in history[-6:]:
                role = "User" if h.get("role") == "user" else "Assistant"
                conv += f"{role}: {h.get('text','')}\n"
            full_prompt = conv + f"User: {message}\nAssistant:"

        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=full_prompt
        )
        reply = response.text.strip()

        return jsonify({"reply": reply, "ai_ready": True})

    except Exception as e:
        print(f"[AI Chat Error] {e}")
        return jsonify({
            "reply": f"AI error: {str(e)}",
            "ai_ready": False
        }), 500

# ── Price comparison endpoint ──
@app.route('/api/price_compare', methods=['POST'])
def price_compare():
    try:
        data        = request.json
        product     = data.get('product', '').strip()
        our_price   = data.get('our_price', '')
        category    = data.get('category', '')

        client = get_gemini_client()
        if client is None:
            return jsonify({"error": "AI not configured", "ai_ready": False,
                            "suggestion": "⚠️ Add your Gemini API key in app.py (GEMINI_API_KEY variable) to enable AI price comparison."})

        prices = load_prices()
        price_context = json.dumps(prices, indent=2) if prices else "No prices set yet."

        prompt = f"""
{MARKET_CONTEXT}

Our current market prices (set by admin today):
{price_context}

A customer wants to buy: {product} (Category: {category})
Our price: ₹{our_price}

Please compare this price with typical market rates in Tamil Nadu for this product.
Give a brief, honest comparison (2-3 sentences max) in English:
1. Is our price competitive / good value?
2. Typical price range in local markets
3. One sentence recommendation: should they buy here or look elsewhere?

Be specific with numbers. Keep it under 60 words.
"""

        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt
        )
        suggestion = response.text

        return jsonify({"suggestion": suggestion, "ai_ready": True, "product": product})

    except Exception as e:
        return jsonify({"error": str(e), "suggestion": "Unable to get price comparison right now."}), 500

# ── Price compare page ──
@app.route('/compare')
def compare():
    prices = load_prices()
    return render_template('compare.html', prices=prices)

# ================================================================
#  RUN
# ================================================================
if __name__ == "__main__":
    app.run(debug=True)
