"""
OpenPilot - Open-Source AI Agent Framework
Core: Multi-model LLM orchestration + tool calling + task automation

用法:
    from openpilot import Agent
    agent = Agent()
    result = agent.run("帮我总结这篇文章的要点")
"""
import json, os, sys, time
from llm_client import chat, ARK_ROLES

BASE = os.path.dirname(os.path.abspath(__file__))

# 内置工具集
class Tools:
    """Tools available to the agent"""
    
    @staticmethod
    def web_search(query, max_results=5):
        """Search the web"""
        try:
            import requests
            r = requests.get(f"https://searx.be/search?q={query}&format=json", timeout=10)
            if r.status_code == 200:
                results = r.json().get("results", [])[:max_results]
                return [{"title": x.get("title"), "url": x.get("url"), "content": x.get("content","")[:200]} for x in results]
        except:
            pass
        return []
    
    @staticmethod
    def fetch_url(url):
        """Fetch webpage content"""
        try:
            import requests
            r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            return r.text[:5000]
        except:
            return ""
    
    @staticmethod
    def read_file(path):
        """Read file"""
        try:
            return open(path).read()
        except:
            return f"无法读取: {path}"
    
    @staticmethod
    def write_file(path, content):
        """Write file"""
        try:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            open(path, "w").write(content)
            return f"已写入: {path}"
        except Exception as e:
            return f"写入失败: {e}"
    
    @staticmethod
    def send_email(to, subject, body):
        """Send email (requires Brevo key)"""
        try:
            key = open(os.path.join(BASE, ".brevo_key")).read().strip()
            import requests
            r = requests.post("https://api.brevo.com/v3/smtp/email",
                headers={"api-key": key, "content-type": "application/json"},
                json={"sender":{"name":"OpenPilot","email":"noreply@pixharvest.com"},
                      "to":[{"email":to}],"subject":subject,"htmlContent":body},
                timeout=10)
            return "已发送" if r.status_code in (200,201) else f"失败: {r.status_code}"
        except:
            return "邮件发送失败"
    
    @staticmethod
    def now():
        """Current time"""
        return time.strftime("%Y-%m-%d %H:%M:%S")


TOOL_LIST = {
    "web_search": "Search the web，参数: query",
    "fetch_url": "抓取网页，参数: url",
    "read_file": "Read file，参数: path",
    "write_file": "Write file，参数: path, content",
    "send_email": "发邮件，参数: to, subject, body",
    "now": "Current time",
}


class Agent:
    """AI Agent - multi-step reasoning + tool calling"""
    
    def __init__(self, task="fast", max_steps=10):
        self.task = task
        self.max_steps = max_steps
        self.tools = Tools()
        self.memory = []
    
    def _tool_prompt(self):
        tools_desc = "\n".join(f"- {name}: {desc}" for name, desc in TOOL_LIST.items())
        return f"""You are an AI agent that can call tools to complete tasks.。

Available tools:
{tools_desc}

How it works:
1. Analyze the user request
2. If tools are needed, output JSON: {{"action": "tool_name", "args": {{"key": "value"}}}}
3. If no tools needed, output the answer directly: {{"action": "answer", "content": "你的回答"}}

Only output JSON, nothing else.。"""
    
    def run(self, user_input):
        """Run the agent"""
        system = self._tool_prompt()
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_input},
        ]
        
        for step in range(self.max_steps):
            response = chat(messages, task=self.task, max_tokens=800, timeout=90)
            if not response:
                return "LLM call failed, check network"
            
            # 解析 JSON 响应
            try:
                # 提取 JSON
                text = response.strip()
                if text.startswith("```"):
                    text = text.split("```")[1]
                    if text.startswith("json"):
                        text = text[4:]
                text = text.strip()
                
                # 尝试找到 JSON 对象
                start = text.find("{")
                end = text.rfind("}") + 1
                if start >= 0 and end > start:
                    action = json.loads(text[start:end])
                else:
                    action = {"action": "answer", "content": text}
            except:
                action = {"action": "answer", "content": response}
            
            if action.get("action") == "answer":
                return action.get("content", "")
            
            # 执行工具
            tool_name = action.get("action")
            args = action.get("args", {})
            
            if hasattr(self.tools, tool_name):
                tool_fn = getattr(self.tools, tool_name)
                try:
                    result = tool_fn(**args)
                except TypeError:
                    result = tool_fn(args)
                except Exception as e:
                    result = f"工具错误: {e}"
                
                self.memory.append({"step": step, "tool": tool_name, "result": str(result)[:500]})
                messages.append({"role": "assistant", "content": response})
                messages.append({"role": "user", "content": f"工具 {tool_name} 返回:\n{str(result)[:1000]}\n\n继续或给出最终答案。"})
            else:
                messages.append({"role": "assistant", "content": response})
                messages.append({"role": "user", "content": f"未知工具: {tool_name}，请用 answer 直接回答或使用已知工具。"})
        
        return "Max steps reached, last result: " + str(self.memory[-1] if self.memory else "无")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        agent = Agent()
        print(agent.run(" ".join(sys.argv[1:])))
    else:
        print("OpenPilot AI 代理框架")
        print("用法: python3 openpilot.py \"你的任务\"")
        print()
        print("示例:")
        print('  python3 openpilot.py "搜索今天的AI新闻并总结"')
        print('  python3 openpilot.py "读取README.md并生成摘要"')
