import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class GmailMCPClient:
    def __init__(self, server_script_path: str):
        self.server_params = StdioServerParameters(
            command="python",
            args=[server_script_path],
            env=None
        )

    async def create_draft(self, to_email: str, subject: str, body_html: str):
        """
        Connects to the Gmail MCP server and creates a draft.
        """
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                result = await session.call_tool(
                    "create_pulse_draft",
                    arguments={
                        "to_email": to_email,
                        "subject": subject,
                        "body_html": body_html
                    }
                )
                return result

async def test_client():
    client = GmailMCPClient("phase_5/server.py")
    # result = await client.create_draft("stakeholder@example.com", "Groww Weekly Pulse", "<h1>Test</h1>")
    # print(result)
    print("Gmail MCP Client configured and ready to connect to phase_5/server.py")

if __name__ == "__main__":
    asyncio.run(test_client())
