import json
import platform
import uuid
from datetime import datetime
from urllib.parse import unquote

import requests
import stripe
from flask import Flask, request, jsonify, redirect, Response
from flask_cors import CORS
import sqlite3
import os
import dotenv
from snowflake import SnowflakeGenerator

dotenv.load_dotenv("../../.env")

prompt_free_times = os.getenv("PROMPT_FREE_TIMES")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
IMAGE_SERVER_DOMAIN = os.getenv("IMAGE_SERVER_DOMAIN")
HOST_IP = os.getenv("HOST_IP")
MODE = os.getenv('MODE', 'server')

if MODE == 'local':
    IMAGE_SERVER_DOMAIN = "http://127.0.0.1:5000"
    HOST_IP = '127.0.0.1'
    # Any other configurations that need to be set for local mode

stripe.api_key = os.getenv("STRIPE_API_KEY")
# If you are testing your webhook locally with the Stripe CLI you
# can find the endpoint's secret by running `stripe listen`
# Otherwise, find your endpoint's secret in your webhook settings in the Developer Dashboard
endpoint_key = os.getenv("STRIPE_ENDPOINT_KEY")
app = Flask(__name__,
            static_url_path='',
            static_folder='public')
CORS(app)
# app.secret_key = FLASK_SECRET_KEY

# Database setup
PROMPT_DATABASE_FILE = 'user_prompts.db'
IMAGE_URL_DATABASE_FILE = 'image_url.db'
ORDER_DATABASE_FILE = 'orders.db'
gen = SnowflakeGenerator(42)

with open("../../stripe_webhook_white_ip.json", "r") as file:
    data = json.load(file)

webhook_ips = data["WEBHOOKS"]


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
                local_url varchar(500),
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
                id BIGINT PRIMARY KEY,
                image_url TEXT NOT NULL,
                color TEXT NOT NULL,
                size TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                address TEXT NOT NULL,
                payment_status INTEGER NOT NULL DEFAULT 0,
                create_date datetime,
                pay_date datetime,
                country TEXT NOT NULL, 
                first_name TEXT NOT NULL, 
                last_name TEXT NOT NULL, 
                phone_code TEXT NOT NULL, 
                phone_number INTEGER NOT NULL, 
                zip_code TEXT NOT NULL
            )
        """)
    conn.execute("""
                CREATE TABLE IF NOT EXISTS canvas_order (
                    id BIGINT PRIMARY KEY,
                    image_url TEXT NOT NULL,
                    size TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    address TEXT NOT NULL,
                    payment_status INTEGER NOT NULL DEFAULT 0,
                    create_date datetime,
                    pay_date datetime,
                    country TEXT NOT NULL, 
                    first_name TEXT NOT NULL, 
                    last_name TEXT NOT NULL, 
                    phone_code TEXT NOT NULL, 
                    phone_number INTEGER NOT NULL, 
                    zip_code TEXT NOT NULL
                )
            """)
    conn.execute("""
                CREATE TABLE IF NOT EXISTS poster_order (
                    id BIGINT PRIMARY KEY,
                    image_url TEXT NOT NULL,
                    size TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    address TEXT NOT NULL,
                    payment_status INTEGER NOT NULL DEFAULT 0,
                    create_date datetime,
                    pay_date datetime,
                    country TEXT NOT NULL, 
                    first_name TEXT NOT NULL, 
                    last_name TEXT NOT NULL, 
                    phone_code TEXT NOT NULL, 
                    phone_number INTEGER NOT NULL, 
                    zip_code TEXT NOT NULL
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
    local_url = write_file(url)
    conn = get_image_db_connection()
    conn.execute("""
                INSERT INTO image_url
                (url, local_url, prompts, style, ratio)
                VALUES (?, ?, ?, ?, ?)
            """, (url, local_url, prompt, style, ratio))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'local_url': local_url})


def write_file(url):
    img_binary_data = requests.get(url).content
    file_dir = generate_file_dir()
    os.makedirs(file_dir, exist_ok=True)
    filename = str(uuid.uuid4()) + '.png'
    with open(file_dir + filename, 'wb') as f:
        f.write(img_binary_data)
    return file_dir + filename


def generate_file_dir():
    system = platform.system()
    now = datetime.now()
    if system == "Windows":
        file_dir = f"public/data/img/{now.year}{now.month}{now.day}/"
    elif system == "Linux":
        file_dir = f"public/data/img/{now.year}{now.month}{now.day}/"
    else:
        raise Exception
    return file_dir


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
    order = conn.execute('SELECT image_url, color, size, payment_status FROM clothe_order WHERE id = ?',
                         (order_id,)).fetchone()
    conn.close()

    if order is None:
        # TODO: if order doesn't exist
        pass
    else:
        image_url, color, size, payment_status = order
        return jsonify({"status": "success", "image_url": image_url, "color": color, "size": size,
                        "payment_status": payment_status})


@app.route('/generate_order', methods=['POST'])
def generate_order():
    data = request.get_json()
    image_url = data['image_url']
    kind = data['kind']
    size = data['size']
    quantity = data['quantity']
    address = data['address']
    country = data['country']
    first_name = data['first_name']
    last_name = data['last_name']
    phone_code = data['phone_code']
    phone_number = data['phone_number']
    zip_code = data['zip_code']

    # if get database last insert id maybe occur concurrent problem, so use snowflake generate order id
    order_id = next(gen)
    conn = get_db_connection(ORDER_DATABASE_FILE)
    if kind == 'hoodie':
        color = data['color']
        conn.execute(
            'INSERT INTO clothe_order (id, image_url, color, size, quantity, address, create_date, country, first_name, last_name, phone_code, phone_number, zip_code) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (order_id, image_url, color, size, quantity, address, datetime.now(), country, first_name, last_name, phone_code, phone_number, zip_code))
        conn.commit()
    elif kind == 'canvas':
        conn.execute(
            'INSERT INTO canvas_order (id, image_url, size, quantity, address, create_date, country, first_name, last_name, phone_code, phone_number, zip_code) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (order_id, image_url, size, quantity, address, datetime.now(), country, first_name, last_name, phone_code, phone_number, zip_code))
        conn.commit()
    elif kind == 'poster':
        conn.execute(
            'INSERT INTO poster_order (id, image_url, size, quantity, address, create_date, country, first_name, last_name, phone_code, phone_number, zip_code) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (order_id, image_url, size, quantity, address, datetime.now(), country, first_name, last_name, phone_code, phone_number, zip_code))
        conn.commit()
    else:
        conn.close()
        return {"status": "error", "message": "There is no kind of order to " + kind}

    conn.close()
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


def idempotent_Order(order_id, kind):
    conn = get_db_connection(ORDER_DATABASE_FILE)
    if kind == 'clothe':
        order = conn.execute('select * from clothe_order WHERE id = ?', (order_id,)).fetchone()
    elif kind == 'canvas':
        order = conn.execute('select * from canvas_order WHERE id = ?', (order_id,)).fetchone()
    elif kind == 'poster':
        order = conn.execute('select * from poster_order WHERE id = ?',  (order_id,)).fetchone()
    else:
        raise Exception
    return order['payment_status'] == 0

def update_order_status(order_id, kind):
    conn = get_db_connection(ORDER_DATABASE_FILE)
    if kind == 'clothe':
        conn.execute('UPDATE clothe_order SET payment_status = ?, pay_date = ? WHERE id = ?', (2, datetime.now(), order_id))
    elif kind == 'canvas':
        conn.execute('UPDATE canvas_order SET payment_status = ?, pay_date = ? WHERE id = ?', (2, datetime.now(), order_id))
    elif kind == 'poster':
        conn.execute('UPDATE poster_order SET payment_status = ?, pay_date = ? WHERE id = ?', (2, datetime.now(), order_id))
    else:
        raise Exception
    conn.commit()


@app.route('/webhook', methods=['POST'])
def webhook():
    # first we need verify the ip, sure it in  stripe provide webhook ips
    ip = request.remote_addr
    if ip is None:
        return jsonify({"status": "success"})
    if ip not in webhook_ips:
        return jsonify({"status": "success"})

    payload = request.data
    sig_header = request.headers['Stripe-Signature']
    # second we need verify Signature
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_key
        )
    except ValueError as e:
        print('Error parsing payload: {}'.format(str(e)))
        return '', 400
    except stripe.error.SignatureVerificationError as e:
        print('Error verifying webhook signature: {}'.format(str(e)))
        return '', 400

    data = request.get_json()
    if event.type == 'checkout.session.completed':
        obj = data['data']['object']
        metadata = obj['metadata']
        order_id = metadata['order_id']
        kind = metadata['kind']
        if not idempotent_Order(order_id, kind):
            return 'duplicate message', 400
        update_order_status(order_id, kind)
        # TODO notify admin to send product

    return jsonify({"status": "success"})


def generate_checkout_item(kind, quantity=1, currency='usd', price=999):
    item = {
        'price_data': {
            'currency': currency,
            'product_data': {
                'name': kind,
            },
            'unit_amount': price,
        },
        'quantity': quantity,
    }
    return item

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        data = request.get_json()
        kind = data['kind']
        quantity = data['quantity']
        order_id = data['order_id']

        # TODO: customer buy multi products
        items = []
        item = generate_checkout_item(kind=kind, quantity=quantity)
        items.append(item)

        checkout_session = stripe.checkout.Session.create(
            line_items=items,
            mode='payment',
            metadata={
                'order_id': order_id,
                'kind': kind
            },
            success_url=IMAGE_SERVER_DOMAIN + '/success.html',
            cancel_url=IMAGE_SERVER_DOMAIN + '/cancel.html',
        )
        return {'status': 'success', 'url': checkout_session.url}
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/download-image', methods=['POST'])
def download_image():
    image_url = request.get_json()['imageUrl']
    img_binary_data = requests.get(image_url).content
    return Response(img_binary_data, mimetype='image/png')

from flask import send_from_directory
@app.route('/public/<path:filename>')
def serve_public_file(filename):
    return send_from_directory('public', filename)

if __name__ == '__main__':
    app.run(host=HOST_IP, debug=False, port=5000)
