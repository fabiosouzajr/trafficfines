# MCP Quick Start Guide

## What You Can Do With MCP

Once set up, the AI assistant in Cursor will be able to:
- Query your traffic fines database
- Search for fines by license plate or fine number
- Parse PDF files
- Check which fines need reminders
- Get statistics about your fines

## Setup Steps

### 1. Install MCP SDK

```bash
pip install mcp
```

Or add to `requirements.txt`:
```
mcp
```

### 2. Get the Absolute Path to Your Server

```bash
# From the project root
realpath mcp_traffic_fines_server.py
```

Or in Python:
```python
from pathlib import Path
print(Path(__file__).parent.absolute() / "mcp_traffic_fines_server.py")
```

### 3. Add to Cursor Settings

1. Open Cursor Settings (Ctrl+, or Cmd+,)
2. Navigate to **Tools & MCP** section
3. Click **Add Custom MCP Tool** or **+** button
4. Enter the configuration:

**Option A: Simple Configuration**
```json
{
  "name": "Traffic Fines ETL",
  "command": "python",
  "args": ["/home/fabio/.cursor/worktrees/trafficfines/etl/mcp_traffic_fines_server.py"]
}
```

**Option B: With Environment Variables**
```json
{
  "name": "Traffic Fines ETL",
  "command": "python",
  "args": ["/home/fabio/.cursor/worktrees/trafficfines/etl/mcp_traffic_fines_server.py"],
  "env": {
    "PYTHONPATH": "/home/fabio/.cursor/worktrees/trafficfines/etl/src"
  }
}
```

**Important**: Replace the path with your actual absolute path!

### 4. Restart Cursor

Close and reopen Cursor for the MCP server to be loaded.

### 5. Test It

Once restarted, you can ask the AI:
- "How many fines are in the database?"
- "Search for fines with license plate ABC1234"
- "What fines need payment reminders?"
- "Parse the PDF at /path/to/fine.pdf"

## Available Tools

After setup, these tools will be available:

1. **get_fine_count** - Get total number of fines
2. **get_fine_by_number** - Get a specific fine by its number
3. **search_fines_by_plate** - Search fines by license plate
4. **parse_pdf** - Parse a traffic fine PDF
5. **get_unpaid_fines** - Get fines needing payment reminders
6. **get_fines_needing_driver_id** - Get fines needing driver ID reminders
7. **get_all_fines** - Get all fines (with optional limit)

## Troubleshooting

### "MCP SDK not installed"
```bash
pip install mcp
```

### "Error importing application modules"
- Make sure you're using the absolute path to the server script
- Check that `src/trafficfines` is in the Python path
- Verify your database exists and is accessible

### Server not starting
- Check Cursor's logs (Help > Toggle Developer Tools > Console)
- Verify the Python path is correct
- Make sure the script is executable: `chmod +x mcp_traffic_fines_server.py`

### Tools not appearing
- Restart Cursor completely
- Check that the server starts without errors
- Verify the JSON configuration is valid

## Example Usage

Once configured, you can have conversations like:

**You**: "How many traffic fines do I have?"
**AI**: *[Uses get_fine_count tool]* "You have 15 fines in the database."

**You**: "Show me all fines for license plate XYZ9876"
**AI**: *[Uses search_fines_by_plate tool]* "Found 3 fines for XYZ9876: ..."

**You**: "What fines need payment reminders?"
**AI**: *[Uses get_unpaid_fines tool]* "You have 5 fines that need payment reminders: ..."

## Next Steps

- Customize the tools in `mcp_traffic_fines_server.py` to add more functionality
- Add tools for Google Calendar integration
- Add tools for PDF batch processing
- Add tools for data export/import

See `MCP_IMPLEMENTATION_GUIDE.md` for more advanced usage.
