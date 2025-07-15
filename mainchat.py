# pylint: disable=line-too-long,useless-suppression
# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

"""
DESCRIPTION:
    This file implements a dynamic chat interface using Chainlit
    to interact with an Azure AI Agent Service agent configured with MCP.
    
USAGE:
    chainlit run mainchat.py

    Before running the application:
    
    pip install azure-ai-projects azure-ai-agents azure-identity chainlit --pre

    Set these environment variables with your own values:
    1) PROJECT_ENDPOINT - The Azure AI Project endpoint
    2) MODEL_DEPLOYMENT_NAME - The deployed model name
    3) MCP_SERVER_URL - The URL of your MCP server
    4) MCP_SERVER_LABEL - A label for your MCP server
    5) MCP_SERVER_TOKEN - Authentication token for the MCP server (optional)
"""

import os
import time
import asyncio
from typing import Dict, Optional
import chainlit as cl
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import McpTool, RequiredMcpToolCall, SubmitToolApprovalAction, ToolApproval

# Load environment variables from .env file
load_dotenv()

class AzureAIAgentHandler:
    def __init__(self):
        self.project_client: Optional[AIProjectClient] = None
        self.agents_client = None
        self.agent = None
        self.thread = None
        self.mcp_tool = None
        
    async def initialize(self):
        """Initialize Azure AI client and create agent with MCP"""
        try:
            # Get MCP server configuration from environment variables
            mcp_server_url = os.environ.get("MCP_SERVER_URL")
            mcp_server_label = os.environ.get("MCP_SERVER_LABEL")
            mcp_server_token = os.environ.get("MCP_SERVER_TOKEN")
            azure_project_endpoint = os.environ.get("PROJECT_ENDPOINT")
            azure_model_deployment_name = os.environ.get("MODEL_DEPLOYMENT_NAME")

            # Verify that required environment variables are set
            required_vars = ["PROJECT_ENDPOINT", "MODEL_DEPLOYMENT_NAME", "MCP_SERVER_URL", "MCP_SERVER_LABEL"]
            missing_vars = [var for var in required_vars if not os.environ.get(var)]
            if missing_vars:
                raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

            # Initialize project client
            self.project_client = AIProjectClient(
                endpoint=azure_project_endpoint,
                credential=DefaultAzureCredential(),
            )

            # Initialize agent MCP tool with authentication headers
            self.mcp_tool = McpTool(
                server_label=mcp_server_label,
                server_url=mcp_server_url
            )

            # Configure authentication headers immediately after tool creation
            if mcp_server_token:
                self.mcp_tool.update_headers("Authorization", f"Bearer {mcp_server_token}")
            else:
                print("Warning: No MCP_SERVER_TOKEN found in environment variables")

            # Create agents client
            self.agents_client = self.project_client.agents

            # Create a new agent
            self.agent = self.agents_client.create_agent(
                model=azure_model_deployment_name,
                name="HomeAssistantMCPChatAgent",
                instructions=f"""You are a helpful assistant that can use MCP tools to help users. 
                You have access to a Home Assistant MCP server at {mcp_server_url} with label '{mcp_server_label}'.
                Use the available MCP tools to answer questions about home automation, sensor data, and device control.
                When making MCP calls, ensure you use the proper authentication headers that have been configured.
                Always respond in a clear and helpful manner.""",
                tools=self.mcp_tool.definitions,
            )

            # Create thread for communication
            self.thread = self.agents_client.threads.create()
            
            # Configure approval mode
            self.mcp_tool.set_approval_mode("never")  # Disable approval requirement for smoother operation
            
            return True
            
        except Exception as e:
            print(f"Error initializing agent: {e}")
            return False

    async def send_message(self, content: str) -> str:
        """Send a message to the agent and return the response"""
        try:
            # Create message in thread
            message = self.agents_client.messages.create(
                thread_id=self.thread.id,
                role="user",
                content=content,
            )

            # Create and process agent run in thread with MCP tools
            run = self.agents_client.runs.create(
                thread_id=self.thread.id, 
                agent_id=self.agent.id, 
                tool_resources=self.mcp_tool.resources
            )

            # Wait for run completion
            while run.status in ["queued", "in_progress", "requires_action"]:
                await asyncio.sleep(1)
                run = self.agents_client.runs.get(thread_id=self.thread.id, run_id=run.id)

                if run.status == "requires_action" and isinstance(run.required_action, SubmitToolApprovalAction):
                    tool_calls = run.required_action.submit_tool_approval.tool_calls
                    if not tool_calls:
                        print("No tool calls provided - cancelling run")
                        self.agents_client.runs.cancel(thread_id=self.thread.id, run_id=run.id)
                        break

                    tool_approvals = []
                    for tool_call in tool_calls:
                        if isinstance(tool_call, RequiredMcpToolCall):
                            try:
                                tool_approvals.append(
                                    ToolApproval(
                                        tool_call_id=tool_call.id,
                                        approve=True,
                                        headers=self.mcp_tool.headers,
                                    )
                                )
                            except Exception as e:
                                print(f"Error approving tool_call {tool_call.id}: {e}")

                    if tool_approvals:
                        self.agents_client.runs.submit_tool_outputs(
                            thread_id=self.thread.id, 
                            run_id=run.id, 
                            tool_approvals=tool_approvals
                        )

            if run.status == "failed":
                return f"Error: Run failed - {run.last_error}"

            # Get all messages and return the latest assistant response
            messages = self.agents_client.messages.list(thread_id=self.thread.id)
            for msg in messages:
                if msg.role == "assistant" and msg.text_messages:
                    last_text = msg.text_messages[-1]
                    return last_text.text.value
            
            return "No response received from agent."
            
        except Exception as e:
            return f"Error processing message: {str(e)}"

    def cleanup(self):
        """Clean up resources"""
        if self.project_client:
            self.project_client.close()

# Global instance of the agent handler
agent_handler = AzureAIAgentHandler()

@cl.on_chat_start
async def start():
    """Runs when a new chat session is started"""
    await cl.Message(
        content="🤖 Initializing Azure AI agent with MCP...",
        author="System"
    ).send()
    
    # Initialize the agent
    success = await agent_handler.initialize()
    
    if success:
        await cl.Message(
            content="✅ Agent initialized successfully! You can now ask questions about your home automation system.",
            author="System"
        ).send()
        
        # Store agent information in user session
        cl.user_session.set("agent_ready", True)
        cl.user_session.set("agent_id", agent_handler.agent.id)
        cl.user_session.set("thread_id", agent_handler.thread.id)
        
        await cl.Message(
            content=f"📋 **Session Information:**\n- Agent ID: `{agent_handler.agent.id}`\n- Thread ID: `{agent_handler.thread.id}`\n- MCP Server: `{agent_handler.mcp_tool.server_label}`",
            author="System"
        ).send()
    else:
        await cl.Message(
            content="❌ Error initializing agent. Please check your environment variables configuration.",
            author="System"
        ).send()
        cl.user_session.set("agent_ready", False)

@cl.on_message
async def main(message: cl.Message):
    """Handles incoming user messages"""
    # Check if agent is ready
    if not cl.user_session.get("agent_ready", False):
        await cl.Message(
            content="❌ Agent is not properly initialized. Please reload the page.",
            author="System"
        ).send()
        return
    
    # Show processing indicator
    async with cl.Step(name="Processing with Azure AI Agent + MCP") as step:
        step.output = "Sending message to agent..."
        
        # Send message to agent and get response
        response = await agent_handler.send_message(message.content)
        
        step.output = f"Response received: {len(response)} characters"
    
    # Send response to user
    await cl.Message(
        content=response,
        author="AI Assistant"
    ).send()

@cl.on_chat_end
async def end():
    """Runs when chat session ends"""
    agent_handler.cleanup()
    print("Chat session ended, resources cleaned up.")

if __name__ == "__main__":
    # To run directly with python (not recommended, use 'chainlit run mainchat.py')
    print("To run this application, use: chainlit run mainchat.py")
