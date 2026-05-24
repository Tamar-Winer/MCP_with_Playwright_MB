from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPClient:
    """Generic MCP client that connects to a single MCP server via stdio."""

    def __init__(self):
        self.session: ClientSession | None = None
        self.exit_stack = AsyncExitStack()
        self.tools: list = []
        self.server_name: str = ""

    async def connect(self, server_script: str) -> "MCPClient":
        self.server_name = server_script

        server_params = StdioServerParameters(
            command="uv",
            args=["run", server_script],
        )

        transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        read, write = transport

        self.session = await self.exit_stack.enter_async_context(
            ClientSession(read, write)
        )

        await self.session.initialize()

        response = await self.session.list_tools()
        self.tools = response.tools

        print(f"[MCP] Connected to '{server_script}' — tools: {[t.name for t in self.tools]}")
        return self

    async def call_tool(self, name: str, arguments: dict):
        return await self.session.call_tool(name, arguments)

    async def cleanup(self):
        await self.exit_stack.aclose()
