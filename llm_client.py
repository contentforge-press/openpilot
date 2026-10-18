"""
统一 LLM 客户端 —— 免费优先，可插拔升级
优先级（自动降级）：
  1) Pollinations  —— 免费 + 免Key + OpenAI兼容（默认模型 GPT-OSS 20B Reasoning）
  2) ARK           —— 火山引擎（若设置 ARK_API_KEY）
  3) OpenRouter    —— 免费额度/开源强模型（若设置 OPENROUTER_API_KEY）
  4) ollama        —— 本地离线（若本地 11434 在跑）

说明：Claude 为闭源专有模型，无法本地下载；本客户端用开源/免费模型平替。

用法:
  from llm_client import chat
  txt = chat([{"role":"user","content":"..."}])
"""
import os, json, requests

BASE = os.path.dirname(os.path.abspath(__file__))

# ---------- 配置 ----------
POLLINATIONS_URL   = "https://text.pollinations.ai/openai"
POLLINATIONS_MODEL = "openai-fast"                      # GPT-OSS 20B Reasoning LLM（免费免Key）
ARK_URL            = os.getenv("ARK_URL", "https://ark.cn-beijing.volces.com/api/plan/v3/chat/completions")
ARK_MODEL          = os.getenv("ARK_MODEL", "deepseek-v4-1-flash")
# 分工大脑：按子任务把活派给最合适的模型（可用环境变量覆盖）
ARK_ROLES = {
    "fast":   os.getenv("ARK_ROLE_FAST", "deepseek-v4-1-flash"),   # 分类/抽取/信号钩子/回复（快、稳）
    "copy":   os.getenv("ARK_ROLE_COPY", "kimi-k3"),               # 文案/叙述（质量优先，较慢）
    "reason": os.getenv("ARK_ROLE_REASON", "glm-5.3"),             # 分析/规划（推理）
}
OPENROUTER_URL     = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL   = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
OLLAMA_URL         = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/chat")
OLLAMA_MODEL       = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
# Cloudflare Workers AI（用已有 CF Token，免 Key、免卡）- 最强 120B；限 10,000 neurons/天
CF_ACCOUNT         = os.getenv("CF_ACCOUNT_ID", "4f5c91b1092d249b2cbdedb4eb408998")
CF_AI_MODEL        = os.getenv("CF_AI_MODEL", "@cf/openai/gpt-oss-120b")
# Groq（免卡、极快）— 免费 failover
GROQ_URL           = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL         = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
# Google AI Studio (Gemini) — 免卡 fee failover（OpenAI 兼容端点）
GEMINI_URL         = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
GEMINI_MODEL       = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def _load_key(name, filename):
    v = os.getenv(name, "")
    if v:
        return v
    p = os.path.join(BASE, filename)
    if os.path.exists(p):
        return open(p).read().strip()
    return ""


def _try_cf_ai(messages, model, temperature, max_tokens, timeout):
    """Cloudflare Workers AI（最快，~1s）。用已有 .cf_token。"""
    key = _load_key("CF_API_TOKEN", ".cf_token")
    if not key:
        return None
    try:
        r = requests.post(
            f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT}/ai/run/{model or CF_AI_MODEL}",
            json={"messages": messages, "max_tokens": max_tokens, "temperature": temperature},
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            timeout=timeout,
        )
        if r.status_code == 200:
            return (r.json().get("result") or {}).get("response")
    except Exception:
        pass
    return None


def _try_groq(messages, model, temperature, max_tokens, timeout):
    """Groq 免费 failover（免卡、极快）。key: GROQ_API_KEY 或 .groq_key"""
    key = _load_key("GROQ_API_KEY", ".groq_key")
    if not key:
        return None
    try:
        r = requests.post(GROQ_URL,
            json={"model": model or GROQ_MODEL, "messages": messages,
                  "temperature": temperature, "max_tokens": max_tokens},
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            timeout=timeout)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
    except Exception:
        pass
    return None


def _try_gemini(messages, model, temperature, max_tokens, timeout):
    """Google AI Studio (Gemini) 免费 failover（免卡）。key: GEMINI_API_KEY 或 .gemini_key"""
    key = _load_key("GEMINI_API_KEY", ".gemini_key")
    if not key:
        return None
    try:
        r = requests.post(GEMINI_URL,
            json={"model": model or GEMINI_MODEL, "messages": messages,
                  "temperature": temperature, "max_tokens": max_tokens},
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            timeout=timeout)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
    except Exception:
        pass
    return None


# 国内可直连的免费/低成本 provider（OpenAI 兼容；key 存 .<name>_key 或环境变量）
CN_PROVIDERS = [
    {"name": "zhipu",       "url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
     "env": "ZHIPU_API_KEY",       "keyfile": ".zhipu_key",       "model": "glm-4-flash"},
    {"name": "modelscope",  "url": "https://api-inference.modelscope.cn/v1/chat/completions",
     "env": "MODELSCOPE_API_KEY",  "keyfile": ".modelscope_key",  "model": "Qwen/Qwen2.5-7B-Instruct"},
    {"name": "siliconflow", "url": "https://api.siliconflow.cn/v1/chat/completions",
     "env": "SILICONFLOW_API_KEY", "keyfile": ".siliconflow_key", "model": "Qwen/Qwen2.5-7B-Instruct"},
    {"name": "dashscope",   "url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
     "env": "DASHSCOPE_API_KEY",   "keyfile": ".dashscope_key",   "model": "qwen-flash"},
]


def _try_cn(cfg, messages, model, temperature, max_tokens, timeout):
    """国内 OpenAI 兼容 provider（智谱/魔搭/硅基流动/通义）。"""
    key = _load_key(cfg["env"], cfg["keyfile"])
    if not key:
        return None
    try:
        r = requests.post(cfg["url"],
            json={"model": model or cfg["model"], "messages": messages,
                  "temperature": temperature, "max_tokens": max_tokens},
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            timeout=timeout)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
    except Exception:
        pass
    return None


def _try_pollinations(messages, model, temperature, max_tokens, timeout):
    try:
        r = requests.post(
            POLLINATIONS_URL,
            json={"model": model or POLLINATIONS_MODEL, "messages": messages,
                  "temperature": temperature, "max_tokens": max_tokens},
            headers={"Content-Type": "application/json"},
            timeout=timeout,
        )
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
    except Exception:
        pass
    return None


def _try_ark(messages, model, temperature, max_tokens, timeout):
    """火山方舟智能体计划（/api/plan/v3，OpenAI 兼容，国内直连）。key: ARK_API_KEY 或 .ark_key"""
    key = _load_key("ARK_API_KEY", ".ark_key")
    if not key:
        return None
    try:
        r = requests.post(
            ARK_URL,
            json={"model": model or ARK_MODEL, "messages": messages,
                  "temperature": temperature, "max_tokens": max_tokens},
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            timeout=timeout,
        )
        if r.status_code == 200:
            msg = r.json()["choices"][0]["message"]
            content = (msg.get("content") or "").strip()
            return content or None
    except Exception:
        pass
    return None


def _try_openrouter(messages, model, temperature, max_tokens, timeout):
    key = _load_key("OPENROUTER_API_KEY", ".openrouter_key")
    if not key:
        return None
    try:
        r = requests.post(
            OPENROUTER_URL,
            json={"model": model or OPENROUTER_MODEL, "messages": messages,
                  "temperature": temperature, "max_tokens": max_tokens},
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            timeout=timeout,
        )
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
    except Exception:
        pass
    return None


def _try_ollama(messages, model, temperature, max_tokens, timeout):
    try:
        r = requests.post(
            OLLAMA_URL,
            json={"model": model or OLLAMA_MODEL, "messages": messages,
                  "options": {"temperature": temperature, "num_predict": max_tokens},
                  "stream": False},
            timeout=timeout,
        )
        if r.status_code == 200:
            return r.json()["message"]["content"]
    except Exception:
        pass
    return None


def chat(messages, model=None, temperature=0.7, max_tokens=800, timeout=120, task=None, retries=3):
    """统一入口：按优先级自动降级，返回文本；全部失败返回 None。
    task ∈ {fast, copy, reason}：优先用该角色对应的火山方舟模型（分工大脑）。
    retries：每个 provider 重试次数
    顺序：ARK(角色/默认) → CF(120B) → Groq → Gemini → 国内 → Pollinations → OpenRouter → Ollama"""
    import time
    if isinstance(messages, str):
        messages = [{"role": "user", "content": messages}]
    
    providers = []
    if task and task in ARK_ROLES:
        providers.append(("ark_role", lambda: _try_ark(messages, ARK_ROLES[task], temperature, max_tokens, timeout)))
    providers += [
        ("ark", lambda: _try_ark(messages, model, temperature, max_tokens, timeout)),
        ("cf", lambda: _try_cf_ai(messages, model, temperature, max_tokens, timeout)),
        ("groq", lambda: _try_groq(messages, model, temperature, max_tokens, timeout)),
        ("gemini", lambda: _try_gemini(messages, model, temperature, max_tokens, timeout)),
    ]
    for cfg in CN_PROVIDERS:
        providers.append((cfg["name"], lambda c=cfg: _try_cn(c, messages, model, temperature, max_tokens, timeout)))
    providers += [
        ("pollinations", lambda: _try_pollinations(messages, model, temperature, max_tokens, timeout)),
        ("openrouter", lambda: _try_openrouter(messages, model, temperature, max_tokens, timeout)),
        ("ollama", lambda: _try_ollama(messages, model, temperature, max_tokens, timeout)),
    ]
    
    for name, fn in providers:
        for attempt in range(retries):
            out = fn()
            if out:
                return out.strip()
            if attempt < retries - 1:
                time.sleep(1)
    return None


def provider_info():
    """返回当前可用的 provider 列表（用于自检）"""
    avail = []
    if _try_cf_ai([{"role": "user", "content": "hi"}], None, 0.1, 5, 30):
        avail.append("cloudflare-workers-ai(免Key, 120B, 10k neurons/天)")
    if _load_key("GROQ_API_KEY", ".groq_key"):
        avail.append("groq(已配Key, 免卡快)" + ("" if _try_groq([{"role": "user", "content": "hi"}], None, 0.1, 5, 30) else "(调用失败)"))
    if _load_key("GEMINI_API_KEY", ".gemini_key"):
        avail.append("gemini(已配Key, 免卡)" + ("" if _try_gemini([{"role": "user", "content": "hi"}], None, 0.1, 5, 30) else "(调用失败)"))
    for cfg in CN_PROVIDERS:
        if _load_key(cfg["env"], cfg["keyfile"]):
            ok = _try_cn(cfg, [{"role": "user", "content": "hi"}], None, 0.1, 5, 30)
            avail.append(f"{cfg['name']}(已配Key)" + ("" if ok else "(调用失败)"))
    if _try_pollinations([{"role": "user", "content": "hi"}], None, 0.1, 5, 30):
        avail.append("pollinations(GPT-OSS 20B, 免费免Key)")
    if _load_key("ARK_API_KEY", ".ark_key"):
        avail.append("ark(已配Key)")
    if _load_key("OPENROUTER_API_KEY", ".openrouter_key"):
        avail.append("openrouter(已配Key)")
    try:
        r = requests.get(OLLAMA_URL.replace("/api/chat", "/api/tags"), timeout=3)
        if r.status_code == 200:
            avail.append("ollama(本地)")
    except Exception:
        pass
    return avail


if __name__ == "__main__":
    print("Provider 自检:", provider_info())
    demo = chat("用一句英文写：给一家刚收到 FDA 警告函的补充剂品牌的开场白（<25词）")
    print("\n示例输出:\n", demo)
