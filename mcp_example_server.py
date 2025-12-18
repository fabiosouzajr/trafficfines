#!/usr/bin/env python3
"""
Example MCP Server for Traffic Fines ETL

This demonstrates how to create a custom MCP server that can be added to Cursor.
The server exposes tools that the AI assistant can use.
"""

import json
import sys
from typing import Any, Dict, List, Optional
from pathlib import Path


class MCPServer:
    """
    A simple MCP server implementation.
    
    In a real implementation, you would use the official MCP SDK,
    but this shows the basic structure.
    """
    
    def __init__(self):
        self.tools = {
            "get_fine_count": {
                "name": "get_fine_count",
                "description": "Get the total count of traffic fines in the database",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            "search_fines": {
                "name": "search_fines",
                "description": "Search for traffic fines by license plate or fine number",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search term (license plate or fine number)"
                        }
                    },
                    "required": ["query"]
                }
            },
            "get_pdf_info": {
                "name": "get_pdf_info",
                "description": "Get information about a PDF file in the fines folder",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pdf_path": {
                            "type": "string",
                            "description": "Path to the PDF file"
                        }
                    },
                    "required": ["pdf_path"]
                }
            }
        }
    
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an MCP request."""
        method = request.get("method")
        params = request.get("params", {})
        
        if method == "tools/list":
            return {
                "tools": list(self.tools.values())
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name == "get_fine_count":
                return self._get_fine_count()
            elif tool_name == "search_fines":
                return self._search_fines(arguments.get("query", ""))
            elif tool_name == "get_pdf_info":
                return self._get_pdf_info(arguments.get("pdf_path", ""))
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        
        return {"error": f"Unknown method: {method}"}
    
    def _get_fine_count(self) -> Dict[str, Any]:
        """Implementation of get_fine_count tool."""
        # This would connect to your database
        # For example:
        # from trafficfines.db.models import FineModel
        # model = FineModel()
        # count = len(model.get_all_fines())
        
        return {
            "content": [{
                "type": "text",
                "text": "Total fines: 0 (example - implement database connection)"
            }]
        }
    
    def _search_fines(self, query: str) -> Dict[str, Any]:
        """Implementation of search_fines tool."""
        # This would search your database
        return {
            "content": [{
                "type": "text",
                "text": f"Search results for '{query}': (implement database search)"
            }]
        }
    
    def _get_pdf_info(self, pdf_path: str) -> Dict[str, Any]:
        """Implementation of get_pdf_info tool."""
        path = Path(pdf_path)
        if path.exists():
            return {
                "content": [{
                    "type": "text",
                    "text": f"PDF: {path.name}\nSize: {path.stat().st_size} bytes\nExists: True"
                }]
            }
        return {
            "content": [{
                "type": "text",
                "text": f"PDF not found: {pdf_path}"
            }]
        }


def main():
    """Main entry point for the MCP server (stdio transport)."""
    server = MCPServer()
    
    # Read from stdin, write to stdout (stdio transport)
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            response = server.handle_request(request)
            print(json.dumps(response))
            sys.stdout.flush()
        except json.JSONDecodeError:
            continue
        except Exception as e:
            error_response = {"error": str(e)}
            print(json.dumps(error_response))
            sys.stdout.flush()


if __name__ == "__main__":
    main()
