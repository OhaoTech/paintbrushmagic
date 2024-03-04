import stripe
from flask import Flask, request, jsonify, redirect
import sqlite3
import os
import dotenv
dotenv.load_dotenv("../../.env")

prompt_free_times = os.getenv("PROMPT_FREE_TIMES")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
IMAGE_SERVER_DOMAIN = os.getenv("IMAGE_SERVER_DOMAIN")

stripe.api_key = os.getenv("STRIPE_API_KEY")

app = Flask(__name__,
            static_url_path='',
            static_folder='public')
app.secret_key = FLASK_SECRET_KEY

# Database setup
PROMPT_DATABASE_FILE = 'user_prompts.db'
IMAGE_URL_DATABASE_FILE = 'image_url.db'
ORDER_DATABASE_FILE = 'orders.db'

def get_db_connection(database_file):
    conn = sqlite3.connect(database_file)
    conn.row_factory = sqlite3.Row
    return conn
def get_image_db_connection():
    return get_db_connection(IMAGE_URL_DATABASE_FILE)

def get_prompt_db_connection():
    return get_db_connection(PROMPT_DATABASE_FILE)

def get_order_db_connection():
    return get_db_connection(ORDER_DATABASE_FILE)

def init_db():
    # create user remaining prompts database
    conn = get_prompt_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT NOT NULL,
            prompts_left INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    # create image url database
    conn = get_image_db_connection()
    conn.execute("""
            CREATE TABLE IF NOT EXISTS image_url (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                prompts TEXT NOT NULL,
                style TEXT NOT NULL,
                ratio TEXT NOT NULL
            )
        """)
    conn.commit()
    conn.close()
    # create order database
    conn = get_order_db_connection()
    conn.execute("""
            CREATE TABLE IF NOT EXISTS clothe_order (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_url TEXT NOT NULL,
                color TEXT NOT NULL,
                size TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                address TEXT NOT NULL,
                payment_status INTEGER NOT NULL DEFAULT 0
            )
        """)
    conn.execute("""
                CREATE TABLE IF NOT EXISTS canvas_order (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_url TEXT NOT NULL,
                    size TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    address TEXT NOT NULL,
                    payment_status INTEGER NOT NULL DEFAULT 0
                )
            """)
    conn.execute("""
                CREATE TABLE IF NOT EXISTS post_order (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_url TEXT NOT NULL,
                    size TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    address TEXT NOT NULL,
                    payment_status INTEGER NOT NULL DEFAULT 0
                )
            """)
    conn.commit()
    conn.close()

@app.before_request
def initialize():
    # Initialize the database table
    init_db()

# add image generation record to database
@app.route('/add_image_record', methods=['POST'])
def add_image_generation_record():
    data = request.get_json()
    url = data['url']
    prompt = data['prompt']
    style = data['style']
    ratio = data['ratio']

    conn = get_image_db_connection()
    conn.execute("""
                INSERT INTO image_url 
                (url, prompts, style, ratio) 
                VALUES (?, ?, ?, ?)
            """, (url, prompt, style, ratio))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/get_prompts', methods=['GET'])
def get_prompts():
    user_ip = request.remote_addr
    conn = get_prompt_db_connection()
    user = conn.execute('SELECT prompts_left FROM user_prompts WHERE ip_address = ?', (user_ip,)).fetchone()
    conn.close()

    if user:
        prompts_left = user['prompts_left']
    else:
        prompts_left = prompt_free_times  # Default number of prompts for new users
        conn = get_prompt_db_connection()
        conn.execute('INSERT INTO user_prompts (ip_address, prompts_left) VALUES (?, ?)', (user_ip, prompts_left))
        conn.commit()
        conn.close()

    return jsonify({'prompts_left': prompts_left})

@app.route('/update_prompts', methods=['POST'])
def update_prompts():
    user_ip = request.remote_addr
    conn = get_prompt_db_connection()
    conn.execute('UPDATE user_prompts SET prompts_left = prompts_left - 1 WHERE ip_address = ?', (user_ip,))
    conn.commit()
    conn.close()

    return jsonify({'status': 'success'})

@app.route('/add_prompts', methods=['POST'])
def add_prompts():
    user_ip = request.remote_addr
    conn = get_prompt_db_connection()
    conn.execute('UPDATE user_prompts SET prompts_left = 5 WHERE ip_address = ?', (user_ip,))
    conn.commit()
    conn.close()

    return jsonify({'status': 'success'})

@app.route('/create_clothe_order', methods=['POST'])
def create_clothe_order():
    data = request.get_json()
    image_url = data['image_url']
    color = data['color']
    size = data['size']
    conn = get_db_connection()
    conn.execute('INSERT INTO clothe_order (image_url, color, size) VALUES (?, ?, ?)', (image_url, color, size))
    conn.commit()
    conn.close()

    return jsonify({'status': 'success'})

@app.route('/select_clothe_order', methods=['POST'])
def select_order():
    data = request.get_json()
    order_id = data['id']
    conn = get_db_connection()
    order = conn.execute('SELECT image_url, color, size, payment_status FROM clothe_order WHERE id = ?', (order_id,)).fetchone()
    conn.close()

    if order is None:
        # TODO: if order doesn't exist
        pass
    else:
        image_url, color, size, payment_status = order
        return jsonify({"status": "success", "image_url": image_url, "color": color, "size": size, "payment_status": payment_status})
@app.route('/generate_order', methods=['POST'])
def generate_order():
    data = request.get_json()
    image_url = data['image_url']
    kind = data['kind']
    size = data['size']
    quantity = data['quantity']
    address = data['address']

    conn = get_db_connection(ORDER_DATABASE_FILE)
    if kind == 'clothe':
        color = data['color']
        conn.execute('INSERT INTO clothe_order (image_url, color, size, quantity, address) VALUES (?, ?, ?, ?, ?)', (image_url, color, size, quantity, address))
        conn.commit()
    elif kind == 'canvas':
        conn.execute('INSERT INTO canvas_order (image_url, size, quantity, address) VALUES (?, ?, ?, ?)', (image_url, size, quantity, address))
        conn.commit()
    elif kind == 'post':
        conn.execute('INSERT INTO post_order (image_url, size, quantity, address) VALUES (?, ?, ?, ?)',
                     (image_url, size, quantity, address))
        conn.commit()
    else:
        conn.close()
        return {"status": "error", "message": "There is no kind of order to " + kind}

    order_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    return {"status": "success", "order_id": str(order_id), 'kind': kind}

@app.route('/update_clothe_order_payment_status', methods=['POST'])
def update_clothe_order_payment_status():
    data = request.get_json()
    order_id = data['id']
    payment_status = data['payment_status']
    conn = get_db_connection()
    conn.execute('UPDATE clothe_order SET payment_status = ? WHERE id = ?', (payment_status, order_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

def generate_post_checkout_item(name, size, address, currency='usd', price=999, quantity=1):
    item = {
        'price_data': {
            'currency': currency,
            'product_data': {
                'name': name,
                'size': size,
                'address': address
            },
            'unit_amount': price,
        },
        'quantity': quantity,
    }
    return item
def generate_canvas_checkout_item(name, size, address, currency='usd', price=999, quantity=1):
    item = {
        'price_data': {
            'currency': currency,
            'product_data': {
                'name': name,
                'size': size,
                'address': address
            },
            'unit_amount': price,
        },
        'quantity': quantity,
    }
    return item
def generate_clothe_checkout_item(name, color, size, address, quantity=1, currency='usd', price=999):
    item = {
        'price_data': {
            'currency': currency,
            'product_data': {
                'name': name,
                'color': color,
                'size': size,
                'address': address
            },
            'unit_amount': price,
        },
        'quantity': quantity,
    }
    return item

@app.route('/create-clothe-checkout-session', methods=['GET'])
def create_clothe_checkout_session():
    try:
        data = request.get_json()
        name = data['name']
        color = data['color']
        size = data['size']
        address = data['address']
        quantity = data['quantity']

        items = []
        items.append(generate_clothe_checkout_item(name=name, color=color, size=size, address=address, quantity=quantity))

        checkout_session = stripe.checkout.Session.create(
            line_items=items,
            mode='payment',
            success_url=IMAGE_SERVER_DOMAIN + '/success.html',
            cancel_url=IMAGE_SERVER_DOMAIN + '/cancel.html',
        )
    except Exception as e:
        return str(e)

    return redirect(checkout_session.url, code=303)

@app.route('/create-canvas-checkout-session', methods=['GET'])
def create_canvas_checkout_session():
    try:
        data = request.get_json()
        name = data['name']
        size = data['size']
        address = data['address']
        quantity = data['quantity']

        items = []
        items.append(generate_canvas_checkout_item(name=name, size=size, address=address, quantity=quantity))

        checkout_session = stripe.checkout.Session.create(
            line_items=items,
            mode='payment',
            success_url=IMAGE_SERVER_DOMAIN + '/success.html',
            cancel_url=IMAGE_SERVER_DOMAIN + '/cancel.html',
        )
    except Exception as e:
        return str(e)

    return redirect(checkout_session.url, code=303)

@app.route('/create-post-checkout-session', methods=['GET'])
def create_post_checkout_session():
    try:
        data = request.get_json()
        name = data['name']
        size = data['size']
        address = data['address']
        quantity = data['quantity']

        items = []
        items.append(generate_canvas_checkout_item(name=name, size=size, address=address, quantity=quantity))

        checkout_session = stripe.checkout.Session.create(
            line_items=items,
            mode='payment',
            success_url=IMAGE_SERVER_DOMAIN + '/success.html',
            cancel_url=IMAGE_SERVER_DOMAIN + '/cancel.html',
        )
    except Exception as e:
        return str(e)

    return redirect(checkout_session.url, code=303)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
