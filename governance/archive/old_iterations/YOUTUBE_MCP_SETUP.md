# YouTube Transcript MCP Setup

✅ **Status:** Running on port 8412

## 🎬 What It Does

The YouTube Transcript MCP server provides tools to:
- `get_transcript` - Get full transcript of a YouTube video
- `get_timed_transcript` - Get transcript with timestamps
- `get_video_info` - Get video metadata

## 🚀 Quick Start

### Start the Service
```bash
cd AI-Projects/universal-ai-tools
docker compose -f docker-compose.youtube-mcp.yml up -d
```

### Check Status
```bash
docker ps | grep youtube
docker logs youtube-transcript-mcp
```

### Stop the Service
```bash
docker compose -f docker-compose.youtube-mcp.yml down
```

## 🔧 Usage

### From MCP Client
```python
from mcp import Client

mcp = Client()

# Get transcript
transcript = mcp.call_tool("get_transcript", 
    url="https://www.youtube.com/watch?v=VIDEO_ID"
)

# Get timed transcript
timed = mcp.call_tool("get_timed_transcript",
    url="https://www.youtube.com/watch?v=VIDEO_ID"
)

# Get video info
info = mcp.call_tool("get_video_info",
    url="https://www.youtube.com/watch?v=VIDEO_ID"
)
```

### Direct HTTP Call
```bash
# The MCP server runs on port 8412
curl http://localhost:8412/health
```

## 📝 Configuration

The service is configured in:
- **Docker Compose:** `docker-compose.youtube-mcp.yml`
- **MCP Config:** `mcp-config.json` (youtube-transcript server)
- **Port:** 8412
- **Network:** universal-ai-network

### Environment Variables

```yaml
RESPONSE_LIMIT: 10000      # Max characters per response
HTTP_PROXY: ""              # Optional HTTP proxy
HTTPS_PROXY: ""             # Optional HTTPS proxy
```

## 🔗 Integration with MCP Store

You can automatically log YouTube transcript requests to MCP Store:

```python
# Get transcript and log it
transcript = mcp.call_tool("get_transcript", url="...")

# Log to MCP Store
mcp.call_tool("store_write",
    agent="youtube-transcript",
    service="transcript-fetcher",
    status="PASS" if transcript else "FAIL",
    summary=f"Fetched transcript for video",
    details_json=json.dumps({"url": url, "length": len(transcript)})
)
```

## 🛠️ Makefile Targets

Add to your Makefile:

```makefile
youtube-mcp-up:
\tcd AI-Projects/universal-ai-tools && docker compose -f docker-compose.youtube-mcp.yml up -d

youtube-mcp-down:
\tcd AI-Projects/universal-ai-tools && docker compose -f docker-compose.youtube-mcp.yml down

youtube-mcp-logs:
\tdocker logs -f youtube-transcript-mcp

youtube-mcp-restart:
\t$(MAKE) youtube-mcp-down
\t$(MAKE) youtube-mcp-up
```

## 📊 Tools Available

### 1. get_transcript
Gets the full transcript without timestamps.

**Input:**
- `url` (string): YouTube video URL

**Output:**
- Plain text transcript

### 2. get_timed_transcript
Gets transcript with timing information.

**Input:**
- `url` (string): YouTube video URL

**Output:**
- JSON array with `text`, `start`, `duration` for each segment

### 3. get_video_info
Gets metadata about the video.

**Input:**
- `url` (string): YouTube video URL

**Output:**
- Video title, author, length, etc.

## 🔍 Troubleshooting

### Container Keeps Restarting
This is normal behavior for MCP servers - they start, wait for connections, then shut down and restart on demand.

### Connection Refused
Make sure the container is running:
```bash
docker ps | grep youtube-transcript-mcp
```

### Transcript Not Available
Some videos don't have transcripts. The tool will return an error in those cases.

### Proxy Issues
If behind a proxy, set the HTTP_PROXY and HTTPS_PROXY environment variables in the compose file.

## 🎯 Next Steps

1. ✅ **Test it:** Try fetching a transcript
2. ✅ **Integrate:** Connect to your AI agents
3. ✅ **Log:** Store results in MCP Store
4. ✅ **Automate:** Add to your workflows

## 📚 Documentation

- **MCP Protocol:** https://github.com/modelcontextprotocol
- **YouTube Transcript:** https://github.com/jkawamoto/mcp-youtube-transcript
- **Docker Hub:** https://hub.docker.com/r/mcp/youtube-transcript

---

**Status:** ✅ Running on port 8412  
**Container:** youtube-transcript-mcp  
**Network:** universal-ai-network

