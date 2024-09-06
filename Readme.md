**The project was suspended because of the lack of fundings.**
***
# Paintbrush Magic

**Paintbrush Magic** is a web application for generating AI-based images and rendering them on various products like hoodies, canvases, and posters. The application is built using Three.js for rendering, Gradio and Flask for the frontend and backend.

## Table of Contents

- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Environment Variables](#environment-variables)
- [Contributing](#contributing)
- [License](#license)

## Project Structure

```
Paintbrush Magic/
├── node_modules/
├── public/
├── views/
├── src/
│   ├── img_generation/
│   └── payment/
├── .env.local
├── .gitignore
├── CHANGELOG
├── dependency.sh
├── kill.sh
├── package-lock.json
├── package.json
├── README.md
├── requirements.txt
├── run.sh
├── server.js
├── stripe_webhook_white_ip.json
```

- **node_modules/**: Contains Node.js modules.
- **public/**: Publicly accessible files.
- **views/**: Views for the application.
- **src/**: Source code for image generation and payment modules.
  - **img_generation/**: Handles the AI image generation logic.
  - **payment/**: Manages payment processing.
- **.env.local**: Local environment configuration example.
- **.gitignore**: Specifies files to be ignored by Git.
- **CHANGELOG**: Log of changes made to the project.
- **dependency.sh**: Script to install dependencies.
- **kill.sh**: Script to kill running processes.
- **package-lock.json**: Lock file for Node.js dependencies.
- **package.json**: Configuration file for Node.js.
- **README.md**: Project documentation.
- **requirements.txt**: Python dependencies.
- **run.sh**: Script to run the application.
- **server.js**: Main server file.
- **stripe_webhook_white_ip.json**: Configuration for Stripe webhooks.

## Installation

### Prerequisites

- Node.js
- Python 3.x
- pip

### Steps:

1. ```sh
   git clone https://github.com/yourusername/paintbrushmagic.git
   cd paintbrushmagic/gen
   ./dependency.sh
   ```
2. Copy the `.env.local` file to `.env` and fill in the necessary environment variables:

   ```sh
   cp .env.local .env
   ```

## Usage

1. Start the frontend and backend:

   ```
   cd gen
   ./run.sh
   ```
2. Stop all process:

   ```sh
   ./gen/kill.sh
   ```
3. Access the application in your web browser at `http://localhost:YOUR_PORT`.

## Environment Variables

The project uses environment variables for configuration. Create a `.env` file in the `gen` directory and add your configuration details. An example configuration is provided in the `.env.local` file.

### Example `.env` File

```plaintext
if for localhost debugging, change the mode into `local`
MODE=local
```

## Contributing

We welcome contributions to Paintbrush Magic. To contribute, please follow these steps:

1. Fork the repository.
2. Create a new branch: `git checkout -b feature-branch-name`.
3. Make your changes and commit them: `git commit -m 'Add some feature'`.
4. Push to the branch: `git push origin feature-branch-name`.
5. Create a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

---

Feel free to modify any sections to better fit your project's specific needs or to add more detailed instructions.

## Todo

- [X] base AI generation webpage
- [X] restrict usage via IP(flask)
- [X] resize the image
- [X] payment via stripe
- [X] payment jumpback
- [X] image preview on product
- [X] connect all procedures
