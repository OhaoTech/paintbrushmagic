from flask import Flask, request, jsonify
import sqlite3
import os
import dotenv
dotenv.load_dotenv() 

prompt_free_times = os.getenv("PROMPT_FREE_TIMES")
app = Flask(__name__)

# Database setup
DATABASE_FILE = 'user_prompts.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT NOT NULL,
            prompts_left INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()

@app.before_request
def initialize():
    # Initialize the database table
    init_db()

@app.route('/get_prompts', methods=['GET'])
def get_prompts():
    user_ip = request.remote_addr
    conn = get_db_connection()
    user = conn.execute('SELECT prompts_left FROM user_prompts WHERE ip_address = ?', (user_ip,)).fetchone()
    conn.close()

    if user:
        prompts_left = user['prompts_left']
    else:
        prompts_left = prompt_free_times  # Default number of prompts for new users
        conn = get_db_connection()
        conn.execute('INSERT INTO user_prompts (ip_address, prompts_left) VALUES (?, ?)', (user_ip, prompts_left))
        conn.commit()
        conn.close()

    return jsonify({'prompts_left': prompts_left})

@app.route('/update_prompts', methods=['POST'])
def update_prompts():
    user_ip = request.remote_addr
    conn = get_db_connection()
    conn.execute('UPDATE user_prompts SET prompts_left = prompts_left - 1 WHERE ip_address = ?', (user_ip,))
    conn.commit()
    conn.close()

    return jsonify({'status': 'success'})

@app.route('/add_prompts', methods=['POST'])
def add_prompts():
    user_ip = request.remote_addr
    conn = get_db_connection()
    conn.execute('UPDATE user_prompts SET prompts_left = 5 WHERE ip_address = ?', (user_ip,))
    conn.commit()
    conn.close()

    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True)
