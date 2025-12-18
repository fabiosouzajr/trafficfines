# MCP (Model Context Protocol) Implementation Guide

## What is MCP?

**Model Context Protocol (MCP)** is a standardized protocol that allows AI assistants to interact with external tools, services, and data sources. In Cursor, you can add custom MCP servers to extend the AI's capabilities.

## Key Concepts

### MCP Server
An application that exposes tools and resources that the AI can use. It communicates via:
- **stdio** (standard input/output) - most common
- **SSE** (Server-Sent Events) - for web-based servers
- **HTTP** - for REST APIs

### Tools
Functions that the AI can call. Each tool has:
- A name
- A description (what it does)
- Parameters (inputs it accepts)
- Implementation (the actual code that runs)

### Resources
Data sources the AI can read from (files, databases, APIs, etc.)

## How to Add an MCP Server to Cursor

### Step 1: Create Your MCP Server

You can create an MCP server in any language. Here are the main approaches:

#### Option A: Using the Official MCP Python SDK (Recommended)

```bash
pip install mcp
```

```python
# mcp_server.py
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

app = Server("traffic-fines-server")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_fine_count",
            description="Get total count of traffic fines",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="search_fines",
            description="Search fines by license plate or number",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search term"
                    }
                },
                "required": ["query"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "get_fine_count":
        # Your implementation
        from trafficfines.db.models import FineModel
        model = FineModel()
        count = len(model.get_all_fines())
        return [TextContent(type="text", text=str(count))]
    
    elif name == "search_fines":
        query = arguments.get("query", "")
        # Your search implementation
        return [TextContent(type="text", text=f"Searching for: {query}")]
    
    raise ValueError(f"Unknown tool: {name}")

if __name__ == "__main__":
    stdio_server(app).run()
```

#### Option B: Manual Implementation (stdio)

See `mcp_example_server.py` for a basic example that reads JSON from stdin and writes JSON to stdout.

### Step 2: Configure in Cursor

1. Open Cursor Settings
2. Go to **Tools & MCP** section
3. Click **Add Custom MCP Tool**
4. Fill in the configuration:

```json
{
  "name": "Traffic Fines Server",
  "command": "python",
  "args": ["/absolute/path/to/mcp_server.py"],
  "env": {}
}
```

Or for a more complete example:

```json
{
  "name": "Traffic Fines ETL",
  "command": "python",
  "args": [
    "/home/fabio/.cursor/worktrees/trafficfines/etl/mcp_example_server.py"
  ],
  "env": {
    "PYTHONPATH": "/home/fabio/.cursor/worktrees/trafficfines/etl/src"
  }
}
```

### Step 3: Test Your Server

After adding the server, restart Cursor. The AI assistant should now be able to use your custom tools.

## Common Use Cases

### 1. Database Access
Expose database queries as tools:
- `get_fine_by_number(fine_number)`
- `get_fines_by_date_range(start_date, end_date)`
- `get_unpaid_fines()`

### 2. File System Operations
Tools for working with files:
- `list_pdf_files(folder_path)`
- `parse_pdf(pdf_path)`
- `validate_pdf_structure(pdf_path)`

### 3. API Integration
Connect to external services:
- `check_fine_status(fine_number)` - query government API
- `send_notification(fine_id)` - send email/SMS
- `sync_with_calendar()` - Google Calendar operations

### 4. Data Processing
ETL-specific tools:
- `extract_pdf_data(pdf_path)`
- `transform_fine_data(raw_data)`
- `load_to_database(fine_data)`

## Best Practices

### 1. Error Handling
Always return meaningful error messages:

```python
try:
    result = perform_operation()
    return [TextContent(type="text", text=str(result))]
except Exception as e:
    return [TextContent(type="text", text=f"Error: {str(e)}")]
```

### 2. Tool Descriptions
Write clear, detailed descriptions so the AI knows when to use each tool:

```python
Tool(
    name="search_fines",
    description="Search for traffic fines by license plate (e.g., 'ABC1234') or fine number. Returns matching fine records with all details including dates, amounts, and violation information.",
    inputSchema={...}
)
```

### 3. Parameter Validation
Validate inputs before processing:

```python
def call_tool(name: str, arguments: dict):
    if name == "search_fines":
        query = arguments.get("query", "")
        if not query or len(query) < 3:
            raise ValueError("Query must be at least 3 characters")
        # ... rest of implementation
```

### 4. Security
- Never expose sensitive operations without authentication
- Validate all inputs
- Don't allow arbitrary code execution
- Use environment variables for secrets

## Example: Complete Traffic Fines MCP Server

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from trafficfines.db.models import FineModel
from trafficfines.pdf.parser import PDFParser

app = Server("traffic-fines-mcp")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_fine_count",
            description="Get the total number of traffic fines in the database",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="get_fine_by_number",
            description="Retrieve a specific fine by its fine number",
            inputSchema={
                "type": "object",
                "properties": {
                    "fine_number": {
                        "type": "string",
                        "description": "The fine number (AIT number)"
                    }
                },
                "required": ["fine_number"]
            }
        ),
        Tool(
            name="parse_pdf",
            description="Parse a traffic fine PDF and extract structured data",
            inputSchema={
                "type": "object",
                "properties": {
                    "pdf_path": {
                        "type": "string",
                        "description": "Absolute path to the PDF file"
                    }
                },
                "required": ["pdf_path"]
            }
        ),
        Tool(
            name="get_unpaid_fines",
            description="Get all fines that haven't been paid yet",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "get_fine_count":
            model = FineModel()
            fines = model.get_all_fines()
            return [TextContent(type="text", text=f"Total fines: {len(fines)}")]
        
        elif name == "get_fine_by_number":
            fine_number = arguments.get("fine_number")
            model = FineModel()
            fine = model.get_fine_by_number(fine_number)
            if fine:
                return [TextContent(type="text", text=str(fine))]
            return [TextContent(type="text", text=f"No fine found with number: {fine_number}")]
        
        elif name == "parse_pdf":
            pdf_path = arguments.get("pdf_path")
            parser = PDFParser()
            result = parser.parse_pdf(pdf_path)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "get_unpaid_fines":
            model = FineModel()
            unpaid = model.get_fines_without_payment_events()
            return [TextContent(type="text", text=f"Unpaid fines: {len(unpaid)}")]
        
        raise ValueError(f"Unknown tool: {name}")
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

if __name__ == "__main__":
    stdio_server(app).run()
```

## Testing Your MCP Server

You can test your server manually:

```bash
# Test tool listing
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}' | python mcp_server.py

# Test tool call
echo '{"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "get_fine_count", "arguments": {}}}' | python mcp_server.py
```

## Resources

- [MCP Specification](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Examples](https://github.com/modelcontextprotocol/servers)

## Troubleshooting

### Server not starting
- Check that the command path is absolute
- Verify Python environment and dependencies
- Check Cursor's logs for error messages

### Tools not appearing
- Ensure `list_tools()` returns valid Tool objects
- Check that the server is running (stdio communication)
- Restart Cursor after adding the server

### Tool calls failing
- Validate parameter types match the schema
- Check error handling in your implementation
- Verify all dependencies are available
