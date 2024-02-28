from flask import Flask, request, jsonify
import sqlite3
import os
import dotenv
dotenv.load_dotenv("../../.env") 

prompt_free_times = os.getenv("PROMPT_FREE_TIMES")
app = Flask(__name__,
            static_url_path='',
            static_folder='public')

# Database setup
PROMPT_DATABASE_FILE = 'user_prompts.db'
IMAGE_URL_DATABASE_FILE = 'image_url.db'

def get_db_connection(database_file):
    conn = sqlite3.connect(database_file)
    conn.row_factory = sqlite3.Row
    return conn
def get_image_db_connection():
    return get_db_connection(IMAGE_URL_DATABASE_FILE)

def get_prompt_db_connection():
    return get_db_connection(PROMPT_DATABASE_FILE)

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

if __name__ == '__main__':
    app.run(debug=True)
