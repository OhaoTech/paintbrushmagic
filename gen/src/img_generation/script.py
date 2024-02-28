import webbrowser

import gradio as gr
from openai import OpenAI
# openai error handling


import requests
import io, os
import dotenv
from PIL import Image
import uuid
import random
import prompt

# Load the environment variables from the .env file
dotenv.load_dotenv()

# Initialize OpenAI client with your API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
random_prompt = prompt.read_prompt()

def generate_prompt(prompt, negative_prompt, style):
    if negative_prompt is None or negative_prompt == '':
        pass
    else:
        prompt += "and I don't want {negative_prompt}"
    if style != "No Style":
        prompt += ", please draw the picture in {style} style"

    return prompt

def generate_image(prompt, negative_prompt, style, ratio, quality):
    # Check the number of prompts left by making a request to the Flask backend
    response = requests.get('http://localhost:5000/get_prompts')
    if response.status_code != 200:
        return None, "Error retrieving prompt count."
    num_prompts = response.json()['prompts_left']
    
    if num_prompts > 0:
        try:
            if ratio == "1:1":
                size = sizes[0]
            elif ratio == "5:4":
                size = sizes[2]
            else:
                size = sizes[0]

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

            param = {
                'url': image_url,
                'prompt': full_prompt,
                'style': style,
                'ratio': ratio
            }

            response = requests.post('http://localhost:5000/add_image_record', json=param)
            if response.status_code != 200:
                # TODO: when image generation record save failed
                pass
            else:
                # TODO: when image generation record save successfully
                pass

            if ratio == "1:1":
                pass
            elif ratio == "5:4":
                size = (1280, 1024)
                img = img.resize(size)
            else:
                size = (256, 256)
            
            # After successfully generating an image, update the prompt count by sending a POST request
            update_response = requests.post('http://localhost:5000/update_prompts')
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

# Define the styles as seen in the screenshot
styles = [   "Abstract Expressionism",   "Acrylic Painting",   "Art Deco",   "Baroque",   "Charcoal Drawing",   "Cubism",   "Engraving",   "Etching",   "Expressionism",   "Futurism",   "Gouache",   "Graffiti",   "Hyperrealism",   "Impressionism",   "Ink Drawing",   "Lithography",   "Lowbrow",   "Minimalism",   "Naive Art",   "Neoclassicism",   "No Style",   "Oil Painting",   "Op Art",   "Photorealism",   "Pixel Art",   "Pointillism",   "Pop Art",   "Realism",   "Renaissance",   "Screen Printing",   "Street Art",   "Surrealism",   "Trompe-l'oeil",   "Ukiyo-e",   "Watercolor",   "Watercolor Painting",   "Woodcut"]
ratios = ["1:1", "5:4"]
sizes = ["1024x1024", "1024x1792", "1792x1024"]
qualities = ["standard", "hd"]

# Helper function to get the current number of prompts left from the backend
def get_prompts_left():
    response = requests.get('http://localhost:5000/get_prompts')
    if response.status_code == 200:
        return f"You have {response.json()['prompts_left']} prompts left."
    else:
        return "Error retrieving prompt count"

# Create the Gradio interface
with gr.Blocks() as demo:
    gr.Markdown("<h1>Create your AI art</h1>")

    with gr.Row():
        prompt = gr.Textbox(placeholder="A bunny in a spacesuit", label="Describe your image")
    with gr.Row():
        negative_prompt = gr.Textbox(placeholder="unwanted themes or characteristics", label="Something you don't like (Optional)")
    with gr.Row():
        style = gr.Dropdown(choices=styles, label="Select image style", value="No Style")
        ratio = gr.Dropdown(choices=ratios, label="Select image ratio", value="1:1")
        quality = gr.Dropdown(choices=qualities, label="Select image quality", value="standard")
    with gr.Row():
        generate_btn = gr.Button("Generate")
        surprise_btn = gr.Button("Surprise me", icon="./public/🎁.png")
    output_image = gr.Image(label="Your AI Generated Art")
    with gr.Row():
        image_url = gr.Textbox(label="Image url", visible=False)
        show_bt = gr.Button("Show it!")
    prompts_left = gr.Label(get_prompts_left())
    get_more = gr.Button("Get more")
    generated_prompt = gr.Textbox(label="Generated prompt", visible=False)
    generated_style = gr.Textbox(label="Generated style", visible=False)

    session_state = gr.State({})

    # Define the event handler for the generate button
    def generate(prompt, negative_prompt, style, size, quality, session_state):
        img, message, image_url = generate_image(prompt, negative_prompt, style, size, quality)
        return img, message, image_url

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

    def show_rendered_cloth(image_url):
        # TODO: pass the image url to the display page
        param = {'image_url': image_url}
        webbrowser.open("http://127.0.0.1:5500/gen/GL/index.html")

    show_bt.click(
        fn=show_rendered_cloth,
        inputs=[image_url],
        outputs=[]
    )

    # Logic to add more prompts when "Get more" is clicked
    def add_prompts(session_state):
        if 'session_id' in session_state:
            session_state[session_state['session_id']] = 5
        response = requests.post('http://localhost:5000/add_prompts')
        if response.status_code == 200 and response.json()['status'] == 'success':
            return "You have 5 prompts left."
        else:
            return "Error! Please try again!"

    get_more.click(
        fn=add_prompts,
        inputs=[session_state],
        outputs=prompts_left
    )

# Launch the Gradio interface
demo.launch(share=True)
