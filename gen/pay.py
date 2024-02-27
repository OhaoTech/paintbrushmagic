import gradio as gr

def open_checkout():
    return "Redirecting to checkout..."

# Replace 'open_checkout' with a JavaScript function for redirection if needed


with gr.Blocks() as demo:
    pay_btn = gr.Button("Pay", link="http://localhost:4242/create-checkout-session")
    pay_btn.click(open_checkout)

demo.launch(share=True)
