import os
import datetime
import requests
import sqlite3
import pandas as pd
import streamlit as st
import re # 用于解析 Prompt
from typing import Dict, List
from openai import OpenAI

# ================= 页面配置 =================
st.set_page_config(page_title="AIGC 多 Agent 内容工厂 (V4.0 - 配图版)", page_icon="🎨", layout="wide")

# ================= 核心逻辑类 =================
class ContentFactoryWeb:
    def __init__(self, api_key: str, base_url: str, model_name: str, search_api_key: str = ""):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model_name
        self.search_api_key = search_api_key
        # 绘画模型 Key (通常和 LLM Key 一致，如果 base_url 是官方 openai)
        self.dalle_client = OpenAI(api_key=api_key) 
        self._init_db()
        # 确保输出文件夹存在
        if not os.path.exists("scripts_output"): os.makedirs("scripts_output")
        if not os.path.exists("images_output"): os.makedirs("images_output")

    def _init_db(self):
        with sqlite3.connect('aigc_factory.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS scripts (id INTEGER PRIMARY KEY AUTOINCREMENT, topic TEXT, search_data TEXT, final_script TEXT, created_at DATETIME)''')
            conn.commit()

    def _call_llm(self, messages: list) -> str:
        try:
            response = self.client.chat.completions.create(model=self.model, messages=messages)
            return response.choices[0].message.content
        except Exception as e:
            return f"API异常: {str(e)}"

    # ================= 绘画功能集成 =================
    def save_image_from_url(self, url: str, filename: str) -> str:
        """【核心】将网络图片下载并保存到本地"""
        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                with open(filename, 'wb') as f:
                    for chunk in response.get("data", []):
                        f.write(chunk)
                return filename
            else:
                print(f"图片下载失败，状态码: {response.status_code}")
                return ""
        except Exception as e:
            print(f"图片下载异常: {str(e)}")
            return ""

    def artist_agent(self, script_md: str, topic: str) -> str:
        """Agent 4: 绘画专家 - 解析脚本并调用 DALL-E 3 配图"""
        print(f"[Artist Agent] 开始为脚本《{topic}》配图...")
        
        # 1. 解析 Markdown 表格，提取所有 Image Prompt
        # 假设脚本格式为 Markdown 表格，Image Prompt 位于某一列
        prompt_pattern = r"\[Image Prompt\]:\s*(.*?)(?=\s*\||$|\n)"
        all_prompts = re.findall(prompt_pattern, script_md)
        
        if not all_prompts:
            print("脚本中未探测到 Image Prompt，跳过配图。")
            return script_md
        
        # 确保只配前几个分镜，节省费用和时间（演示用）
        prompts_to_generate = all_prompts[:3] 
        updated_script = script_md
        image_links = []
        
        # 创建专属的主题图片文件夹
        safe_topic = "".join([c for c in topic if c.isalnum() or c in (' ', '_')]).rstrip()
        topic_img_dir = f"images_output/{safe_topic}_{datetime.datetime.now().strftime('%m%d%H%M')}"
        if not os.path.exists(topic_img_dir): os.makedirs(topic_img_dir)

        for i, raw_prompt in enumerate(prompts_to_generate):
            # 为了画面风格统一，为 Prompt 加上统一后缀
            final_prompt = f"{raw_prompt}, realistic style, cinematic lighting, 4k, ultra-detailed"
            print(f"正在为分镜 {i+1} 生成图片...")
            
            try:
                # 调用 DALL-E 3 API
                response = self.dalle_client.images.generate(
                    model="dall-e-3",
                    prompt=final_prompt,
                    size="1024x1024",
                    quality="standard",
                    n=1,
                )
                
                image_url = response.data[0].url
                
                # 保存到本地
                image_filename = f"{topic_img_dir}/shot_{i+1}.png"
                saved_path = self.save_image_from_url(image_url, image_filename)
                
                if saved_path:
                    # 在生成的 Markdown 脚本中插入本地图片路径（用于在 Streamlit 展示或本地预览）
                    # 替换原有的 Image Prompt 文本为图片的本地链接
                    image_links.append(saved_path)
                    updated_script = updated_script.replace(f"[Image Prompt]: {raw_prompt}", f"![分镜{i+1}]({saved_path})")
                
            except Exception as e:
                print(f"分镜 {i+1} 生成图片失败: {str(e)}")
        
        # 2. 如果成功生成了图片，将图片路径列表保存到数据库（暂不演示，需要修改 DB 结构）
        print(f"[Artist Agent] 配图完成，共成功生成 {len(image_links)} 张图片。")
        return updated_script

    # ================= 原有功能保持不变 =================
    def inspiration_agent(self, context: str) -> List[str]:
        trend = self.fetch_real_time_trends(f"{context} 热点")
        output = self._call_llm([{"role": "system", "content": "策划3个有冲突感的创作主题，每行一个。"},{"role": "user", "content": f"领域:{context},参考:{trend}"}])
        return [t.strip() for t in output.strip().split('\n') if t.strip()][:3]

    def fetch_real_time_trends(self, query: str) -> str:
        if not self.search_api_key: return "模拟联网数据。"
        try:
            url = "https://api.tavily.com/search"
            payload = {"api_key": self.search_api_key, "query": query, "search_depth": "advanced", "max_results": 3}
            response = requests.post(url, json=payload).json()
            return "\n".join([f"- {res['title']}: {res['content']}" for res in response.get("results", [])])
        except: return "搜索不可用。"

    def trend_analyzer_agent(self, data: str) -> str:
        return self._call_llm([{"role": "system", "content": "提取痛点、反常识点、视觉建议。"},{"role": "user", "content": data}])

    def script_writer_agent(self, analysis: str, feedback: str = "") -> str:
        return self._call_llm([{"role": "system", "content": "短视频编剧，输出包含分镜、画面、旁白和[Image Prompt]的Markdown表格脚本。"},{"role": "user", "content": analysis + (f"\n反馈:{feedback}" if feedback else "")}])

    def critic_agent(self, script: str) -> Dict:
        res = self._call_llm([{"role": "system", "content": "完美复'PASS'，否则给尖锐修改建议。"},{"role": "user", "content": script}])
        return {"passed": "PASS" in res.upper(), "feedback": res}

    def save_to_db(self, topic: str, data: str, script: str):
        with sqlite3.connect('aigc_factory.db') as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO scripts (topic, search_data, final_script, created_at) VALUES (?, ?, ?, ?)", (topic, data, script, datetime.datetime.now()))
            conn.commit()

    def save_to_markdown(self, topic: str, script: str):
        fn = f"scripts_output/{topic}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(fn, "w", encoding="utf-8") as f: f.write(script)
        return fn

# ================= Streamlit UI =================
if __name__ == "__main__":
    st.title("🚀 多 Agent 内容工厂 (V4.0🎨)")
    
    with st.sidebar:
        st.header("⚙️ 配置")
        # DALL-E 3 通常需要官方 API Key
        api_key = st.text_input("OpenAI/DeepSeek API Key", type="password") 
        base_url = st.text_input("Base URL", value="https://api.deepseek.com")
        model_name = st.text_input("模型名称", value="deepseek-chat")
        tavily_key = st.text_input("Tavily API Key", type="password")

    mode = st.radio("模式", ["手动输入主题", "🤖 Agent 自策划主题"])

    if mode == "手动输入主题":
        run_topics = [st.text_input("💡 主题", value="2026 AI普及")]
    else:
        context = st.text_input("🏢 关注领域", value="数码科技")
        if st.button("🪄 策划"):
            factory = ContentFactoryWeb(api_key, base_url, model_name, tavily_key)
            st.session_state.auto_topics = factory.inspiration_agent(context)
        run_topics = st.session_state.get("auto_topics", [])
        if run_topics: st.success("策划主题:" + "\n".join([f"- {t}" for t in run_topics]))

    if st.button("🔥 启动自动化配图生产", type="primary"):
        factory = ContentFactoryWeb(api_key, base_url, model_name, tavily_key)
        for topic in run_topics:
            with st.status(f"处理：{topic}...") as status:
                data = factory.fetch_real_time_trends(topic)
                analysis = factory.trend_analyzer_agent(data)
                script = factory.script_writer_agent(analysis)
                
                # 审核迭代
                for i in range(2):
                    review = factory.critic_agent(script)
                    if review["passed"]: break
                    script = factory.script_writer_agent(analysis, review["feedback"])
                
                # --- 新增：自动配图环节 ---
                st.write(f"🎨 {topic}：脚本已生成，正在调用 DALL-E 3 配图...")
                final_script_with_images = factory.artist_agent(script, topic)
                
                # 保存到本地和数据库
                factory.save_to_db(topic, data, final_script_with_images)
                file_path = factory.save_to_markdown(topic, final_script_with_images)
                status.update(label=f"✅ {topic} 完成，文件存至: {file_path}", state="complete")
            
            st.markdown(f"### 📄 {topic} 最终脚本（含配图预览）")
            # 在 Streamlit 中完美展示含有图片链接的 Markdown
            st.markdown(final_script_with_images)
            st.divider()

    if st.button("查看数据库"):
        with sqlite3.connect('aigc_factory.db') as conn:
            df = pd.read_sql_query("SELECT topic, created_at FROM scripts ORDER BY created_at DESC", conn)
            st.table(df)
