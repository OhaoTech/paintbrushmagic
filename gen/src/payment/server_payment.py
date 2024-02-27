#! /usr/bin/env python3.6

"""
server.py
Stripe Sample.
Python 3.6 or newer required.
"""
import os, dotenv
from flask import Flask, redirect, request
import stripe

dotenv.load_dotenv("../../.env")
# This is a public sample test API key.
# Don’t submit any personally identifiable information in requests made with this key.
# Sign in to see your own test API key embedded in code samples.
stripe.api_key = os.getenv("STRIPE_API_KEY")

app = Flask(__name__,
            static_url_path='',
            static_folder='public')

STRIPE_DOMAIN = os.getenv("STRIPE_DOMAIN")
pr_123 = 123
@app.route('/create-checkout-session', methods=['GET'])
def create_checkout_session():
    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                    'name': 'T-shirt',
                    },
                    'unit_amount': 60,
                },
                'quantity': 1,
                }],

            mode='payment',
            success_url=STRIPE_DOMAIN + '/success.html',
            cancel_url=STRIPE_DOMAIN + '/cancel.html',
        )
    except Exception as e:
        return str(e)

    return redirect(checkout_session.url, code=303)

if __name__ == '__main__':
    app.run(port=4242)