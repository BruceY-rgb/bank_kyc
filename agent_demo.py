"""
KYC Document Processing Agent Demo

This demo shows how to set up a basic Claude Agent for processing KYC documents.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

# Load environment variables from .env file
load_dotenv()


def setup_kyc_agent():
    """
    Set up a Claude Agent for KYC document processing.

    The agent is configured with:
    - Read: Read files and documents
    - Write: Create or update files
    - Bash: Execute shell commands
    - Grep: Search for content in files
    - Glob: Find files by pattern
    """

    # Get the KYC documents directory path
    kyc_docs_path = Path(__file__).parent / "kyc_documents"

    # Configure the agent options
    options = ClaudeAgentOptions(
        # Allow specific tools for document processing
        allowed_tools=["Read", "Write", "Bash", "Grep", "Glob","Search"],

        # Automatically accept file edits (use with caution in production)
        permission_mode='acceptEdits',

        # Set working directory to KYC documents folder
        cwd=str(kyc_docs_path.absolute()),

        # Optional: Load project settings from .claude directory
        # setting_sources=["project"],
    )

    # Create the Claude SDK client
    client = ClaudeSDKClient(options=options)

    return client


def example_usage():
    """
    Example: Using the agent to process KYC documents.
    """

    # Initialize the agent
    agent = setup_kyc_agent()

    print("KYC Agent initialized successfully!")
    print(f"Working directory: {agent.options.cwd}")
    print(f"Allowed tools: {agent.options.allowed_tools}")

    # Example query to the agent
    # Uncomment to test:
    # response = agent.query("List all PDF files in the current directory")
    # print(f"\nAgent response: {response}")

    # For interactive multi-turn conversations, use agent.chat()
    # Example:
    # agent.chat("Please analyze the ID documents in this folder")


if __name__ == "__main__":
    # Check if API key is set
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Warning: ANTHROPIC_API_KEY not found in environment variables")
        print("Please set it in your .env file or environment")
    else:
        example_usage()
