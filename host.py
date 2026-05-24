import asyncio
import os
from dotenv import load_dotenv
from anthropic import Anthropic
from client import MCPClient

load_dotenv()

MCP_SERVERS = [
    "weather_USA.py",
    "weather_Israel.py",
]

SYSTEM_PROMPT = """You are a helpful weather assistant. You have access to tools that let you:
1. Fetch weather forecasts for US cities via the NWS API.
2. Control a browser to retrieve Israeli weather forecasts from weather2day.co.il.

When the user asks about Israeli weather:
- Call open_weather_forecast_israel to open the browser.
- Call enter_weather_forecast_city_israel with the city name.
- Call select_weather_forecast_city_israel to pick the first result.
- Call get_weather_forecast_content_israel to read the page and answer the question.

When the user asks about US weather:
- Call get_weather_usa with the city name.

Always answer in the same language the user used."""


class Host:
    def __init__(self):
        self.clients: list[MCPClient] = []
        self.tool_to_client: dict[str, MCPClient] = {}
        self.anthropic = Anthropic()
        self.history: list[dict] = []

    async def setup(self):
        for script in MCP_SERVERS:
            client = MCPClient()
            await client.connect(script)
            self.clients.append(client)
            for tool in client.tools:
                self.tool_to_client[tool.name] = client

    def _claude_tools(self) -> list[dict]:
        tools = []
        for client in self.clients:
            for tool in client.tools:
                tools.append(
                    {
                        "name": tool.name,
                        "description": tool.description or "",
                        "input_schema": tool.inputSchema,
                    }
                )
        return tools

    async def _process(self, user_input: str) -> str:
        self.history.append({"role": "user", "content": user_input})

        while True:
            response = self.anthropic.messages.create(
                model="claude-opus-4-5",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=self._claude_tools(),
                messages=self.history,
            )

            if response.stop_reason == "end_turn":
                text = "".join(
                    block.text for block in response.content if hasattr(block, "text")
                )
                self.history.append({"role": "assistant", "content": response.content})
                return text

            # stop_reason == "tool_use"
            self.history.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue

                print(f"  → calling tool: {block.name}({block.input})")
                client = self.tool_to_client[block.name]
                result = await client.call_tool(block.name, block.input)

                content_text = "".join(
                    c.text for c in result.content if hasattr(c, "text")
                )
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": content_text,
                    }
                )

            self.history.append({"role": "user", "content": tool_results})

    async def run(self):
        print("=" * 55)
        print("  Weather MCP Chat — Israel 🇮🇱  &  USA 🇺🇸")
        print("  Type 'quit' to exit.")
        print("=" * 55)
        print()

        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break

            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit", "q"):
                print("Goodbye!")
                break

            print("\nAssistant: ", end="", flush=True)
            answer = await self._process(user_input)
            print(answer)
            print()

    async def cleanup(self):
        for client in self.clients:
            await client.cleanup()


async def main():
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable is not set.")
        return

    host = Host()
    await host.setup()
    try:
        await host.run()
    finally:
        await host.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
