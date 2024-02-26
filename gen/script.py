import gradio as gr
from openai import OpenAI
import requests
import io
from PIL import Image
import uuid

# Initialize OpenAI client with your API key
client = OpenAI(api_key="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")

# Define the function that will call the OpenAI API to generate an image
def generate_image(prompt, style, session_state):
    session_id = session_state.get('session_id')
    num_prompts = session_state.get(session_id, 30)

    if num_prompts > 0:
        # Decrease the prompt count
        session_state[session_id] -= 1

        # Add the style to the prompt
        full_prompt = f"{prompt}, draw it in {style} style"
        # Call the OpenAI API
        response = client.images.generate(
            model="dall-e-3",
            prompt=full_prompt,
            size="1024x1024",
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

# Define the styles as seen in the screenshot
styles = [
    "Impressionism",
    "Surrealism",
    "Pop Art",
    "Cubism",
    "Renaissance",
    "Abstract Expressionism",
    "Watercolor",
    "Pixel Art",
    "Ukiyo-e",
    "Baroque",
    "Neoclassicism",
    "Art Deco",
    "Minimalism",
    "Futurism",
    "Graffiti",
    "Op Art",
    "Lowbrow",
    "Photorealism",
    "Naive Art"
]

# Create the Gradio interface
with gr.Blocks() as demo:
    gr.Markdown("<h1>Create your AI art</h1>")
    with gr.Row():
        prompt = gr.Textbox(placeholder="A bunny in a spacesuit", label="Describe your image")
        style = gr.Dropdown(choices=styles, label="Select image style")
    generate_btn = gr.Button("Generate")
    output_image = gr.Image(label="Your AI Generated Art")
    prompts_left = gr.Label()
    get_more = gr.Button("Get more")

    session_state = gr.State({})

    # Define the event handler for the generate button
    def generate(prompt, style, session_state):
        # Check if the session_id is initialized
        if 'session_id' not in session_state:
            # Initialize it with a unique identifier
            session_state['session_id'] = str(uuid.uuid4())
            session_state[session_state['session_id']] = 30  # Start with 30 prompts
        return generate_image(prompt, style, session_state)

    generate_btn.click(
        fn=generate, 
        inputs=[prompt, style, session_state], 
        outputs=[output_image, prompts_left]
    )

    # Logic to add more prompts when "Get more" is clicked
    def add_prompts(session_state):
        if 'session_id' in session_state:
            session_state[session_state['session_id']] = 30
        return "You have 30 prompts left."

    get_more.click(
        fn=add_prompts,
        inputs=[session_state],
        outputs=prompts_left
    )

# Launch the Gradio interface
demo.launch(share=True)