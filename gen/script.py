import gradio as gr
from openai import OpenAI
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

# Define the function that will call the OpenAI API to generate an image
def generate_image(prompt, style, size, quality, session_state):
    session_id = session_state.get('session_id')
    num_prompts = session_state.get(session_id, 5)

    if num_prompts > 0:
        # Decrease the prompt count
        session_state[session_id] -= 1

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
        return img, f"You have {session_state[session_id]} prompts left"
    else:
        return None, "You have no prompts left."

def surprise_me():
    # Randomly select a prompt and a style
    tmp_prompt = random.choice(random_prompt)
    tmp_style = random.choice(styles)
    # Return the random prompt and style
    return tmp_prompt, tmp_style

# Define the styles as seen in the screenshot
styles = [   "Abstract Expressionism",   "Acrylic Painting",   "Art Deco",   "Baroque",   "Charcoal Drawing",   "Cubism",   "Engraving",   "Etching",   "Expressionism",   "Futurism",   "Gouache",   "Graffiti",   "Hyperrealism",   "Impressionism",   "Ink Drawing",   "Lithography",   "Lowbrow",   "Minimalism",   "Naive Art",   "Neoclassicism",   "No Style",   "Oil Painting",   "Op Art",   "Photorealism",   "Pixel Art",   "Pointillism",   "Pop Art",   "Realism",   "Renaissance",   "Screen Printing",   "Street Art",   "Surrealism",   "Trompe-l'oeil",   "Ukiyo-e",   "Watercolor",   "Watercolor Painting",   "Woodcut"]
sizes = ["1024x1024", "1024x1792", "1792x1024"]
qualities = ["standard", "hd"]


# Create the Gradio interface
with gr.Blocks() as demo:
    gr.Markdown("<h1>Create your AI art</h1>")
    with gr.Row():
        prompt = gr.Textbox(placeholder="A bunny in a spacesuit", label="Describe your image")
        style = gr.Dropdown(choices=styles, label="Select image style", value="No Style")
        size = gr.Dropdown(choices=sizes, label="Select image size", value="1024x1024")
        quality = gr.Dropdown(choices=qualities, label="Select image quality", value="standard")
    with gr.Row():
        generate_btn = gr.Button("Generate")
        surprise_btn = gr.Button("Surprise me", icon="🎁.png")
    output_image = gr.Image(label="Your AI Generated Art")
    prompts_left = gr.Label()
    get_more = gr.Button("Get more")
    generated_prompt = gr.Textbox(label="Generated prompt", visible=False)
    generated_style = gr.Textbox(label="Generated style", visible=False)

    session_state = gr.State({})

    # Define the event handler for the generate button
    def generate(prompt, style, size, quality, session_state):
        if 'session_id' not in session_state:
            session_state['session_id'] = str(uuid.uuid4())
            session_state[session_state['session_id']] = 5  # Start with 5 prompts
        return generate_image(prompt, style, size, quality, session_state)

    generate_btn.click(
        fn=generate, 
        inputs=[prompt, style, size, quality, session_state], 
        outputs=[output_image, prompts_left]
    )
    # Define the event handler for the "Surprise Me" button
    surprise_btn.click(
        fn=surprise_me,
        inputs=[],
        outputs=[prompt, style]
    )

    # Logic to add more prompts when "Get more" is clicked
    def add_prompts(session_state):
        if 'session_id' in session_state:
            session_state[session_state['session_id']] = 5
        return "You have 5 prompts left."

    get_more.click(
        fn=add_prompts,
        inputs=[session_state],
        outputs=prompts_left
    )

# Launch the Gradio interface
demo.launch(share=True)
