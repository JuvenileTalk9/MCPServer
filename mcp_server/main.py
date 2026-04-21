import argparse
from dotenv import load_dotenv

load_dotenv()

from server import mcp  # noqa: E402

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MCP Server")
    parser.add_argument(
        "--transport",
        type=str,
        default="stdio",
        choices=["stdio", "streamable-http"],
        help="Transport method (stdio or streamable-http)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Port number (default: 8765)",
    )
    args = parser.parse_args()

    if args.transport == "streamable-http":
        print(
            f"Starting MCP server with streamable HTTP transport on port {args.port}..."
        )
        import uvicorn

        app = mcp.streamable_http_app()
        uvicorn.run(app, host="127.0.0.1", port=args.port)
    else:
        print("Starting MCP server with stdio transport...")
        mcp.run(transport="stdio")
