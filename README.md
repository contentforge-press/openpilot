# 🚀 OpenPilot - Open-Source AI Agent Framework

> Multi-model LLM orchestration + tool calling + task automation. Zero config, works out of the box.

## ✨ Features

- **Multi-model brain**: Auto-switches between deepseek / glm / kimi / groq / gemini — never breaks
- **Tool calling**: Web search, URL fetching, file read/write, email sending
- **Zero config**: Clone and run, no API key required (built-in free LLM fallback chain)
- **Extensible**: Easily add custom tools

## 🚀 Quick Start

```bash
git clone https://github.com/contentforge-press/openpilot.git
cd openpilot
python3 openpilot.py "Search today's AI news and summarize"
```

## 📖 Usage

```python
from openpilot import Agent

agent = Agent()
result = agent.run("Fetch https://example.com and summarize the content")
print(result)
```

### Available Tools

| Tool | Description |
|------|-------------|
| `web_search` | Search the web |
| `fetch_url` | Fetch webpage content |
| `read_file` | Read a local file |
| `write_file` | Write to a file |
| `send_email` | Send an email |
| `now` | Current time |

## 💰 Hosted Version

Don't want to self-host? Use our hosted version:

- **Free**: Run locally, all features
- **Hosted $19/mo**: Cloud running, API access, priority models

👉 [Get Hosted Version](https://checkout.dodopayments.com/session/cks_0NpybOiirX7X66rKHfYfM)

## 🛠️ Tech Stack

- Python 3.8+
- Multi-model LLM orchestration (auto-fallback: deepseek → glm → kimi → groq → gemini → pollinations)
- Zero-dependency core (only `requests` needed)

## 📄 License

MIT

---

**Give it a Star ⭐ if you find it useful!**
