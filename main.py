# pylint: disable=line-too-long,useless-suppression
# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

"""
DESCRIPTION:
    This sample demonstrates how to use agent operations with the
    Model Context Protocol (MCP) tool from the Azure Agents service using a synchronous client.
    To learn more about Model Context Protocol, visit https://modelcontextprotocol.io/

USAGE:
    python sample_agents_mcp.py

    Before running the sample:

    pip install azure-ai-projects azure-ai-agents azure-identity --pre

    Set these environment variables with your own values:
    1) PROJECT_ENDPOINT - The Azure AI Project endpoint, as found in the Overview
                          page of your Azure AI Foundry portal.
    2) MODEL_DEPLOYMENT_NAME - The deployment name of the AI model, as found under the "Name" column in
       the "Models + endpoints" tab in your Azure AI Foundry project.
    3) MCP_SERVER_URL - The URL of your MCP server endpoint.
    4) MCP_SERVER_LABEL - A label for your MCP server.
"""

import os, time
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import McpTool, RequiredMcpToolCall, SubmitToolApprovalAction, ToolApproval

# Load environment variables from .env file
load_dotenv()

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

project_client = AIProjectClient(
    endpoint=azure_project_endpoint,
    credential=DefaultAzureCredential(),
)

# [START create_agent_with_mcp_tool]
# Initialize agent MCP tool with authentication headers
mcp_tool = McpTool(
    server_label=mcp_server_label,
    server_url=mcp_server_url
)

# Configure authentication headers immediately after tool creation
if mcp_server_token:
    mcp_tool.update_headers("Authorization", f"Bearer {mcp_server_token}")
else:
    print("Warning: No MCP_SERVER_TOKEN found in environment variables")

# Create agent with MCP tool and process agent run
with project_client:
    agents_client = project_client.agents

    # Create a new agent.
    # NOTE: To reuse existing agent, fetch it with get_agent(agent_id)
    agent = agents_client.create_agent(
        model=azure_model_deployment_name,
        name="HomeAssistantMCPAgent",
        instructions=f"""You are a helpful agent that can use MCP tools to assist users. 
        You have access to a Home Assistant MCP server at {mcp_server_url} with label '{mcp_server_label}'.
        Use the available MCP tools to answer questions about home automation, sensor data, and device control.
        When making MCP calls, ensure you use the proper authentication headers that have been configured.""",
        tools=mcp_tool.definitions,
    )
    # [END create_agent_with_mcp_tool]

    print(f"Created agent, ID: {agent.id}")
    print(f"MCP Server: {mcp_tool.server_label} at {mcp_tool.server_url}")

    # Create thread for communication
    thread = agents_client.threads.create()
    print(f"Created thread, ID: {thread.id}")

    # Create message to thread
    message = agents_client.messages.create(
        thread_id=thread.id,
        role="user",
        content="Qué temperatura hace en el salón?",
    )
    print(f"Created message, ID: {message.id}")

    # [START handle_tool_approvals]
    # Create and process agent run in thread with MCP tools
    # Headers were already configured during tool creation
    mcp_tool.set_approval_mode("never")  # Disable approval requirement for smoother operation
    run = agents_client.runs.create(thread_id=thread.id, agent_id=agent.id, tool_resources=mcp_tool.resources)
    print(f"Created run, ID: {run.id}")

    while run.status in ["queued", "in_progress", "requires_action"]:
        time.sleep(1)
        run = agents_client.runs.get(thread_id=thread.id, run_id=run.id)

        if run.status == "requires_action" and isinstance(run.required_action, SubmitToolApprovalAction):
            tool_calls = run.required_action.submit_tool_approval.tool_calls
            if not tool_calls:
                print("No tool calls provided - cancelling run")
                agents_client.runs.cancel(thread_id=thread.id, run_id=run.id)
                break

            tool_approvals = []
            for tool_call in tool_calls:
                if isinstance(tool_call, RequiredMcpToolCall):
                    try:
                        print(f"Approving tool call: {tool_call}")
                        tool_approvals.append(
                            ToolApproval(
                                tool_call_id=tool_call.id,
                                approve=True,
                                headers=mcp_tool.headers,
                            )
                        )
                    except Exception as e:
                        print(f"Error approving tool_call {tool_call.id}: {e}")

            print(f"tool_approvals: {tool_approvals}")
            if tool_approvals:
                agents_client.runs.submit_tool_outputs(
                    thread_id=thread.id, run_id=run.id, tool_approvals=tool_approvals
                )

        print(f"Current run status: {run.status}")
        # [END handle_tool_approvals]

    print(f"Run completed with status: {run.status}")
    if run.status == "failed":
        print(f"Run failed: {run.last_error}")

    # Display run steps and tool calls
    run_steps = agents_client.run_steps.list(thread_id=thread.id, run_id=run.id)

    # Loop through each step
    for step in run_steps:
        print(f"Step {step['id']} status: {step['status']}")

        # Check if there are tool calls in the step details
        step_details = step.get("step_details", {})
        tool_calls = step_details.get("tool_calls", [])

        if tool_calls:
            print("  MCP Tool calls:")
            for call in tool_calls:
                print(f"    Tool Call ID: {call.get('id')}")
                print(f"    Type: {call.get('type')}")

        print()  # add an extra newline between steps

    # Fetch and log all messages
    messages = agents_client.messages.list(thread_id=thread.id)
    print("\nConversation:")
    print("-" * 50)
    for msg in messages:
        if msg.text_messages:
            last_text = msg.text_messages[-1]
            print(f"{msg.role.upper()}: {last_text.text.value}")
            print("-" * 50)

    