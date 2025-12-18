#!/usr/bin/env python3
"""
MCP Server for Traffic Fines ETL

This server exposes tools that allow the AI assistant to interact with
your traffic fines database and PDF processing functionality.

To use this in Cursor:
1. Install MCP SDK: pip install mcp
2. Add to Cursor Settings > Tools & MCP:
   {
     "name": "Traffic Fines",
     "command": "python",
     "args": ["/absolute/path/to/mcp_traffic_fines_server.py"]
   }
3. Restart Cursor
"""

import sys
import json
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("Error: MCP SDK not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

# Import your application modules
try:
    from trafficfines.db.models import FineModel
    from trafficfines.pdf.parser import PDFParser
except ImportError as e:
    print(f"Error importing application modules: {e}", file=sys.stderr)
    print("Make sure you're running from the project root", file=sys.stderr)
    sys.exit(1)

app = Server("traffic-fines-etl")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools."""
    return [
        Tool(
            name="get_fine_count",
            description="Get the total number of traffic fines stored in the database",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_fine_by_number",
            description="Retrieve a specific traffic fine by its fine number (AIT number). Returns all fine details including dates, amounts, and violation information.",
            inputSchema={
                "type": "object",
                "properties": {
                    "fine_number": {
                        "type": "string",
                        "description": "The fine number (AIT number) to search for"
                    }
                },
                "required": ["fine_number"]
            }
        ),
        Tool(
            name="search_fines_by_plate",
            description="Search for traffic fines by license plate. Returns all fines associated with that license plate.",
            inputSchema={
                "type": "object",
                "properties": {
                    "license_plate": {
                        "type": "string",
                        "description": "License plate to search for (e.g., 'ABC1234')"
                    }
                },
                "required": ["license_plate"]
            }
        ),
        Tool(
            name="parse_pdf",
            description="Parse a traffic fine PDF file and extract structured data. Returns a JSON object with all extracted fine information.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pdf_path": {
                        "type": "string",
                        "description": "Absolute or relative path to the PDF file"
                    }
                },
                "required": ["pdf_path"]
            }
        ),
        Tool(
            name="get_unpaid_fines",
            description="Get all fines that haven't had payment reminder events created in Google Calendar",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_fines_needing_driver_id",
            description="Get all fines that need driver ID reminder events created",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_all_fines",
            description="Get all traffic fines from the database, ordered by violation date",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of fines to return (optional)",
                        "minimum": 1,
                        "maximum": 1000
                    }
                }
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    try:
        model = FineModel()
        
        if name == "get_fine_count":
            fines = model.get_all_fines()
            return [TextContent(
                type="text",
                text=f"Total fines in database: {len(fines)}"
            )]
        
        elif name == "get_fine_by_number":
            fine_number = arguments.get("fine_number", "").strip()
            if not fine_number:
                return [TextContent(type="text", text="Error: fine_number is required")]
            
            fine = model.get_fine_by_number(fine_number)
            if fine:
                # Format fine data nicely
                fine_dict = {
                    "fine_number": fine.fine_number,
                    "license_plate": fine.license_plate,
                    "violation_date": fine.violation_date,
                    "amount": fine.amount,
                    "description": fine.description,
                    "violation_location": fine.violation_location
                }
                return [TextContent(
                    type="text",
                    text=json.dumps(fine_dict, indent=2, default=str)
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"No fine found with number: {fine_number}"
                )]
        
        elif name == "search_fines_by_plate":
            license_plate = arguments.get("license_plate", "").strip().upper()
            if not license_plate:
                return [TextContent(type="text", text="Error: license_plate is required")]
            
            all_fines = model.get_all_fines()
            matching_fines = [f for f in all_fines if f.license_plate == license_plate]
            
            if matching_fines:
                result = []
                for fine in matching_fines:
                    result.append({
                        "fine_number": fine.fine_number,
                        "violation_date": fine.violation_date,
                        "amount": fine.amount,
                        "description": fine.description
                    })
                return [TextContent(
                    type="text",
                    text=f"Found {len(matching_fines)} fine(s) for plate {license_plate}:\n\n" +
                         json.dumps(result, indent=2, default=str)
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"No fines found for license plate: {license_plate}"
                )]
        
        elif name == "parse_pdf":
            pdf_path = arguments.get("pdf_path", "").strip()
            if not pdf_path:
                return [TextContent(type="text", text="Error: pdf_path is required")]
            
            # Resolve path (handle relative paths)
            path = Path(pdf_path)
            if not path.is_absolute():
                path = project_root / path
            
            if not path.exists():
                return [TextContent(
                    type="text",
                    text=f"Error: PDF file not found: {path}"
                )]
            
            try:
                parser = PDFParser()
                result = parser.parse_pdf(str(path), validate=False)
                return [TextContent(
                    type="text",
                    text=json.dumps(result, indent=2, default=str)
                )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Error parsing PDF: {str(e)}"
                )]
        
        elif name == "get_unpaid_fines":
            unpaid = model.get_fines_without_payment_events()
            if unpaid:
                result = []
                for fine in unpaid:
                    result.append({
                        "fine_number": fine.fine_number,
                        "license_plate": fine.license_plate,
                        "amount": fine.amount,
                        "defense_due_date": fine.defense_due_date
                    })
                return [TextContent(
                    type="text",
                    text=f"Found {len(unpaid)} unpaid fine(s):\n\n" +
                         json.dumps(result, indent=2, default=str)
                )]
            else:
                return [TextContent(
                    type="text",
                    text="No unpaid fines found"
                )]
        
        elif name == "get_fines_needing_driver_id":
            needing_id = model.get_fines_without_driver_id_events()
            if needing_id:
                result = []
                for fine in needing_id:
                    result.append({
                        "fine_number": fine.fine_number,
                        "license_plate": fine.license_plate,
                        "driver_id_due_date": fine.driver_id_due_date
                    })
                return [TextContent(
                    type="text",
                    text=f"Found {len(needing_id)} fine(s) needing driver ID reminders:\n\n" +
                         json.dumps(result, indent=2, default=str)
                )]
            else:
                return [TextContent(
                    type="text",
                    text="No fines need driver ID reminders"
                )]
        
        elif name == "get_all_fines":
            limit = arguments.get("limit")
            all_fines = model.get_all_fines()
            
            if limit:
                all_fines = all_fines[:limit]
            
            result = []
            for fine in all_fines:
                result.append({
                    "fine_number": fine.fine_number,
                    "license_plate": fine.license_plate,
                    "violation_date": fine.violation_date,
                    "amount": fine.amount,
                    "description": fine.description
                })
            
            return [TextContent(
                type="text",
                text=f"Total: {len(result)} fine(s)\n\n" +
                     json.dumps(result, indent=2, default=str)
            )]
        
        else:
            return [TextContent(
                type="text",
                text=f"Error: Unknown tool: {name}"
            )]
    
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error executing tool '{name}': {str(e)}"
        )]


if __name__ == "__main__":
    stdio_server(app).run()
