# Azure AI Agent with MCP and Chainlit

This project includes two implementations for interacting with an Azure AI Agent Service agent configured with Model Context Protocol (MCP):

1. **main.py** - Basic implementation with a fixed message
2. **mainchat.py** - Interactive chat interface using Chainlit

## Setup

### 1. Environment Variables

Copy the `.env.example` file to `.env` and configure the following variables:

```bash
cp .env.example .env
```

Edit the `.env` file with your values:

- `PROJECT_ENDPOINT`: Your Azure AI project endpoint
- `MODEL_DEPLOYMENT_NAME`: The deployed model name (e.g., gpt-4o)
- `MCP_SERVER_URL`: Your MCP server URL
- `MCP_SERVER_LABEL`: A label for your MCP server
- `MCP_SERVER_TOKEN`: Authentication token for the MCP server (optional)

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Run the Basic Example

```bash
python main.py
```

### Run the Interactive Chat Interface

```bash
chainlit run mainchat.py
```

The application will open in your browser at `http://localhost:8000` (by default).

## Features

### mainchat.py

- **Interactive web interface**: Using Chainlit for a smooth chat experience
- **Dynamic conversation**: Allows multiple message exchanges with the agent
- **Session information**: Shows agent and conversation thread details
- **Error handling**: Robust error management and connection states
- **Automatic configuration**: Automatic agent and MCP initialization on session start

### Key Features

1. **Automatic initialization**: Agent is automatically configured when starting a new session
2. **Asynchronous processing**: Uses async/await for non-blocking operations
3. **MCP tool handling**: Automatic approval of MCP tool calls
4. **User-friendly interface**: Visual status indicators and processing feedback
5. **Resource cleanup**: Proper resource management when session ends

## Project Structure

```
├── main.py              # Basic implementation
├── mainchat.py          # Chat interface with Chainlit
├── requirements.txt     # Project dependencies
├── .env.example        # Configuration example
└── README.md           # This file
```

## Important Notes

- Make sure you have Azure credentials properly configured
- The MCP server must be accessible from the application
- For Home Assistant MCP, ensure the server is running and properly configured
