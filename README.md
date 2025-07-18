# Azure AI Agent with MCP and Chainlit

This project includes two implementations for interacting with an Azure AI Agent Service agent configured with Model Context Protocol (MCP):

1. **main.py** - Basic implementation with a fixed message
2. **mainchat.py** - Interactive chat interface using Chainlit

## Prerequisites

This project is designed to run in a **DevContainer** for the best development experience. The DevContainer includes all necessary tools pre-installed.

### Option 1: Using DevContainer (Recommended)

If you have VS Code with the DevContainer extension installed:

1. **Install VS Code**: Download from [https://code.visualstudio.com/](https://code.visualstudio.com/)
2. **Install DevContainer extension**: Install the "Dev Containers" extension in VS Code
3. **Install Docker**: Make sure Docker is installed and running on your system
4. **Open in DevContainer**: 
   - Clone this repository
   - Open VS Code in the project folder
   - When prompted, click "Reopen in Container" or press `Ctrl+Shift+P` and select "Dev Containers: Reopen in Container"

The DevContainer includes:
- Git (latest version)
- Node.js, npm, and ESLint
- Python 3 and pip3
- Azure CLI
- All necessary dependencies

### Option 2: Local Development (Without DevContainer)

If you prefer not to use DevContainer, you'll need to install the following manually:

1. **Python 3.8+**: Download from [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. **Azure CLI**: Install from [https://docs.microsoft.com/en-us/cli/azure/install-azure-cli](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
3. **Git**: Download from [https://git-scm.com/downloads](https://git-scm.com/downloads)

## Setup

### 1. Azure Authentication

Before running the application, you need to authenticate with Azure:

```bash
az login
```

This will open a browser window where you can log in with your Azure credentials. Make sure you have:

- An active Azure subscription
- Access to Azure AI Services
- Proper permissions to create and manage AI resources

**Note**: If you're using DevContainer, the Azure CLI is already installed. If you're developing locally without DevContainer, make sure you have installed the Azure CLI from the prerequisites section above.

After successful login, you can verify your authentication by running:

```bash
az account show
```

### 2. Environment Variables

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

### 3. Install Dependencies

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

### DevContainer Environment
- This project is optimized for DevContainer usage with all dependencies pre-installed
- The DevContainer runs on Debian GNU/Linux 11 (bullseye)
- All necessary tools (Git, Node.js, Python, Azure CLI) are available on the PATH

### Azure Requirements
- **Azure Authentication**: You must run `az login` before using the application
- **Azure Credentials**: Make sure you have valid Azure credentials and proper permissions
- **Azure AI Services**: Ensure you have access to Azure AI Services in your subscription
- **Network Access**: The MCP server must be accessible from the application

### Additional Requirements
- **MCP Server**: For Home Assistant MCP, ensure the server is running and properly configured
- **Environment Variables**: All required environment variables must be properly set in the `.env` file
- **Model Deployment**: Verify that your Azure AI model deployment is active and accessible

## Troubleshooting

### Common Issues

1. **Azure Authentication Errors**
   - Run `az login` to ensure you're properly authenticated
   - Verify your account has the necessary permissions: `az account show`
   - Check if you're in the correct subscription: `az account list`

2. **DevContainer Issues**
   - Ensure Docker is running on your system
   - Try rebuilding the container: `Ctrl+Shift+P` → "Dev Containers: Rebuild Container"
   - Check VS Code has the latest DevContainer extension installed

3. **Environment Variable Issues**
   - Verify the `.env` file exists and contains all required variables
   - Ensure no trailing spaces or special characters in the environment values
   - Check that the Azure AI project endpoint is correct and accessible

4. **MCP Server Connection Issues**
   - Verify the MCP server URL is accessible
   - Check if authentication tokens are correctly configured
   - Ensure network connectivity to the MCP server
