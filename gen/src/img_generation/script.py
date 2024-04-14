import json
import webbrowser

import gradio as gr
from openai import OpenAI
import requests, io, os, dotenv
from PIL import Image
import random, prompt
import country_info

# Load the environment variables from the .env file
dotenv.load_dotenv()
IMAGE_SERVER_DOMAIN = os.getenv('IMAGE_SERVER_DOMAIN')
SERVER_IP = os.getenv('SERVER_IP')
# Initialize OpenAI client with your API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
HOST_IP = os.getenv('HOST_IP')
GRADIO_SERVER_PORT = int(os.getenv('GRADIO_SERVER_PORT'))
RENDER_SERVER_DOMAIN = os.getenv('RENDER_SERVER_DOMAIN')
MODE = os.getenv('MODE', 'server')

if MODE == 'local':
    IMAGE_SERVER_DOMAIN = "http://127.0.0.1:5000"
    HOST_IP = '127.0.0.1'
    SERVER_IP = '127.0.0.1'
    # Any other configurations that need to be set for local mode

# Button and Links    
BUTTON_ICON = "http://" + SERVER_IP + ":5000/public/button.png"
ILLEGAL_PAYMENT_HTML = "http://" + SERVER_IP + ":5000/public/illegal_payment.html"
BASE_REDIRECT_URL = f"http://{SERVER_IP}:5500" + "/render?image_url=http://" + SERVER_IP + f":5000/"
STRIPE_REDIRECT_HTML_TEMPLATE = "<a href={} target='_blank'><img src={} alt='Click Me' style='width:10%; height:auto;'></a>"

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
kind_list = ['hoodie', 'canvas', 'poster']
hoodie_size = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
canvas_size = ['20x25', '30x40', '40x50', '60x80']
poster_size = ['A1', 'A2', 'A3']
color_list = ['white', 'red', 'green', 'blue', 'black']
country_en_name_list = country_info.country_en_name_list
country_phone_codes_map_list = country_info.country_phone_codes_map_list


def generate_prompt(prompt, negative_prompt, style):
    if negative_prompt is None or negative_prompt == '':
        pass
    else:
        prompt += "and I don't want {negative_prompt}"
    if style != "No Style":
        prompt += ", please draw the picture in {style} style"

    return prompt


def record_image_and_prompt(prompt, image_url, style, ratio):
    params = {
        'url': image_url,
        'prompt': prompt,
        'style': style,
        'ratio': ratio
    }
    response = requests.post(f"{IMAGE_SERVER_DOMAIN}/add_image_record", json=params)
    if response.status_code != 200:
        raise Exception(f"Failed to record image and prompt: {response.text}")
    local_url = response.json().get('local_url')
    if not local_url:
        raise Exception("Failed to retrieve the local URL from response")
    return local_url



def generate_image(prompt, negative_prompt, style, ratio, quality):
    try:
        response = requests.get(f"{IMAGE_SERVER_DOMAIN}/get_prompts")
        response.raise_for_status()
        num_prompts = response.json().get('prompts_left', 0)

        if num_prompts <= 0:
            return None, "You have no prompts left.", ""

        size_mapping = {"1:1": sizes[0], "4:7": sizes[1], "7:4": sizes[2]}
        size = size_mapping.get(ratio)
        if not size:
            return None, "Invalid ratio specified.", ""

        full_prompt = generate_prompt(prompt, negative_prompt, style)
        response = client.images.generate(model="dall-e-3", prompt=full_prompt, size=size, quality=quality, n=1)
        image_url = response.data[0].url
        img_binary_data = requests.get(image_url).content
        img = Image.open(io.BytesIO(img_binary_data))

        local_url = record_image_and_prompt(full_prompt, image_url, style, ratio)
        image_url = local_url if local_url else image_url  # fallback to original URL if local URL fails

        requests.post(f"{IMAGE_SERVER_DOMAIN}/update_prompts")  # Assuming this always succeeds
        num_prompts -= 1
        return img, f"You have {num_prompts} prompts left", image_url

    except requests.RequestException as e:
        return None, f"Network error: {e}", ""
    except Exception as e:
        return None, f"An error occurred: {e}", ""


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
    return img, message, image_url, jump_render_page(image_url)


def jump_render_page(image_url):
    # This is the URL where the Node.js server will handle the GET request
    redirect_url = BASE_REDIRECT_URL + f"{image_url}"
    image_button = f"<a href={redirect_url} target='_blank'><img src={BUTTON_ICON} alt='Click Me' style='width:20%; height:auto;'></a>"
    # the appearance of the button
    return image_button


# change display to order
def change_to_order_display():
    return (
        gr.Textbox(visible=False),  # Original prompt textbox
        gr.Textbox(visible=False),  # Negative prompt textbox
        gr.Dropdown(visible=False),  # Style dropdown
        gr.Dropdown(visible=False),  # Image ratio dropdown
        gr.Dropdown(visible=False),  # Image quality dropdown
        gr.Button(visible=False),  # Generate image button
        gr.Button(visible=False),  # Surprise me button
        gr.Button(visible=False),  # Show button
        gr.Button(visible=False),  # Buy button (hidden when showing order)
        gr.Label(visible=False),  # Prompts left label
        gr.Button(visible=False),  # Get more button
        gr.Dropdown(visible=True),  # Kind of item dropdown (visible in order)
        gr.Dropdown(visible=True),  # Size dropdown (visible in order)
        gr.Dropdown(visible=True),  # Color dropdown (visible in order)
        gr.Textbox(visible=True),  # Order Zip Code (visible in order)
        gr.Textbox(visible=True),  # Order address textbox (visible in order)
        gr.Button(visible=False),  # Pay button (visible in order)
        gr.Button(visible=True),  # Back button (visible in order)
        gr.Number(visible=True),  # Quantity number input (visible in order)
        gr.Markdown(visible=False),  # Generation title markdown
        gr.Markdown(visible=True),  # Order title markdown (visible in order)
        gr.HTML(visible=False),  # Link output HTML
        gr.Dropdown(visible=True),  # Order country dropdown (visible in order)
        gr.Textbox(visible=True),  # Order first name textbox (visible in order)
        gr.Textbox(visible=True),  # Order last name textbox (visible in order)
        gr.Dropdown(visible=True),  # Order phone code dropdown (visible in order)
        gr.Textbox(visible=True),  # Order phone number textbox (visible in order)
        gr.HTML(visible=True),  # stripe pay link
        gr.Label(visible=True)  # address tip
    )


# change display to image generation
def change_to_generation_display():
    return (
        gr.Textbox(visible=True),  # Original prompt textbox (visible in generation)
        gr.Textbox(visible=True),  # Negative prompt textbox (visible in generation)
        gr.Dropdown(visible=True),  # Style dropdown (visible in generation)
        gr.Dropdown(visible=True),  # Image ratio dropdown (visible in generation)
        gr.Dropdown(visible=True),  # Image quality dropdown (visible in generation)
        gr.Button(visible=True),  # Generate image button (visible in generation)
        gr.Button(visible=True),  # Surprise me button (visible in generation)
        gr.Button(visible=False),  # Show button
        gr.Button(visible=True),  # Buy button (visible in generation)
        gr.Label(visible=True),  # Prompts left label (visible in generation)
        gr.Button(visible=True),  # Get more button (visible in generation)
        gr.Dropdown(visible=False),  # Kind of item dropdown
        gr.Dropdown(visible=False),  # Size dropdown
        gr.Dropdown(visible=False),  # Color dropdown
        gr.Textbox(visible=False),  # Order Zip Code
        gr.Textbox(visible=False),  # Order address textbox
        gr.Button(visible=False),  # Pay button
        gr.Button(visible=False),  # Back button
        gr.Number(visible=False),  # Quantity number input
        gr.Markdown(visible=True),  # Generation title markdown (visible in generation)
        gr.Markdown(visible=False),  # Order title markdown
        gr.HTML(visible=True),  # Link output HTML (visible in generation)
        gr.Dropdown(visible=False),  # Order country dropdown
        gr.Textbox(visible=False),  # Order first name textbox
        gr.Textbox(visible=False),  # Order last name textbox
        gr.Dropdown(visible=False),  # Order phone code dropdown
        gr.Textbox(visible=False),  # Order phone number textbox
        gr.HTML(visible=False),  # stripe pay link
        gr.Label(visible=False)  # address tip
    )


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
    if kind == 'hoodie':
        return gr.Dropdown(label="Size", choices=hoodie_size, value='M'), gr.Dropdown(interactive=True, visible=True)
    elif kind == 'canvas':
        return gr.Dropdown(label="Size(cm)", choices=canvas_size, value=canvas_size[0], interactive=True), gr.Dropdown(
            visible=False)
    elif kind == 'poster':
        return gr.Dropdown(label="Size", choices=poster_size, value=poster_size[0], interactive=True), gr.Dropdown(
            visible=False)

#####################
def validate_order_details(**order_details):
    # Validate required fields are present and non-empty
    required_fields = ['order_address', 'order_country', 'order_first_name', 
                       'order_last_name', 'order_phone_code', 'order_phone_number', 'order_zip']
    missing_fields = [field for field in required_fields if not order_details.get(field)]
    if missing_fields:
        return False, f"You need to finish the order information: {', '.join(missing_fields)}"
    return True, ""

def generate_order_data(kind, **kwargs):
    # Initialize order data with common attributes
    order_data = {k: v for k, v in kwargs.items() if k in [
        'image_url', 'size', 'color', 'quantity', 'address', 'country', 
        'first_name', 'last_name', 'phone_code', 'phone_number', 'zip_code']}
    order_data['kind'] = kind
    return order_data

def post_order(order_data):
    response = requests.post(f"{IMAGE_SERVER_DOMAIN}/generate_order", json=order_data)
    if response.status_code != 200 or response.json().get('status') == "error":
        error_message = response.json().get('message', 'An unknown error occurred.')
        return None, f"Failed to generate order: {error_message}"
    return response.json()['order_id'], None

def generate_order(image_url, kind, size, color, quantity, order_address, order_country, order_first_name,
                   order_last_name, order_phone_code, order_phone_number, order_zip):
    # Validate order details
    valid, message = validate_order_details(
        order_address=order_address, order_country=order_country, order_first_name=order_first_name,
        order_last_name=order_last_name, order_phone_code=order_phone_code, 
        order_phone_number=order_phone_number, order_zip=order_zip
    )
    if not valid:
        return message, STRIPE_REDIRECT_HTML_TEMPLATE.format(ILLEGAL_PAYMENT_HTML, BUTTON_ICON)

    # Generate order data
    order_data = generate_order_data(kind, image_url=image_url, size=size, color=color, quantity=quantity, 
                                     address=order_address, country=order_country, first_name=order_first_name, 
                                     last_name=order_last_name, phone_code=order_phone_code, 
                                     phone_number=order_phone_number, zip_code=order_zip)

    # Post order and handle response
    order_id, error = post_order(order_data)
    if error:
        return error, STRIPE_REDIRECT_HTML_TEMPLATE.format(ILLEGAL_PAYMENT_HTML, BUTTON_ICON)

    # Create checkout session and redirect to payment page
    url = create_checkout_session(order_id, kind, quantity)
    return 'You can pay it now!', STRIPE_REDIRECT_HTML_TEMPLATE.format(url, BUTTON_ICON)

def create_checkout_session(order_id, kind, quantity):
    session_data = {'order_id': order_id, 'kind': kind, 'quantity': quantity}
    response = requests.post(f"{IMAGE_SERVER_DOMAIN}/create-checkout-session", json=session_data)
    try:
        response.raise_for_status()  # Will raise an HTTPError if the HTTP request returned an unsuccessful status code
        return response.json()['url']
    except requests.HTTPError as e:
        error_message = f"HTTP error occurred: {e}"
    except requests.RequestException as e:
        error_message = f"Network error occurred: {e}"
    except json.JSONDecodeError:
        error_message = "Response content is not valid JSON"
    
    # Default error message if none of the above exceptions are caught
    error_message = error_message or "An unknown error occurred"
    return f"Error creating payment session: {error_message}"


# Create the Gradio interface
with gr.Blocks(theme='Taithrah/Minimal') as demo:
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
            "",
            label="Image url", visible=False)
        show_btn = gr.Button("Show it!", visible=False)
        link_output = gr.HTML(
            f"<a href={BASE_REDIRECT_URL} target='_blank'><img src={BUTTON_ICON} alt='Click Me' style='width:10%; height:auto;'></a>")  # Use gr.HTML to render the link as clickable
        buy_btn = gr.Button("Buy it!")
    prompts_left = gr.Label(get_prompts_left())
    get_more = gr.Button("Get more")
    generated_prompt = gr.Textbox(label="Generated prompt", visible=False)
    generated_style = gr.Textbox(label="Generated style", visible=False)

    with gr.Row():
        kind = gr.Dropdown(label="What kind of things you want to buy", choices=kind_list, value=kind_list[0],
                           interactive=True, visible=False)
        size = gr.Dropdown(label="Size", choices=hoodie_size, value=hoodie_size[0], interactive=True, visible=False)
        color = gr.Dropdown(label="Hoodie Color", choices=color_list, value=color_list[0], interactive=True,
                            visible=False)
        quantity = gr.Number(label="Quantity", value=1, minimum=1, interactive=True, visible=False)
    with gr.Column():
        order_country = gr.Dropdown(label="Country/Region", value='Sweden', choices=country_en_name_list,
                                    interactive=True, visible=False)
        with gr.Row():
            order_first_name = gr.Textbox(label="First Name", placeholder="Your first name", interactive=True,
                                          visible=False)
            order_last_name = gr.Textbox(label="Last Name", placeholder="Your last name", interactive=True,
                                         visible=False)
        with gr.Row():
            order_phone_code = gr.Dropdown(label="Phone Code",
                                           value=country_phone_codes_map_list[country_en_name_list.index('Sweden')],
                                           choices=country_phone_codes_map_list, interactive=True, visible=False)
            order_phone_number = gr.Textbox(label="Phone Number", placeholder="Your phone number", interactive=True,
                                            visible=False)
            order_zip = gr.Textbox(label="Zip Code", placeholder="Enter your zip code", interactive=True, visible=False)

        order_address = gr.Textbox(label="Your address", placeholder="somewhere you want to receive the package",
                                   interactive=True, visible=False)
    with gr.Row():
        addressTip = gr.Label(visible=False)
    with gr.Row():
        back_btn = gr.Button("Back to generation page", visible=False)
        pay_btn = gr.Button("Pay it!", visible=False)
        pay_link_redirect = gr.HTML(
            f"<a href={ILLEGAL_PAYMENT_HTML} target='_blank'><img src={BUTTON_ICON} alt='Click Me' style='width:10%; height:auto;'></a>",
            visible=False)

    session_state = gr.State({})

    generate_btn.click(
        fn=generate,
        inputs=[prompt, negative_prompt, style, ratio, quality, session_state],
        outputs=[output_image, prompts_left, image_url, link_output]
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
        outputs=[link_output]
    )

    buy_btn.click(
        fn=change_to_order_display,
        inputs=[],
        outputs=[prompt, negative_prompt, style, ratio, quality, generate_btn, surprise_btn, show_btn, buy_btn,
                 prompts_left, get_more, kind, size, color, order_zip, order_address, pay_btn, back_btn, quantity,
                 generation_title,
                 order_title, link_output, order_country, order_first_name, order_last_name, order_phone_code,
                 order_phone_number, pay_link_redirect, addressTip]
    )

    back_btn.click(
        fn=change_to_generation_display,
        inputs=[],
        outputs=[prompt, negative_prompt, style, ratio, quality, generate_btn, surprise_btn, show_btn, buy_btn,
                 prompts_left, get_more, kind, size, color, order_zip, order_address, pay_btn, back_btn, quantity,
                 generation_title,
                 order_title, link_output, order_country, order_first_name, order_last_name, order_phone_code,
                 order_phone_number, pay_link_redirect, addressTip]
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

    pay_btn.click(
        fn=generate_order,
        inputs=[image_url, kind, size, color, quantity, order_address, order_country, order_first_name, order_last_name,
                order_phone_code, order_phone_number, order_zip],
        outputs=[addressTip, pay_link_redirect]
    )

    kind.change(
        fn=generate_order,
        inputs=[image_url, kind, size, color, quantity, order_address, order_country, order_first_name, order_last_name,
                order_phone_code, order_phone_number, order_zip],
        outputs=[addressTip, pay_link_redirect]
    )

    order_address.change(
        fn=generate_order,
        inputs=[image_url, kind, size, color, quantity, order_address, order_country, order_first_name, order_last_name,
                order_phone_code, order_phone_number, order_zip],
        outputs=[addressTip, pay_link_redirect]
    )

    order_zip.change(
        fn=generate_order,
        inputs=[image_url, kind, size, color, quantity, order_address, order_country, order_first_name, order_last_name,
                order_phone_code, order_phone_number, order_zip],
        outputs=[addressTip, pay_link_redirect]
    )

    order_phone_number.change(
        fn=generate_order,
        inputs=[image_url, kind, size, color, quantity, order_address, order_country, order_first_name, order_last_name,
                order_phone_code, order_phone_number, order_zip],
        outputs=[addressTip, pay_link_redirect]
    )

    order_first_name.change(
        fn=generate_order,
        inputs=[image_url, kind, size, color, quantity, order_address, order_country, order_first_name, order_last_name,
                order_phone_code, order_phone_number, order_zip],
        outputs=[addressTip, pay_link_redirect]
    )

    order_last_name.change(
        fn=generate_order,
        inputs=[image_url, kind, size, color, quantity, order_address, order_country, order_first_name, order_last_name,
                order_phone_code, order_phone_number, order_zip],
        outputs=[addressTip, pay_link_redirect]
    )

    order_phone_code.change(
        fn=generate_order,
        inputs=[image_url, kind, size, color, quantity, order_address, order_country, order_first_name, order_last_name,
                order_phone_code, order_phone_number, order_zip],
        outputs=[addressTip, pay_link_redirect]
    )

    order_country.change(
        fn=generate_order,
        inputs=[image_url, kind, size, color, quantity, order_address, order_country, order_first_name, order_last_name,
                order_phone_code, order_phone_number, order_zip],
        outputs=[addressTip, pay_link_redirect]
    )

# Launch the Gradio interface
demo.launch(server_name=HOST_IP, share=False, server_port=GRADIO_SERVER_PORT)