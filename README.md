# AI Assistant Application

This application is a Streamlit interface for interacting with OpenAI's AI assistants. It allows users to create assistants, upload files to them, send them messages, and view their responses.

Here's a high-level overview of what each function does:

- `init()`: Initializes session state variables.
- `set_apikey()`: Allows the user to input their OpenAI API key.
- `config(client)`: Fetches a list of assistants and returns the selected assistant's ID.
- `upload_file(client, assistant_id, uploaded_file)`: Uploads a file to the selected assistant.
- `assistant_handler(client, assistant_id)`: Handles assistant updates, including name, instructions, model, and file management.
- `create_assistant(client)`: Creates a new assistant with a given name, instructions, and model.
- `chat_prompt(client, assistant_option)`: Handles the chat interface, allowing the user to send messages to the assistant and receive responses.
- `chat_display(client)`: Displays the chat history, including any images returned by the assistant.
- `main()`: The main function that runs the Streamlit application. It handles API key input, assistant selection, and chat initiation.

## Installation

1. Clone the repository: `git clone https://github.com/calapsss/assistants-api-easy.git`
2. Navigate to `assistants-api-easy` directory: `cd assistants-api-easy`
3. You can install the package `poetry install`
4. Navigate to frontend folder: `cd frontend`
5. Run with Poetry: `poetry run streamlit run app.py`
