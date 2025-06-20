# Consul MCP Server

A Model Control Protocol (MCP) server for interacting with HashiCorp Consul service discovery and service mesh. This implementation follows Anthropic's MCP specification and allows Claude to analyze your microservices architecture, create diagrams, identify issues, and provide recommendations through natural language interaction.

## What is Model Control Protocol?

Model Control Protocol (MCP) is a specification developed by Anthropic that enables AI models like Claude to interact with external tools and APIs. This implementation connects AI Agents to your Consul infrastructure, allowing you to manage and analyze your services using natural language.

## Features

- List and analyze services registered in Consul 
- Identify and diagnose failing health checks

## Requirements

- Node.js 18+
- uv
- python
- A running Consul instance (local or remote)
- Claude Desktop or Cursor IDE with Claude integration

## Installation
- Clone consul mcp repository
    ```angular2html
    git clone https://github.com/kswap/consul-mcp.git
    cd consul-mcp
    ```
- Install uv
    ```
    Install from [uv documentation](https://docs.astral.sh/uv/getting-started/installation/).
  ```
- Install node
    ```
    Install from: [nodejs](https://nodejs.org) or using a package manager
  ```
- Setup virtual environment
    ```
    uv venv && uv sync
    source .venv/bin/activate
    export PYTHONPATH=.
  ```
- Run Server
    ```angular2html
    python src/server/main.py
    ```

  - Integrate with Claude desktop 
    1. In Claude Desktop, open Settings (⌘+,) and navigate to the "Developer" tab. 
    2. Click "Edit Config" at the bottom of the window. 
    3. Edit the file (~/Library/Application Support/Claude/claude_desktop_config.json) to add code similar to the following, then Save the file.
          ```
        {
            "mcpServers": {
              "consul_mcp": {
                "command": "/opt/homebrew/bin/uv",
                "args": [
                  "run",
                  "--with",
                  "mcp[cli]",
                  "mcp",
                  "run",
                  "/absolute/path/to/main.py" 
                ],
                "env": {
                  "PYTHONPATH": "/absolute/path/to/consul-mcp"
                }
              }
            }
          }
        ```
    4. Restart Claude Desktop to ensure the MCP server is properly loaded.

## Example Prompts

Once connected, try these prompts with Claude:

- "Show me all services registered in Consul"
- "Which services have failing health checks?"

## Contributing

Contributions are welcome! Please feel free to submit a pull request.