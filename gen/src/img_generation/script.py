import json
import webbrowser

import gradio as gr
from openai import OpenAI
import requests, io, os, dotenv
from PIL import Image
import random, prompt
import country_info
import currency_info

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
CHECKOUT_BUTTON_ICON = "http://" + SERVER_IP + ":5000/public/CheckoutButton.png"
PREVIEW_BUTTON_ICON = "http://" + SERVER_IP + ":5000/public/PreviewButton.png"
ILLEGAL_PAYMENT_HTML = "http://" + SERVER_IP + ":5000/public/illegal_payment.html"
BASE_REDIRECT_URL = f"http://{SERVER_IP}:5500" + "/render?image_url=http://" + SERVER_IP + f":5000/"
STRIPE_REDIRECT_HTML_TEMPLATE = "<a href={} target='_blank'><img src={} alt='Click Me' style='width:100%; height:auto;'></a>"

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
hoodie_size = ['S', 'M', 'L', 'XL']
canvas_size = ['12x16', '16x16', '18x24']
poster_size = ['12x16', '16x16', '18x24', '24x36']
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
    image_button = f"<a href={redirect_url} target='_blank'><img src={PREVIEW_BUTTON_ICON} alt='Click Me' style='width:100%; height:auto;'></a>"
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
        gr.Button(visible=True),  # Place Order button (visible in order)
        gr.HTML(visible=True),  # stripe pay link
        gr.Label(visible=True),  # address tip
        gr.Dropdown(visible=True),  # Currency dropdown
        gr.Label(visible=True),  # Price tip
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
        gr.Button(visible=False),  # Place Order button
        gr.HTML(visible=False),  # stripe pay link
        gr.Label(visible=False),  # address tip
        gr.Dropdown(visible=False),  # Currency dropdown
        gr.Label(visible=False),  # Price tip
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
        return gr.Dropdown(label="Size", choices=hoodie_size, value=hoodie_size[0]), gr.Dropdown(interactive=True, visible=True)
    elif kind == 'canvas':
        return gr.Dropdown(label="Size(cm)", choices=canvas_size, value=canvas_size[0], interactive=True), gr.Dropdown(
            visible=False)
    elif kind == 'poster':
        return gr.Dropdown(label="Size", choices=poster_size, value=poster_size[0], interactive=True), gr.Dropdown(
            visible=False)

#####################
def humanize_field_name(field_name):
    """Converts a field name from snake_case to Title Case without 'Order' and replaces underscores with spaces."""
    # Remove 'order_' prefix and replace underscores with spaces
    return ' '.join(word.title() for word in field_name.replace('order_', '').split('_')).title()

def validate_order_details(**order_details):
    # Define human-readable field names that correspond to the form labels.
    readable_field_names = {
        'order_country': 'Country/Region',
        'order_first_name': 'First Name',
        'order_last_name': 'Last Name',
        'order_phone_code': 'Phone Code',
        'order_phone_number': 'Phone Number',
        'order_zip': 'Zip Code',
        'order_address': 'Address',
        'order_currency': 'Currency'
    }

    # Validate required fields are present and non-empty.
    missing_fields = [
        humanize_field_name(field) for field in readable_field_names
        if not order_details.get(field)
    ]

    if missing_fields:
        # Format the list of missing fields into a human-readable string.
        if len(missing_fields) > 1:
            formatted_fields = ', '.join(missing_fields[:-1]) + ', and ' + missing_fields[-1]
        else:
            formatted_fields = missing_fields[0]
        
        return False, f"Please complete the following information: {formatted_fields}"

    return True, ""

def generate_order_data(kind, **kwargs):
    # Initialize order data with common attributes
    order_data = {k: v for k, v in kwargs.items() if k in [
        'image_url', 'size', 'color', 'quantity', 'address', 'country', 
        'first_name', 'last_name', 'phone_code', 'phone_number', 'zip_code', 'currency']}
    order_data['kind'] = kind
    return order_data

def post_order(order_data):
    response = requests.post(f"{IMAGE_SERVER_DOMAIN}/generate_order", json=order_data)
    if response.status_code != 200 or response.json().get('status') == "error":
        error_message = response.json().get('message', 'An unknown error occurred.')
        return None, f"Failed to generate order: {error_message}", 'Something went wrong. Please try again later.'
    data = response.json()
    order_id = data['order_id']
    price = data['price']
    return order_id, None, price

def generate_order(image_url, kind, size, color, quantity, order_address, order_country, order_first_name,
                   order_last_name, order_phone_code, order_phone_number, order_zip, order_currency):
    # Validate order details
    valid, message = validate_order_details(
        order_address=order_address, order_country=order_country, order_first_name=order_first_name,
        order_last_name=order_last_name, order_phone_code=order_phone_code, 
        order_phone_number=order_phone_number, order_zip=order_zip, order_currency=order_currency
    )
    if not valid:
        return message, STRIPE_REDIRECT_HTML_TEMPLATE.format(ILLEGAL_PAYMENT_HTML, CHECKOUT_BUTTON_ICON), "Something went wrong. Please try again later."

    # Generate order data
    order_data = generate_order_data(kind, image_url=image_url, size=size, color=color, quantity=quantity, 
                                     address=order_address, country=order_country, first_name=order_first_name, 
                                     last_name=order_last_name, phone_code=order_phone_code, 
                                     phone_number=order_phone_number, zip_code=order_zip, currency=order_currency)

    # Post order and handle response
    order_id, error, price = post_order(order_data)
    if error:
        return error, STRIPE_REDIRECT_HTML_TEMPLATE.format(ILLEGAL_PAYMENT_HTML, CHECKOUT_BUTTON_ICON), "Something went wrong. Please try again later."

    order_data['price'] = price
    if type(price) is float or type(price) is int:
        currency_symbol = currency_info.currency_symbol_map[order_currency]
        price = f"{currency_symbol} {price/100:.2f}"
    # Create checkout session and redirect to payment page
    url = create_checkout_session(order_id, kind, order_data)
    return 'You can pay it now!', STRIPE_REDIRECT_HTML_TEMPLATE.format(url, CHECKOUT_BUTTON_ICON), price

def create_checkout_session(order_id, kind, order_data):
    session_data = {'order_id': order_id, 'kind': kind, 'order_data': order_data}
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
with gr.Blocks(theme='Taithrah/Minimal', title="Paintbrush Magic - AI Art Generator") as demo:
    generation_title = gr.Markdown("# [Paintbrush Magic](https://www.paintbrushmagic.com): Create your AI art", visible=True)
    order_title = gr.Markdown("# [Paintbrush Magic](https://www.paintbrushmagic.com): Check your order", visible=False)

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
            f"<a href={BASE_REDIRECT_URL} target='_blank'><img src={PREVIEW_BUTTON_ICON} alt='Click Me' style='width:100%; height:auto;'></a>")  # Use gr.HTML to render the link as clickable
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
            order_currency = gr.Dropdown(label="Currency", choices=currency_info.currency_simple_name_list, value='USD', interactive=True,
                                         visible=False)

        order_address = gr.Textbox(label="Your address", placeholder="somewhere you want to receive the package",
                                   interactive=True, visible=False)
    with gr.Row():
        addressTip = gr.Label(value='Please fill the table!', visible=False)
    with gr.Row():
        back_btn = gr.Button("Back to generation page", visible=False)
        place_order_btn = gr.Button("Place Order", visible=False)

    with gr.Row():
        priceTip = gr.Label(label='Price', value='Click the place order button first.', visible=False)
        jump_to_payment_img_btn = gr.HTML(
            f"<a href={ILLEGAL_PAYMENT_HTML} target='_blank'><img src={CHECKOUT_BUTTON_ICON} alt='Click Me' style='width:100%; height:auto;'></a>",
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
                 prompts_left, get_more, kind, size, color, order_zip, order_address, back_btn, quantity,
                 generation_title,
                 order_title, link_output, order_country, order_first_name, order_last_name, order_phone_code,
                 order_phone_number, place_order_btn, jump_to_payment_img_btn, addressTip, order_currency, priceTip]
    )

    back_btn.click(
        fn=change_to_generation_display,
        inputs=[],
        outputs=[prompt, negative_prompt, style, ratio, quality, generate_btn, surprise_btn, show_btn, buy_btn,
                 prompts_left, get_more, kind, size, color, order_zip, order_address, back_btn, quantity,
                 generation_title,
                 order_title, link_output, order_country, order_first_name, order_last_name, order_phone_code,
                 order_phone_number, place_order_btn, jump_to_payment_img_btn, addressTip, order_currency, priceTip]
    )
    
    place_order_btn.click(
        fn=generate_order,
        inputs=[image_url, kind, size, color, quantity, order_address, 
                order_country, order_first_name, order_last_name,
                order_phone_code, order_phone_number, order_zip, order_currency],
        outputs=[addressTip, jump_to_payment_img_btn, priceTip]
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
    
    # order_country.change( #todo: currency varies by country
    #     fn=generate_order,
    #     inputs=[image_url, kind, size, color, quantity, order_address, order_country, order_first_name, order_last_name,
    #             order_phone_code, order_phone_number, order_zip],
    #     outputs=[addressTip, jump_to_payment_img_btn]
    # )

# Launch the Gradio interface
demo.launch(server_name=HOST_IP, share=False, server_port=GRADIO_SERVER_PORT)