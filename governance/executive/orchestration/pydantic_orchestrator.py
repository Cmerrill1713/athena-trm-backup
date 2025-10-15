#!/usr/bin/env python3
"""
Pydantic AI MCP Orchestrator
Master agent that coordinates all MCP tool servers
"""
import os

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

# Configure MCP servers to orchestrate
MCP_SERVERS = [
    MCPServerStdio(
        command='python',
        args=['/mcp/python_servers/youtube_server.py'],
        tool_prefix='youtube'
    ),
    MCPServerStdio(
        command='python',
        args=['/mcp/python_servers/research_server.py'],
        tool_prefix='research'
    ),
    MCPServerStdio(
        command='python',
        args=['/mcp/python_servers/web_server.py'],
        tool_prefix='web'
    ),
    MCPServerStdio(
        command='python',
        args=['/mcp/python_servers/store_client.py'],
        tool_prefix='store'
    ),
]

# Create orchestrator agent
orchestrator = Agent(
    model=os.getenv('OPENAI_MODEL', 'openai:gpt-4'),
    mcp_servers=MCP_SERVERS,
    system_prompt="""You are the MCP Ecosystem Orchestrator.

You have access to multiple tool categories:
- youtube_* tools for fetching video transcripts and metadata
- research_* tools for academic papers (arXiv) and knowledge (Wikipedia)
- web_* tools for web search and scraping
- store_* tools for storing results

Coordinate these tools to accomplish complex research and analysis tasks."""
)

# Add orchestrator-specific tools
@orchestrator.tool()
async def ecosystem_status() -> dict:
    """Get status of all MCP servers in the ecosystem."""
    servers_status = []
    for server in MCP_SERVERS:
        try:
            tools = await server.list_tools()
            servers_status.append({
                "prefix": server.tool_prefix,
                "running": server.is_running,
                "tools_count": len(tools)
            })
        except Exception as e:
            servers_status.append({
                "prefix": server.tool_prefix,
                "running": False,
                "error": str(e)
            })

    return {
        "servers": servers_status,
        "total_servers": len(MCP_SERVERS),
        "healthy": sum(1 for s in servers_status if s.get("running"))
    }

@orchestrator.tool()
async def multi_source_research(topic: str, sources: str = "all") -> dict:
    """
    Research a topic across multiple sources simultaneously.
    
    Args:
        topic: Topic to research
        sources: Comma-separated sources or 'all' (arxiv,wikipedia,web,youtube)
    
    Returns:
        dict: Combined research from all requested sources
    """
    source_list = sources.split(",") if sources != "all" else ["arxiv", "wikipedia", "web"]
    results = {}

    # This would dispatch to multiple MCP servers
    # The orchestrator handles this automatically via its MCP servers
    return {
        "topic": topic,
        "sources_requested": source_list,
        "note": "Use research_* and web_* tools directly for actual queries"
    }

if __name__ == "__main__":
    import asyncio

    # Example: Run orchestrator
    async def main():
        # The orchestrator can now use all tools from all servers
        result = await orchestrator.run(
            "What is the current state of research on quantum computing?"
        )
        print(result.data)

    asyncio.run(main())

