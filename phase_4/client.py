import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class DocsMCPClient:
    def __init__(self, server_script_path: str):
        self.server_params = StdioServerParameters(
            command="python",
            args=[server_script_path],
            env=None
        )

    async def append_report(self, document_id: str, week_label: str, markdown_content: str):
        """
        Connects to the Docs MCP server and appends the report.
        """
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                await session.initialize()
                
                # Call the 'append_to_document' tool
                result = await session.call_tool(
                    "append_to_document",
                    arguments={
                        "document_id": document_id,
                        "heading_text": week_label,
                        "content_markdown": markdown_content
                    }
                )
                return result

async def test_client():
    client = DocsMCPClient("phase_4/server.py")
    # Replace with a real Doc ID for testing
    # result = await client.append_report("YOUR_DOC_ID", "Week 19 - 2026", "This is a test report content.")
    # print(result)
    print("Client configured and ready to connect to phase_4/server.py")

if __name__ == "__main__":
    asyncio.run(test_client())
