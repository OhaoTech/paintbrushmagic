import webbrowser

import gradio as gr
from openai import OpenAI
# openai error handling


import requests
import io, os
import dotenv
from PIL import Image
import random
import prompt
import network

# Load the environment variables from the .env file
dotenv.load_dotenv()
IMAGE_SERVER_DOMAIN = os.getenv('IMAGE_SERVER_DOMAIN')
RENDER_SERVER_DOMAIN = os.getenv('RENDER_SERVER_DOMAIN')

# Initialize OpenAI client with your API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
random_prompt = prompt.read_prompt()

# variants about image generation
styles = ["Abstract Expressionism", "Acrylic Painting", "Art Deco", "Baroque", "Charcoal Drawing", "Cubism",
          "Engraving", "Etching", "Expressionism", "Futurism", "Gouache", "Graffiti", "Hyperrealism", "Impressionism",
          "Ink Drawing", "Lithography", "Lowbrow", "Minimalism", "Naive Art", "Neoclassicism", "No Style",
          "Oil Painting", "Op Art", "Photorealism", "Pixel Art", "Pointillism", "Pop Art", "Realism", "Renaissance",
          "Screen Printing", "Street Art", "Surrealism", "Trompe-l'oeil", "Ukiyo-e", "Watercolor",
          "Watercolor Painting", "Woodcut"]
ratios = ["1:1", "4:7", "7:4"]
sizes = ["1024x1024", "1024x1792", "1792x1024"]
qualities = ["standard", "hd"]

# variants about order generation
kind_list = ['clothe', 'canvas', 'post']
clothe_size = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
canvas_size = ['20x25', '30x40', '40x50', '60x80']
post_size = ['A1', 'A2', 'A3']
color_list = ['white', 'red', 'green', 'blue', 'black']


def generate_prompt(prompt, negative_prompt, style):
    if negative_prompt is None or negative_prompt == '':
        pass
    else:
        prompt += "and I don't want {negative_prompt}"
    if style != "No Style":
        prompt += ", please draw the picture in {style} style"

    return prompt


def record_image_and_prompt(prompt, image_url, style, ratio):
    param = {
        'url': image_url,
        'prompt': prompt,
        'style': style,
        'ratio': ratio
    }

    response = requests.post(IMAGE_SERVER_DOMAIN + '/add_image_record', json=param)
    if response.status_code != 200:
        # TODO: when image generation record save failed
        pass
    else:
        # TODO: when image generation record save successfully
        pass


def generate_image(prompt, negative_prompt, style, ratio, quality):
    # Check the number of prompts left by making a request to the Flask backend
    response = requests.get(IMAGE_SERVER_DOMAIN + '/get_prompts')
    if response.status_code != 200:
        return None, "Error retrieving prompt count."
    num_prompts = response.json()['prompts_left']

    if num_prompts > 0:
        try:
            if ratio == "1:1":
                size = sizes[0]
            elif ratio == "4:7":
                size = sizes[1]
            elif ratio == "7:4":
                size = sizes[2]
            else:
                return None, "Wrong ratio", ""

            # Add the style to the prompt
            full_prompt = generate_prompt(prompt, negative_prompt, style)
            # Call the OpenAI API
            response = client.images.generate(
                model="dall-e-3",
                prompt=full_prompt,
                size=size,
                quality=quality,
                n=1,
            )
            # The response should contain the URL to the generated image
            image_url = response.data[0].url
            # Get the binary image data from the URL
            img_binary_data = requests.get(image_url).content
            img = Image.open(io.BytesIO(img_binary_data))

            # Record image url and prompt
            record_image_and_prompt(full_prompt, image_url, style, ratio)

            # After successfully generating an image, update the prompt count by sending a POST request
            update_response = requests.post(IMAGE_SERVER_DOMAIN + '/update_prompts')
            if update_response.status_code == 200:
                num_prompts -= 1  # Decrement the prompt count after the update
            else:
                return None, "Error updating prompt count.", ""

            return img, f"You have {num_prompts} prompts left", image_url

        except Exception as e:
            return None, f"An error occurred: {e}", ""
    else:
        return None, "You have no prompts left.", ""


def surprise_me():
    # Randomly select a prompt and a style
    tmp_prompt = random.choice(random_prompt)
    tmp_style = random.choice(styles)
    # Return the random prompt and style
    return tmp_prompt, tmp_style


# Helper function to get the current number of prompts left from the backend
def get_prompts_left():
    response = requests.get(IMAGE_SERVER_DOMAIN + '/get_prompts')
    if response.status_code == 200:
        return f"You have {response.json()['prompts_left']} prompts left."
    else:
        return "Error retrieving prompt count"


# Define the event handler for the generate button
def generate(prompt, negative_prompt, style, size, quality, session_state):
    img, message, image_url = generate_image(prompt, negative_prompt, style, size, quality)
    return img, message, image_url


# jump to the render page
def jump_render_page(image_url):
    # TODO: pass the image url to the display page
    param = {'image_url': image_url}
    # running under express js server
    network.jump(RENDER_SERVER_DOMAIN, param=param, method='get')


# change display to order
def change_to_order_display():
    return gr.Textbox(visible=False), gr.Textbox(visible=False), gr.Dropdown(visible=False), gr.Dropdown(
        visible=False), gr.Dropdown(visible=False), gr.Button(visible=False), gr.Button(visible=False), gr.Button(
        visible=False), gr.Button(visible=False), gr.Label(visible=False), gr.Button(visible=False), gr.Dropdown(
        visible=True), gr.Dropdown(visible=True), gr.Dropdown(visible=True), gr.Textbox(visible=True), gr.Button(
        visible=True), gr.Button(visible=True), gr.Number(visible=True), gr.Markdown(visible=False), gr.Markdown(visible=True)


# change display to image generation
def change_to_generation_display():
    return gr.Textbox(visible=True), gr.Textbox(visible=True), gr.Dropdown(visible=True), gr.Dropdown(
        visible=True), gr.Dropdown(visible=True), gr.Button(visible=True), gr.Button(visible=True), gr.Button(
        visible=True), gr.Button(visible=True), gr.Label(visible=True), gr.Button(visible=True), gr.Dropdown(
        visible=False), gr.Dropdown(visible=False), gr.Dropdown(visible=False), gr.Textbox(visible=False), gr.Button(
        visible=False), gr.Button(visible=False), gr.Number(visible=False), gr.Markdown(visible=True), gr.Markdown(visible=False)


# Logic to add more prompts when "Get more" is clicked
def add_prompts(session_state):
    if 'session_id' in session_state:
        session_state[session_state['session_id']] = 5
    response = requests.post(IMAGE_SERVER_DOMAIN + '/add_prompts')
    if response.status_code == 200 and response.json()['status'] == 'success':
        return "You have 5 prompts left."
    else:
        return "Error! Please try again!"


def change_size_dropdown(kind):
    if kind == 'clothe':
        return gr.Dropdown(label="Size", choices=clothe_size, value='M'), gr.Dropdown(interactive=True, visible=True)
    elif kind == 'canvas':
        return gr.Dropdown(label="Size(cm)", choices=canvas_size, value=canvas_size[0], interactive=True), gr.Dropdown(
            visible=False)
    elif kind == 'post':
        return gr.Dropdown(label="Size", choices=post_size, value=post_size[0], interactive=True), gr.Dropdown(
            visible=False)


# Create the Gradio interface
with gr.Blocks() as demo:
    generation_title = gr.Markdown("<h1>Create your AI art</h1>", visible=True)
    order_title = gr.Markdown("<h1>Check your order</h1>", visible=False)

    with gr.Row():
        prompt = gr.Textbox(placeholder="A bunny in a spacesuit", label="Describe your image")
    with gr.Row():
        negative_prompt = gr.Textbox(placeholder="unwanted themes or characteristics",
                                     label="Something you don't like (Optional)")
    with gr.Row():
        style = gr.Dropdown(choices=styles, label="Select image style", value="No Style")
        ratio = gr.Dropdown(choices=ratios, label="Select image ratio", value="1:1")
        quality = gr.Dropdown(choices=qualities, label="Select image quality", value="standard")
    with gr.Row():
        generate_btn = gr.Button("Generate")
        surprise_btn = gr.Button("Surprise me", icon="./public/🎁.png")
    output_image = gr.Image(label="Your AI Generated Art")
    with gr.Row():
        image_url = gr.Textbox(
            "https://oaidalleapiprodscus.blob.core.windows.net/private/org-sEbC9g0SYxi1GqsvDqWMNi6l/user-fmy5WrRtRPgJvvPdrS8CBJnC/img-ImftP3jWw50x0XabV3eLAEBI.png?st=2024-02-28T03%3A04%3A35Z&se=2024-02-28T05%3A04%3A35Z&sp=r&sv=2021-08-06&sr=b&rscd=inline&rsct=image/png&skoid=6aaadede-4fb3-4698-a8f6-684d7786b067&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2024-02-28T01%3A01%3A05Z&ske=2024-02-29T01%3A01%3A05Z&sks=b&skv=2021-08-06&sig=MxWKeBG54ok4OryjBVPIjCablO%2BmB6RvpikONUyhSm8%3D",
            label="Image url", visible=False)
        show_btn = gr.Button("Show it!")
        buy_btn = gr.Button("Buy it!")
    prompts_left = gr.Label(get_prompts_left())
    get_more = gr.Button("Get more")
    generated_prompt = gr.Textbox(label="Generated prompt", visible=False)
    generated_style = gr.Textbox(label="Generated style", visible=False)

    with gr.Row():
        kind = gr.Dropdown(label="What kind of things you want to buy", choices=kind_list, value='clothe',
                           interactive=True, visible=False)
        size = gr.Dropdown(label="Size", choices=clothe_size, value='M', interactive=True, visible=False)
        color = gr.Dropdown(label="Clothe Color", choices=color_list, value=color_list[0], interactive=True,
                            visible=False)
        quantity = gr.Number(label="Quantity", value=1, minimum=1, interactive=True, visible=False)
    with gr.Row():
        address = gr.Textbox(label="Your address", placeholder="somewhere you want to receive the package",
                             interactive=True, visible=False)
    with gr.Row():
        back_btn = gr.Button("Back to generation page", visible=False)
        pay_btn = gr.Button("Pay it!", visible=False)

    session_state = gr.State({})

    generate_btn.click(
        fn=generate,
        inputs=[prompt, negative_prompt, style, ratio, quality, session_state],
        outputs=[output_image, prompts_left, image_url]
    )
    # Define the event handler for the "Surprise Me" button
    surprise_btn.click(
        fn=surprise_me,
        inputs=[],
        outputs=[prompt, style]
    )

    show_btn.click(
        fn=jump_render_page,
        inputs=[image_url],
        outputs=[]
    )

    buy_btn.click(
        fn=change_to_order_display,
        inputs=[],
        outputs=[prompt, negative_prompt, style, ratio, quality, generate_btn, surprise_btn, show_btn, buy_btn,
                 prompts_left, get_more, kind, size, color, address, pay_btn, back_btn, quantity, generation_title, order_title]
    )

    back_btn.click(
        fn=change_to_generation_display,
        inputs=[],
        outputs=[prompt, negative_prompt, style, ratio, quality, generate_btn, surprise_btn, show_btn, buy_btn,
                 prompts_left, get_more, kind, size, color, address, pay_btn, back_btn, quantity, generation_title, order_title]
    )

    get_more.click(
        fn=add_prompts,
        inputs=[session_state],
        outputs=prompts_left
    )
    kind.change(
        fn=change_size_dropdown,
        inputs=[kind],
        outputs=[size, color]
    )

# Launch the Gradio interface
demo.launch(share=True, server_port=7860)
