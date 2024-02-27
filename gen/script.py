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


def generate_image(prompt, style, ratio, quality):
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
            full_prompt = f"{prompt}, draw it in {style} style"
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
                return None, "Error updating prompt count."

            return img, f"You have {num_prompts} prompts left"
        
        except Exception as e:
            return None, f"An error occurred: {e}"
    else:
        return None, "You have no prompts left."

def surprise_me(ratio, quality, session_state):
    # Randomly select a prompt and a style
    tmp_prompt = random.choice(random_prompt)
    tmp_style = random.choice(styles)

    img, prompt_left_str = generate_image(tmp_prompt, tmp_style, ratio, quality)

    # Return the random prompt and style
    return tmp_prompt, tmp_style, img, prompt_left_str

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
        style = gr.Dropdown(choices=styles, label="Select image style", value="No Style")
        ratio = gr.Dropdown(choices=ratios, label="Select image ratio", value="1:1")
        quality = gr.Dropdown(choices=qualities, label="Select image quality", value="standard")
    with gr.Row():
        generate_btn = gr.Button("Generate")
        surprise_btn = gr.Button("Surprise me", icon="🎁.png")
    output_image = gr.Image(label="Your AI Generated Art")
    prompts_left = gr.Label(get_prompts_left())
    get_more = gr.Button("Get more")
    generated_prompt = gr.Textbox(label="Generated prompt", visible=False)
    generated_style = gr.Textbox(label="Generated style", visible=False)

    session_state = gr.State({})

    # Define the event handler for the generate button
    def generate(prompt, style, size, quality, session_state):
        img, message = generate_image(prompt, style, size, quality)
        return img, message

    generate_btn.click(
        fn=generate, 
        inputs=[prompt, style, ratio, quality, session_state],
        outputs=[output_image, prompts_left]
    )
    # Define the event handler for the "Surprise Me" button
    surprise_btn.click(
        fn=surprise_me,
        inputs=[ratio, quality, session_state],
        outputs=[prompt, style, output_image, prompts_left]
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
