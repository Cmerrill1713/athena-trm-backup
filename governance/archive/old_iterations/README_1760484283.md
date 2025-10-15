# IndyDevDan Video Transcripts

**Channel**: [@indydevdan](https://www.youtube.com/@indydevdan)
**Downloaded**: $(date)
**Total Videos**: 10

## 📺 Videos Included

1. **Claude Code 2.0 Agentic Coding** - 91K chars
2. **My TOP 5 Agentic Bets** - 79K chars
3. **Agentic Coding ENDGAME** - 52K chars
4. **Agentic Prompt Engineering** - 113K chars
5. **Elite Context Engineering** - 85K chars
6. **Agentic Workflows BEYOND the Chat UI** - 80K chars
7. **5 Agent PATTERNS to SIMPLIFY** - 91K chars
8. **Claude Code Output Styles** - 92K chars
9. **GPT-5 Agentic Coding** - 117K chars
10. **ADDICTED to Claude Code** - 82K chars

**Total Content**: ~887K characters across all transcripts

## 🔍 Topics Covered

- Claude Code 2.0 & Claude 4.5 Sonnet
- Agentic coding architectures & workflows
- Scout-Plan-Build patterns
- Context engineering (R&D framework)
- Dedicated agent devices
- MCP servers & custom agents
- Multi-agent systems
- Tactical agentic coding

## 💾 Files

- `.vtt` - Original subtitle files from YouTube
- `.txt` - Plain text transcripts
- `.json` - Structured data (first video only)

## 🗄️ Embedded in Weaviate

All transcripts are embedded in the Weaviate knowledge base:
- **Class**: LearnedPattern
- **Tags**: indydevdan, agentic-coding, claude-code, tutorial, youtube
- **Query**: http://localhost:8090

## 📖 Usage

Search the knowledge base:
\`\`\`bash
curl 'http://localhost:8090/v1/graphql' -H 'Content-Type: application/json' \\
  --data '{"query":"{ Get { LearnedPattern(where: {operator: Like, path: [\"tags\"], valueText: \"*indydevdan*\"}) { title description } } }"}'
\`\`\`
