from mcp.server.fastmcp import FastMCP

mcp = FastMCP("multi-domain-mcp-server")


from domains.book.tools import register as register_book_tools  # noqa: E402
from domains.weather.tools import register as register_weather_tools  # noqa: E402

register_book_tools(mcp)
register_weather_tools(mcp)
