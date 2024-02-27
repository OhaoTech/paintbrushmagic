import os, dotenv
import gradio as gr

dotenv.load_dotenv("../../.env")
STRIPE_DOMAIN = os.getenv("STRIPE_DOMAIN")
def open_checkout():
    return "Redirecting to checkout..."

# Replace 'open_checkout' with a JavaScript function for redirection if needed



with gr.Blocks() as demo:
    pay_btn = gr.Button("Pay", link= STRIPE_DOMAIN + "/create-checkout-session")
    pay_btn.click(open_checkout)

demo.launch(share=True)
