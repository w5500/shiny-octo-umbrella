import os
import datetime
import requests
import sqlite3
import pandas as pd
import streamlit as st
from typing import Dict, List
from openai import OpenAI

# ================= 页面配置 =================
st.set_page_config(page_title="AIGC 多 Agent 内容工厂", page_icon="🚀", layout="wide")

# ================= 核心逻辑类 =================
class ContentFactoryWeb:
    def __init__(self, api_key: str, base_url: str, model_name: str, search_api_key: str = ""):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model_name
        self.search_api_key = search_api_key
        self._init_db()
        if not os.path.exists("scripts_output"):
            os.makedirs("scripts_output")

    def _init_db(self):
        """初始化 SQLite 数据库"""
        with sqlite3.connect('aigc_factory.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scripts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT,
                    search_data TEXT,
                    final_script TEXT,
                    created_at DATETIME
                )
            ''')
            conn.commit()

    def _call_llm(self, messages: list) -> str:
        try:
            response = self.client.chat.completions.create(model=self.model, messages=messages)
            return response.choices[0].message.content
        except Exception as e:
            return f"API异常: {str(e)}"

    # ================= 新增：自动主题生成功能 =================
    def inspiration_agent(self, industry_context: str) -> List[str]:
        """Agent 0: 灵感专家 - 自动策划今日创作主题"""
        print("[Inspiration Agent] 正在洞察行业趋势并策划主题...")
        
        # 1. 先通过搜索获取行业动态（如果提供了 API Key）
        trend_context = self.fetch_real_time_trends(f"{industry_context} 最新热点")
        
        system_prompt = (
            f"你是一个拥有敏锐嗅觉的内容策划总监。你的任务是根据背景信息，策划3个最具有『爆款潜质』的具体创作主题。\n"
            "【要求】：\n"
            "1. 主题必须具体且具有冲突感（例如：不要写'AI发展'，要写'为什么90%的程序员会被AI取代'）。\n"
            "2. 仅输出主题名称，每个主题占一行，不要有编号或其他文字。"
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"行业背景：{industry_context}\n实时参考信息：{trend_context}"}
        ]
        
        raw_output = self._call_llm(messages)
        # 将输出按行切分为列表
        topics = [t.strip() for t in raw_output.strip().split('\n') if t.strip()]
        return topics[:3] # 确保只返回3个

    def save_to_db(self, topic: str, search_data: str, script: str):
        with sqlite3.connect('aigc_factory.db') as conn:
            cursor = conn.cursor()
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO scripts (topic, search_data, final_script, created_at) VALUES (?, ?, ?, ?)",
                           (topic, search_data, script, now))
            conn.commit()

    def save_to_markdown(self, topic: str, script: str):
        safe_topic = "".join([c for c in topic if c.isalnum() or c in (' ', '_')]).rstrip()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scripts_output/{safe_topic}_{timestamp}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# 话题：{topic}\n生成时间：{datetime.datetime.now()}\n\n{script}")
        return filename

    def fetch_real_time_trends(self, query: str) -> str:
        if not self.search_api_key: return "模拟联网数据：AI行业今日重点在于多模态模型落地。"
        try:
            url = "https://api.tavily.com/search"
            payload = {"api_key": self.search_api_key, "query": query, "search_depth": "advanced", "max_results": 3}
            response = requests.post(url, json=payload).json()
            return "\n".join([f"- {res['title']}: {res['content']}" for res in response.get("results", [])])
        except: return "搜索服务暂时不可用。"

    def trend_analyzer_agent(self, raw_data: str) -> str:
        system_prompt = "你是一个千万级爆款操盘手。从数据中提取核心情绪痛点、反常识切入点和视觉建议。"
        return self._call_llm([{"role": "system", "content": system_prompt}, {"role": "user", "content": raw_data}])

    def script_writer_agent(self, analysis: str, previous_feedback: str = "") -> str:
        system_prompt = "你是一个短视频编剧。请输出包含分镜、旁白和[Image Prompt]的Markdown表格脚本。"
        user_prompt = f"分析结果：{analysis}" + (f"\n修改建议：{previous_feedback}" if previous_feedback else "")
        return self._call_llm([{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}])

    def critic_agent(self, script: str) -> Dict:
        system_prompt = "你是一个严苛的审核官。若脚本完美请仅回复'PASS'，否则给出尖锐的修改建议。"
        feedback = self._call_llm([{"role": "system", "content": system_prompt}, {"role": "user", "content": script}])
        return {"passed": feedback.strip().upper().startswith("PASS"), "feedback": feedback}

# ================= Streamlit UI =================
if __name__ == "__main__":
    st.title("🚀 全自动化多 Agent 内容工厂 (V3.0)")
    
    with st.sidebar:
        st.header("⚙️ 引擎配置")
        api_key = st.text_input("LLM API Key", type="password")
        base_url = st.text_input("Base URL", value="https://api.deepseek.com")
        model_name = st.text_input("模型名称", value="deepseek-chat")
        tavily_key = st.text_input("Tavily API Key", type="password")

    # --- 模式选择 ---
    mode = st.radio("选择运行模式", ["手动输入主题", "🤖 Agent 自动策划主题"])

    if mode == "手动输入主题":
        topic_input = st.text_input("💡 创作主题", value="2026年AI全自动驾驶普及")
        run_topics = [topic_input]
    else:
        industry_context = st.text_input("🏢 关注领域", value="人工智能、短视频出海、数码科技")
        if st.button("🪄 让 Agent 策划今日主题"):
            if not api_key: st.error("请先配置 Key")
            else:
                factory = ContentFactoryWeb(api_key, base_url, model_name, tavily_key)
                st.session_state.auto_topics = factory.inspiration_agent(industry_context)
        
        run_topics = st.session_state.get("auto_topics", [])
        if run_topics:
            st.success(f"Agent 已为你策划以下主题：\n" + "\n".join([f"- {t}" for t in run_topics]))

    if st.button("🔥 启动全链路生产", type="primary"):
        if not api_key: st.error("请配置 Key")
        elif not run_topics: st.warning("请先确定或策划主题")
        else:
            factory = ContentFactoryWeb(api_key, base_url, model_name, tavily_key)
            for topic in run_topics:
                with st.status(f"正在生产：{topic}...") as status:
                    data = factory.fetch_real_time_trends(topic)
                    analysis = factory.trend_analyzer_agent(data)
                    script = factory.script_writer_agent(analysis)
                    
                    for i in range(2):
                        review = factory.critic_agent(script)
                        if review["passed"]: break
                        script = factory.script_writer_agent(analysis, review["feedback"])
                    
                    factory.save_to_db(topic, data, script)
                    file_path = factory.save_to_markdown(topic, script)
                    status.update(label=f"✅ {topic} 完成并存档", state="complete")
                
                st.markdown(f"### 📄 {topic} 最终脚本")
                st.markdown(script)
                st.divider()

    st.subheader("📚 历史库")
    if st.button("查看数据库"):
        with sqlite3.connect('aigc_factory.db') as conn:
            df = pd.read_sql_query("SELECT topic, created_at FROM scripts ORDER BY created_at DESC", conn)
            st.table(df)