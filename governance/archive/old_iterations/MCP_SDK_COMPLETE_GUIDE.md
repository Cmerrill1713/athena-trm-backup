# 🌐 Complete MCP SDK Guide - Top 10 Languages

**Version:** 1.0.0  
**Date:** October 13, 2025  
**Spec:** [Model Context Protocol Official](https://modelcontextprotocol.io)

## 📚 Table of Contents

1. [Anthropic's MCP Specification](#anthropics-mcp-specification)
2. [Top 10 Language SDKs](#top-10-language-sdks)
3. [SDK Comparison Matrix](#sdk-comparison-matrix)
4. [Build & Usage Patterns](#build--usage-patterns)
5. [Cross-SDK Integration](#cross-sdk-integration)
6. [Agent Understanding Guide](#agent-understanding-guide)

---

## 🎯 Anthropic's MCP Specification

### Official Anthropic MCP Integration

Anthropic is the **creator of the Model Context Protocol** and provides first-class support through:

**Source:** https://github.com/modelcontextprotocol
**Docs:** https://modelcontextprotocol.io

### Core Specifications

#### 1. **Transport Protocols** (3 types)

**stdio (Standard Input/Output)**
```json
{
  "command": "python",
  "args": ["server.py"],
  "env": {"KEY": "value"}
}
```
- Most common
- Process-based
- Used by Claude Desktop

**HTTP + SSE (Server-Sent Events)**
```json
{
  "url": "http://localhost:8080/sse",
  "headers": {"Authorization": "Bearer token"}
}
```
- HTTP-based
- Real-time updates
- Network-friendly

**Streamable HTTP** (New in 2024)
```json
{
  "url": "http://localhost:8080",
  "method": "POST"
}
```
- Latest protocol
- Bidirectional streaming
- Best performance

#### 2. **Message Format**

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "tool_name",
    "arguments": {"key": "value"}
  },
  "id": 1
}
```

#### 3. **Tool Definition**

```json
{
  "name": "my_tool",
  "description": "What the tool does",
  "inputSchema": {
    "type": "object",
    "properties": {
      "param": {"type": "string", "description": "Parameter description"}
    },
    "required": ["param"]
  }
}
```

---

## 🔝 Top 10 Language SDKs

### 1. **Python** ⭐⭐⭐ (PRIMARY)

**Official SDK:** `mcp` + `pydantic-ai[mcp]`  
**Stars:** 69,752  
**Maturity:** Production-ready  
**Anthropic Support:** ✅ Native

#### Installation
```bash
# Official MCP SDK
pip install mcp

# Pydantic AI with MCP
pip install "pydantic-ai-slim[mcp]"

# Anthropic's model
pip install "pydantic-ai-slim[anthropic]"
```

#### Build a Server
```python
from mcp.server.fastmcp import FastMCP, tool

mcp = FastMCP("my-server")

@tool()
def my_tool(param: str) -> dict:
    """Tool description for Claude/agents."""
    return {"result": param}

if __name__ == "__main__":
    mcp.run()
```

#### Build a Client (Pydantic AI)
```python
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

agent = Agent(
    'anthropic:claude-3-5-sonnet-latest',  # Anthropic model!
    mcp_servers=[
        MCPServerStdio(command='python', args=['server.py'])
    ]
)

result = await agent.run("Use the MCP tools to...")
```

#### Patterns
- ✅ Use FastMCP for simple servers
- ✅ Use Pydantic AI for agent orchestration
- ✅ Use Anthropic models for best MCP support
- ✅ Async/await for scalability

---

### 2. **TypeScript/JavaScript** ⭐⭐⭐

**Official SDK:** `@modelcontextprotocol/sdk`  
**Package:** [@modelcontextprotocol/sdk on npm](https://www.npmjs.com/package/@modelcontextprotocol/sdk)  
**Maturity:** Production-ready  
**Anthropic Support:** ✅ Official

#### Installation
```bash
npm install @modelcontextprotocol/sdk
```

#### Build a Server
```typescript
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';

const server = new Server({
  name: 'my-mcp-server',
  version: '1.0.0'
}, {
  capabilities: { tools: {} }
});

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [{
    name: 'my_tool',
    description: 'Tool description',
    inputSchema: {
      type: 'object',
      properties: {
        param: { type: 'string' }
      }
    }
  }]
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  // Handle tool call
  return {
    content: [{ type: 'text', text: 'result' }]
  };
});

const transport = new StdioServerTransport();
await server.connect(transport);
```

#### Build a Client
```typescript
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';

const transport = new StdioClientTransport({
  command: 'node',
  args: ['server.js']
});

const client = new Client({
  name: 'my-client',
  version: '1.0.0'
}, {
  capabilities: {}
});

await client.connect(transport);
const tools = await client.listTools();
const result = await client.callTool({name: 'my_tool', arguments: {}});
```

#### Patterns
- ✅ TypeScript for type safety
- ✅ stdio transport most common
- ✅ Async/await throughout
- ✅ Use with Node.js servers

---

### 3. **Go** ⭐⭐

**SDK:** `github.com/mark3labs/mcp-go`  
**Maturity:** Beta  
**Anthropic Support:** ✅ Community

#### Installation
```bash
go get github.com/mark3labs/mcp-go
```

#### Build a Server
```go
package main

import (
    "github.com/mark3labs/mcp-go/server"
    "github.com/mark3labs/mcp-go/mcp"
)

func main() {
    s := server.NewMCPServer(
        "my-server",
        "1.0.0",
        server.WithStdioTransport(),
    )
    
    // Register tool
    s.AddTool(mcp.Tool{
        Name: "my_tool",
        Description: "Tool description",
        InputSchema: mcp.ToolInputSchema{
            Type: "object",
            Properties: map[string]interface{}{
                "param": map[string]string{"type": "string"},
            },
        },
    }, handleMyTool)
    
    s.Serve()
}

func handleMyTool(params map[string]interface{}) (interface{}, error) {
    return map[string]string{"result": "success"}, nil
}
```

#### Patterns
- ✅ High performance
- ✅ Good for system-level tools
- ✅ Use for Go microservices
- ✅ Struct-based configuration

---

### 4. **Rust** ⭐⭐

**SDK:** `mcp-rs` (Community)  
**Crate:** In development  
**Maturity:** Alpha  
**Anthropic Support:** ⚠️ Community

#### Build a Server (Pattern)
```rust
use mcp_rs::server::{Server, Tool, ToolSchema};
use serde_json::json;

#[tokio::main]
async fn main() {
    let server = Server::new("my-server", "1.0.0");
    
    server.add_tool(Tool {
        name: "my_tool".to_string(),
        description: "Tool description".to_string(),
        input_schema: ToolSchema {
            type_: "object".to_string(),
            properties: json!({"param": {"type": "string"}}),
            required: vec!["param".to_string()],
        },
        handler: |args| {
            Ok(json!({"result": "success"}))
        }
    });
    
    server.serve_stdio().await;
}
```

#### Patterns
- ✅ Memory safe
- ✅ Best for performance-critical tools
- ✅ Use for system programming
- ✅ Zero-cost abstractions

---

### 5. **Swift** ⭐⭐

**SDK:** Community implementations  
**Maturity:** Beta  
**Anthropic Support:** ⚠️ Community

#### Build a Server (Pattern)
```swift
import Foundation

struct MCPServer {
    let name: String
    let version: String
    
    func addTool(name: String, description: String, handler: @escaping (Dictionary<String, Any>) -> Any) {
        // Tool registration
    }
    
    func serve() {
        // stdio transport
    }
}

let server = MCPServer(name: "my-server", version: "1.0.0")

server.addTool(name: "my_tool", description: "Tool description") { params in
    return ["result": "success"]
}

server.serve()
```

#### Patterns
- ✅ iOS/macOS integration
- ✅ SwiftUI tools
- ✅ Native Apple ecosystem
- ✅ Type-safe

---

### 6. **Java** ⭐

**SDK:** Community implementations  
**Maturity:** Alpha  
**Anthropic Support:** ⚠️ Community

#### Build a Server (Pattern)
```java
import com.mcp.server.MCPServer;
import com.mcp.server.Tool;

public class MyMCPServer {
    public static void main(String[] args) {
        MCPServer server = new MCPServer("my-server", "1.0.0");
        
        server.addTool(new Tool(
            "my_tool",
            "Tool description",
            params -> {
                return Map.of("result", "success");
            }
        ));
        
        server.serveStdio();
    }
}
```

#### Patterns
- ✅ Enterprise integration
- ✅ JVM ecosystem
- ✅ Spring Boot compatibility
- ✅ Thread-safe

---

### 7. **C#/.NET** ⭐

**SDK:** Community implementations  
**Maturity:** Beta  
**Anthropic Support:** ⚠️ Community

#### Build a Server (Pattern)
```csharp
using MCP.Server;

public class MyMCPServer
{
    public static async Task Main(string[] args)
    {
        var server = new MCPServer("my-server", "1.0.0");
        
        server.AddTool("my_tool", "Tool description", async (params) => 
        {
            return new { result = "success" };
        });
        
        await server.ServeStdioAsync();
    }
}
```

#### Patterns
- ✅ .NET Core integration
- ✅ Azure ecosystem
- ✅ Async/await
- ✅ LINQ support

---

### 8. **Kotlin** ⭐

**SDK:** JVM-compatible  
**Maturity:** Alpha  
**Anthropic Support:** ⚠️ Via JVM

#### Build a Server (Pattern)
```kotlin
import com.mcp.server.MCPServer
import com.mcp.server.Tool

fun main() {
    val server = MCPServer("my-server", "1.0.0")
    
    server.addTool(Tool(
        name = "my_tool",
        description = "Tool description",
        handler = { params ->
            mapOf("result" to "success")
        }
    ))
    
    server.serveStdio()
}
```

#### Patterns
- ✅ Android integration
- ✅ Coroutines for async
- ✅ JVM interop
- ✅ Null safety

---

### 9. **Ruby** ⭐

**SDK:** Community implementations  
**Maturity:** Alpha  
**Anthropic Support:** ⚠️ Community

#### Build a Server (Pattern)
```ruby
require 'mcp/server'

server = MCP::Server.new('my-server', '1.0.0')

server.add_tool(
  name: 'my_tool',
  description: 'Tool description',
  handler: ->(params) { { result: 'success' } }
)

server.serve_stdio
```

#### Patterns
- ✅ Rails integration
- ✅ Blocks/lambdas
- ✅ Dynamic typing
- ✅ Gem ecosystem

---

### 10. **PHP** ⭐

**SDK:** Community implementations  
**Maturity:** Early  
**Anthropic Support:** ⚠️ Community

#### Build a Server (Pattern)
```php
<?php
require 'vendor/autoload.php';

use MCP\Server\MCPServer;
use MCP\Server\Tool;

$server = new MCPServer('my-server', '1.0.0');

$server->addTool(new Tool(
    'my_tool',
    'Tool description',
    function($params) {
        return ['result' => 'success'];
    }
));

$server->serveStdio();
```

#### Patterns
- ✅ Laravel/Symfony integration
- ✅ Composer packages
- ✅ Web-focused
- ✅ Session management

---

## 📊 SDK Comparison Matrix

| Language | SDK | Maturity | Anthropic | Transports | Use Case |
|----------|-----|----------|-----------|------------|----------|
| **Python** | mcp + pydantic-ai | ✅✅✅ | ✅ Native | stdio, SSE, HTTP | AI/ML, Data |
| **TypeScript** | @modelcontextprotocol/sdk | ✅✅✅ | ✅ Official | stdio, SSE | Web, Node |
| **Go** | mcp-go | ✅✅ | ✅ Community | stdio | Microservices |
| **Rust** | mcp-rs | ✅ | ⚠️ Community | stdio | Systems |
| **Swift** | Community | ✅ | ⚠️ Community | stdio | iOS/macOS |
| **Java** | Community | ✅ | ⚠️ JVM | stdio | Enterprise |
| **C#** | Community | ✅ | ⚠️ Community | stdio | .NET/Azure |
| **Kotlin** | JVM-based | ✅ | ⚠️ JVM | stdio | Android |
| **Ruby** | Community | ⚠️ | ⚠️ Community | stdio | Rails/Web |
| **PHP** | Community | ⚠️ | ⚠️ Community | stdio | WordPress |

**Legend:**
- ✅✅✅ = Production Ready
- ✅✅ = Beta (Stable)
- ✅ = Alpha (Usable)
- ⚠️ = Early/Experimental

---

## 🏗️ Build & Usage Patterns

### Pattern 1: Simple Tool Server (FastMCP - Python)

**When to use:** Quick tools, Python libraries, data processing

```python
from mcp.server.fastmcp import FastMCP, tool

mcp = FastMCP("toolserver")

@tool()
def process_data(input: str) -> dict:
    """Process data and return results."""
    # Your logic
    return {"output": processed}

# Run: python server.py
if __name__ == "__main__":
    mcp.run()
```

**Key Points:**
- Decorator-based (`@tool()`)
- Auto-documentation
- Type hints become schema
- Runs on stdio

---

### Pattern 2: Agent Orchestrator (Pydantic AI)

**When to use:** Coordinating multiple tools, complex workflows

```python
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

agent = Agent(
    'anthropic:claude-3-5-sonnet-latest',
    mcp_servers=[
        MCPServerStdio(command='python', args=['youtube.py'], tool_prefix='yt'),
        MCPServerStdio(command='python', args=['research.py'], tool_prefix='research'),
        MCPServerStdio(command='node', args=['web.js'], tool_prefix='web'),
    ],
    system_prompt='You coordinate research and content analysis.'
)

# Agent can use: yt_get_transcript, research_search_arxiv, web_scrape, etc.
result = await agent.run("Research quantum computing using all available sources")
```

**Key Points:**
- Multi-server orchestration
- Tool prefixing (namespace isolation)
- Anthropic models recommended
- Natural language→tool mapping

---

### Pattern 3: HTTP Server (TypeScript)

**When to use:** Web services, REST APIs, distributed systems

```typescript
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';
import express from 'express';

const app = express();
const server = new Server({name: 'web-server', version: '1.0.0'}, {capabilities: {tools: {}}});

// Register tools...

app.get('/sse', async (req, res) => {
  const transport = new SSEServerTransport('/message', res);
  await server.connect(transport);
});

app.listen(8080);
```

**Key Points:**
- HTTP-based (network accessible)
- SSE for real-time
- Express.js integration
- Scalable

---

### Pattern 4: Microservice Integration (Go)

**When to use:** High-performance services, system tools

```go
package main

import (
    "github.com/mark3labs/mcp-go/server"
    "github.com/mark3labs/mcp-go/mcp"
)

func main() {
    s := server.NewMCPServer("service", "1.0.0")
    
    s.AddTool(mcp.Tool{
        Name: "process",
        Description: "High-performance processing",
    }, func(params map[string]interface{}) (interface{}, error) {
        // Fast processing
        return map[string]string{"status": "done"}, nil
    })
    
    s.Serve()
}
```

**Key Points:**
- Compiled (fast)
- Concurrent by default
- Low resource usage
- Great for services

---

### Pattern 5: Cross-Language Ecosystem

**When to use:** Leveraging best-of-breed for each domain

```
┌─────────────────────────────────────────┐
│  Pydantic AI Orchestrator (Python)      │
│  - Coordinates everything                │
│  - Uses Anthropic Claude                 │
└──────────┬──────────────────────────────┘
           │
           ├──► Python/FastMCP (Data Tools)
           │    ├── YouTube transcripts
           │    ├── arXiv research
           │    └── Data processing
           │
           ├──► TypeScript/Node (Web Tools)
           │    ├── Web scraping
           │    ├── API calls
           │    └── Frontend integration
           │
           ├──► Go (System Tools)
           │    ├── Service testing
           │    ├── Performance monitoring
           │    └── Load balancing
           │
           └──► Rust (Performance Tools)
                ├── Video processing
                ├── ML inference
                └── System monitoring
```

**Key Points:**
- Each language handles its strengths
- Orchestrator coordinates all
- Type-safe boundaries
- Maximum performance

---

## 🤖 Agent Understanding Guide

### For AI Agents Reading This

#### What is MCP?
Model Context Protocol (MCP) is a standard way for me (an AI agent) to access external tools and data sources.

#### How It Works
1. **Client (Me)** - I send requests to use tools
2. **Server** - Provides tools I can call
3. **Transport** - How we communicate (stdio, HTTP, SSE)
4. **Tools** - Functions I can execute

#### Key Concepts I Need to Know

**Tool Schema** - Tells me what parameters a tool accepts
```json
{
  "name": "search",
  "inputSchema": {
    "properties": {
      "query": {"type": "string", "description": "Search query"}
    },
    "required": ["query"]
  }
}
```

**Tool Prefixes** - Namespace tools from different servers
- `youtube_get_transcript` - YouTube server
- `research_search_arxiv` - Research server  
- `web_scrape` - Web server

**Calling Tools** - I use natural language, system maps to tools
```
User: "Get transcript from YouTube video X"
→ I call: youtube_get_transcript(url="X")
```

#### Patterns I Should Use

**Pattern 1: Single Tool**
```python
# User asks for one thing
result = call_tool("youtube_get_transcript", {"url": "..."})
```

**Pattern 2: Sequential Tools**
```python
# User asks for multi-step process
transcript = call_tool("youtube_get_transcript", {"url": "..."})
papers = call_tool("research_search_arxiv", {"query": extract_topic(transcript)})
summary = synthesize(transcript, papers)
```

**Pattern 3: Parallel Tools**
```python
# User asks for multiple independent things
results = await asyncio.gather(
    call_tool("youtube_get_transcript", {"url": "1"}),
    call_tool("research_search_arxiv", {"query": "topic"}),
    call_tool("web_search_duckduckgo", {"query": "context"})
)
```

**Pattern 4: Store Results**
```python
# Always log what I do
result = call_tool("youtube_get_transcript", {"url": "..."})
call_tool("store_write_result", {
    "agent": "ai-assistant",
    "service": "youtube",
    "status": "PASS" if result else "FAIL",
    "summary": "Fetched transcript"
})
```

#### Error Handling I Should Do

```python
try:
    result = call_tool("tool_name", params)
    if result.get("status") == "error":
        # Try alternative approach
        fallback = call_tool("backup_tool", params)
except McpError as e:
    # Tool unavailable - inform user
    return "Tool is currently unavailable"
```

#### Multi-SDK Workflow Example

```
User Request: "Research AI trends by analyzing YouTube videos and papers"

My Workflow:
1. Use youtube_* tools → Get transcripts
2. Use research_* tools → Search arXiv  
3. Use web_* tools → Web search for context
4. Synthesize all sources
5. Use store_* tools → Save results
6. Return comprehensive analysis

I coordinate across 4 different MCP servers seamlessly!
```

---

## 🔗 Cross-SDK Integration Patterns

### Integration 1: Python ↔ Node.js

```python
# Python orchestrator calls Node.js server
from pydantic_ai.mcp import MCPServerStdio

agent = Agent('anthropic:claude-3-5-sonnet-latest', mcp_servers=[
    MCPServerStdio(command='python', args=['python_tools.py']),
    MCPServerStdio(command='node', args=['node_tools.js']),
])

# Agent can use tools from BOTH!
```

### Integration 2: All Languages Together

```yaml
# docker-compose.yml
services:
  mcp-ecosystem:
    # Container with Python, Node, Go binaries
    # Can exec any MCP server
    
  mcp-python-tools:
    # Pure Python tools
    
  mcp-node-tools:
    # Pure Node tools
    
  mcp-go-tools:
    # Pure Go tools

# Orchestrator connects to all
```

### Integration 3: Via MCP Store

```
All servers → Write results to MCP Store → Query from anywhere

Python server logs → MCP Store
Node server logs → MCP Store  
Go server logs → MCP Store

Any agent can query complete history!
```

---

## 📝 Configuration According to Anthropic's Spec

### Recommended mcp-config.json

```json
{
  "mcpServers": {
    "mcp-ecosystem-orchestrator": {
      "command": "python",
      "args": ["/mcp/pydantic_orchestrator.py"],
      "env": {
        "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY}",
        "OPENAI_API_KEY": "${OPENAI_API_KEY}"
      }
    },
    "youtube": {
      "command": "python",
      "args": ["/mcp/python_servers/youtube_server.py"]
    },
    "research": {
      "command": "python",
      "args": ["/mcp/python_servers/research_server.py"]
    },
    "web": {
      "command": "python",
      "args": ["/mcp/python_servers/web_server.py"]
    },
    "node-tools": {
      "command": "node",
      "args": ["/mcp/node_servers/index.js"]
    },
    "mcp-store": {
      "command": "python",
      "args": ["/mcp/python_servers/store_client.py"],
      "env": {
        "MCPSTORE_URL": "http://localhost:8411"
      }
    }
  }
}
```

### Following Anthropic's Patterns

1. ✅ **stdio transport** - Primary method
2. ✅ **JSON-RPC 2.0** - Message format
3. ✅ **Tool schemas** - JSON Schema validation
4. ✅ **Async/await** - Non-blocking operations
5. ✅ **Error handling** - Proper error responses
6. ✅ **Sampling support** - For agent-to-agent calls

---

## 🎯 Complete Tool Inventory

### By SDK/Language

#### Python Tools (via FastMCP)
1. `youtube_get_transcript`
2. `youtube_get_timed_transcript`
3. `youtube_get_video_info`
4. `youtube_batch_transcripts`
5. `research_search_arxiv`
6. `research_search_wikipedia`
7. `research_get_full_article`
8. `research_topic`
9. `web_search_duckduckgo`
10. `web_scrape_webpage`
11. `web_fetch_url`
12. `web_search_news`
13. `store_write_result`
14. `store_query_results`

#### Node.js Tools (via @modelcontextprotocol/sdk)
15. `node_test_service`
16. `node_extract_structured_data`
17. `node_api_call`

#### Orchestrator (via Pydantic AI)
18. `ecosystem_status`
19. `multi_source_research`

**Total: 19+ tools across 3 SDKs**

---

## 🚀 References & Resources

### Official Documentation
- **Anthropic MCP Spec:** https://modelcontextprotocol.io
- **Python SDK:** https://github.com/modelcontextprotocol/python-sdk
- **TypeScript SDK:** https://github.com/modelcontextprotocol/typescript-sdk
- **Pydantic AI:** https://ai.pydantic.dev/mcp/

### Community Repositories
- **MCP Servers List:** https://github.com/modelcontextprotocol/servers
- **Go SDK:** https://github.com/mark3labs/mcp-go
- **Community Tools:** https://github.com/topics/mcp-server

### Our Implementation
- **MCP Store:** `/services/mcp_store/`
- **MCP Ecosystem:** `/services/mcp_ecosystem/`
- **Documentation:** `/docs/mcp/`

---

**Status:** ✅ Comprehensive guide for all top 10 languages  
**Spec Compliance:** ✅ Follows Anthropic's MCP specification  
**Ready for:** Agents to understand and use all MCP patterns

