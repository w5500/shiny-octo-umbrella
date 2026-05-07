import os
import datetime
import requests
import sqlite3
import pandas as pd
import streamlit as st
from typing import Dict
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
        # 【新增】确保本地输出文件夹存在
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

    def save_to_db(self, topic: str, search_data: str, script: str):
        """保存生成的脚本到数据库"""
        try:
            with sqlite3.connect('aigc_factory.db') as conn:
                cursor = conn.cursor()
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute(
                    "INSERT INTO scripts (topic, search_data, final_script, created_at) VALUES (?, ?, ?, ?)",
                    (topic, search_data, script, now)
                )
                conn.commit()
            return True
        except Exception as e:
            st.error(f"数据库保存失败: {e}")
            return False

    def save_to_markdown(self, topic: str, script: str):
        """【新增】物理存盘功能：将脚本保存为 .md 文件"""
        try:
            # 清理文件名中的特殊字符
            safe_topic = "".join([c for c in topic if c.isalnum() or c in (' ', '_')]).rstrip()
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scripts_output/{safe_topic}_{timestamp}.md"
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"# 话题：{topic}\n")
                f.write(f"生成时间：{datetime.datetime.now()}\n\n")
                f.write(script)
            return filename
        except Exception as e:
            print(f"本地存盘失败: {e}")
            return None

    def fetch_real_time_trends(self, query: str) -> str:
        """接入 Tavily API 进行实时搜索"""
        if not self.search_api_key:
            return f"【模拟数据】关于'{query}'的实时讨论极其火爆。"
        
        try:
            url = "https://api.tavily.com/search"
            payload = {
                "api_key": self.search_api_key,
                "query": f"最新社交媒体热点趋势：{query}",
                "search_depth": "advanced",
                "include_answer": True,
                "max_results": 5
            }
            response = requests.post(url, json=payload).json()
            results = "\n".join([f"- {res['title']}: {res['content']}" for res in response.get("results", [])])
            return f"综合结论: {response.get('answer', '')}\n\n详情:\n{results}"
        except Exception as e:
            return f"搜索异常: {str(e)}"

    def _call_llm(self, messages: list) -> str:
        try:
            response = self.client.chat.completions.create(model=self.model, messages=messages)
            return response.choices[0].message.content
        except Exception as e:
            return f"API异常: {str(e)}"

    def trend_analyzer_agent(self, raw_data: str) -> str:
        system_prompt = "你是一个千万级爆款操盘手。从数据中提取核心情绪痛点、反常识切入点和视觉建议。"
        return self._call_llm([{"role": "system", "content": system_prompt}, {"role": "user", "content": raw_data}])

    def script_writer_agent(self, analysis: str, previous_feedback: str = "") -> str:
        system_prompt = (
            "你是一个短视频编剧。请输出包含分镜编号、画面描述、旁白和[Image Prompt]的Markdown表格脚本。"
        )
        user_prompt = f"分析结果：{analysis}"
        if previous_feedback:
            user_prompt += f"\n\n修改建议：{previous_feedback}"
        return self._call_llm([{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}])

    def critic_agent(self, script: str) -> Dict:
        system_prompt = "你是一个严苛的审核官。若脚本完美请仅回复'PASS'，否则给出尖锐的修改建议。"
        feedback = self._call_llm([{"role": "system", "content": system_prompt}, {"role": "user", "content": script}])
        return {"passed": feedback.strip().upper().startswith("PASS"), "feedback": feedback}

# ================= Streamlit UI =================
if __name__ == "__main__":
    st.title("🚀 全自动化多 Agent 内容工厂")
    
    with st.sidebar:
        st.header("⚙️ 引擎配置")
        api_key = st.text_input("LLM API Key", type="password")
        base_url = st.text_input("Base URL", value="https://api.deepseek.com")
        model_name = st.text_input("模型名称", value="deepseek-chat")
        tavily_key = st.text_input("Tavily API Key", type="password")
    
    topic_query = st.text_input("💡 创作主题", value="2026年AI全自动驾驶普及")
    
    if st.button("启动引擎", type="primary"):
        if not api_key: st.error("请配置 Key")
        else:
            factory = ContentFactoryWeb(api_key, base_url, model_name, tavily_key)
            with st.status("管线运行中...") as status:
                data = factory.fetch_real_time_trends(topic_query)
                st.write("🌍 联网数据获取完毕")
                analysis = factory.trend_analyzer_agent(data)
                st.write("🧠 趋势分析完毕")
                script = factory.script_writer_agent(analysis)
                
                for i in range(2): 
                    review = factory.critic_agent(script)
                    if review["passed"]: break
                    st.write(f"⚠️ 第{i+1}轮审核未通过，重写中...")
                    script = factory.script_writer_agent(analysis, review["feedback"])
                
                # 保存到数据库
                factory.save_to_db(topic_query, data, script)
                # 【新增】自动物理保存到本地文件夹
                file_path = factory.save_to_markdown(topic_query, script)
                
                status.update(label=f"🎉 生成完毕！文件已存至: {file_path}", state="complete")
            
            st.markdown(script)
            # 同时保留网页下载按钮
            st.download_button("💾 点击下载脚本", script, file_name=f"{topic_query}.md")
    
    st.divider()
    st.subheader("📚 历史记录")
    if st.button("查看数据库记录"):
        with sqlite3.connect('aigc_factory.db') as conn:
            df = pd.read_sql_query("SELECT topic, created_at FROM scripts ORDER BY created_at DESC", conn)
            st.table(df)