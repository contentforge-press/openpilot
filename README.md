# 🚀 OpenPilot - 开源 AI 代理框架

> 多模型 LLM 编排 + 工具调用 + 任务自动化。零配置，开箱即用。

## ✨ 特性

- **多模型大脑**：自动切换 deepseek / glm / kimi / groq / gemini，永不中断
- **工具调用**：网页搜索、URL 抓取、文件读写、邮件发送
- **零配置**：克隆即跑，不需要 API key（内置免费 LLM 回退链）
- **可扩展**：轻松添加自定义工具

## 🚀 快速开始

```bash
git clone https://github.com/你的用户名/openpilot.git
cd openpilot
python3 openpilot.py "搜索今天的 AI 新闻并总结"
```

## 📖 用法

```python
from openpilot import Agent

agent = Agent()
result = agent.run("帮我抓取 https://example.com 并总结内容")
print(result)
```

### 可用工具

| 工具 | 说明 |
|------|------|
| `web_search` | 搜索网页 |
| `fetch_url` | 抓取网页内容 |
| `read_file` | 读取本地文件 |
| `write_file` | 写入文件 |
| `send_email` | 发送邮件 |
| `now` | 当前时间 |

## 💰 托管版

不想自己部署？使用我们的托管版本：

- **免费版**：本地运行，所有功能
- **托管版 $19/月**：云端运行，API 访问，优先模型

👉 [立即使用托管版](https://checkout.dodopayments.com/session/cks_0NpybOiirX7X66rKHfYfM)

## 🛠️ 技术栈

- Python 3.8+
- 多模型 LLM 编排（自动降级：deepseek → glm → kimi → groq → gemini → pollinations）
- 零依赖核心（只需 requests）

## 📄 License

MIT

---

**给个 Star ⭐ 支持一下！**
