import os
import datetime
import requests
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

    def fetch_real_time_trends(self, query: str) -> str:
        """【重大升级】接入 Tavily API 进行真实的实时全网搜索"""
        if not self.search_api_key:
            return f"【模拟数据】近期关于'{query}'的讨论热度极高。争议点在于落地速度和安全性。（提示：在左侧配置 Tavily API Key 以解锁真实网络搜索）"
        
        try:
            # 调用 Tavily Search API
            url = "https://api.tavily.com/search"
            payload = {
                "api_key": self.search_api_key,
                "query": f"最新社交媒体爆款讨论与趋势：{query}",
                "search_depth": "advanced",
                "include_answer": True,
                "max_results": 5
            }
            response = requests.post(url, json=payload).json()
            
            # 提取搜索结果并拼接给大模型
            results = "\n".join([f"- {res['title']}: {res['content']}" for res in response.get("results", [])])
            ai_answer = response.get('answer', '')
            
            return f"【Tavily 实时全网搜索结果】\n综合AI总结: {ai_answer}\n\n具体信息源:\n{results}"
        except Exception as e:
            return f"搜索 API 调用异常: {str(e)}。已临时回退到基础模式。"

    def retrieve_successful_cases(self, topic: str) -> str:
        return "爆款知识库提示：\n1. 黄金前3秒必须制造强烈的视觉反差或提出颠覆常理的疑问；\n2. 视频中间加入具体的数据或引发共鸣的痛点；\n3. 结尾必须抛出开放性问题引导评论区站队互动。"

    def _call_llm(self, messages: list) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"API 调用异常: {str(e)}"

    def trend_analyzer_agent(self, raw_data: str) -> str:
        """【提示词升级】强制输出结构化的爆款拆解逻辑"""
        system_prompt = (
            "你是一个拥有千万粉丝操盘经验的资深趋势分析师。\n"
            "请从提供的全网实时搜索数据中，提取出3个最容易引发病毒式传播的『爆款逻辑』。\n"
            "请严格按以下结构输出：\n"
            "1. 🎯 核心情绪痛点（用户的恐惧、焦虑、猎奇或渴望）\n"
            "2. 💥 制造冲突与反常识的切入点\n"
            "3. 👁️ 视觉与听觉呈现建议（什么画面最抓人眼球）\n"
            "4. 📈 整体传播潜力评估（打分及理由）"
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": raw_data}
        ]
        return self._call_llm(messages)

    def script_writer_agent(self, analysis: str, rag_guidelines: str, previous_feedback: str = "") -> str:
        """【提示词升级】强化工业级标准，严格约束 Markdown 表格与高质量图像提示词"""
        system_prompt = (
            "你是一个工业级短视频爆款编剧。请严格根据『趋势分析』和『爆款法则』，输出直接可用于生产的分镜脚本。\n"
            "【执行强制指令】：\n"
            "1. 遵循『黄金3秒原则』，开头必须极度抓人眼球。\n"
            "2. 脚本必须采用 Markdown 表格形式，表头必须是：| 镜头编号 | 时长 | 画面分镜描述 | 旁白/字幕 | 音效/BGM | 图像提示词(Midjourney) |\n"
            "3. 【极度重要】Midjourney图像提示词必须是专业的英文描述，格式为：[Image Prompt: subject, environment, lighting, camera angle, style, 8k, highly detailed --ar 16:9]。\n"
            "4. 绝不要输出多余的寒暄，直接输出表格。"
        )
        
        user_prompt = f"【内部爆款法则】\n{rag_guidelines}\n\n【最新全网趋势分析】\n{analysis}"
        if previous_feedback:
            user_prompt += f"\n\n【！！！操盘手打回修改意见，请务必解决以下痛点】\n{previous_feedback}"
            
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        return self._call_llm(messages)

    def critic_agent(self, script: str) -> Dict:
        """【提示词升级】赋予极度苛刻的人设，保障出片质量"""
        system_prompt = (
            "你是字节跳动/抖音级别的 S 级内容审核官与爆款操盘手。你需要对编剧提交的脚本进行极为苛刻的『毒舌审查』。\n"
            "【你的审查维度】：\n"
            "1. 完播率预估：前3秒够不够刺激？会不会让人划走？\n"
            "2. 情绪张力：对白是否太平淡？能否激发评论区的激烈争论？\n"
            "3. 视觉可行性：英文图像提示词是否专业且有表现力？\n\n"
            "【输出规则】：\n"
            "如果你发现任何平庸、拖沓之处，请极其尖锐地指出，并给出具体的『重写指导指令』。\n"
            "【只有当脚本完美无瑕，让你觉得必定大爆时】，你才可以并且必须在回复的【第一行】仅输出大写的 'PASS'。其余情况绝不能输出 PASS。"
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": script}
        ]
        feedback = self._call_llm(messages)
        
        if "API 调用异常" in feedback:
            return {"passed": False, "feedback": feedback}
        return {"passed": feedback.strip().startswith("PASS"), "feedback": feedback}


# ================= Web 界面构建 =================
st.title("🚀 多 Agent 爆款内容全自动生产线")
st.markdown("基于大模型的长链推理与实时网络感知，一键生成带有视觉指令的工业级分镜脚本。")

with st.sidebar:
    st.header("⚙️ 引擎配置")
    api_key = st.text_input("大模型 API Key", placeholder="输入您的 API Key", type="password")
    base_url = st.text_input("Base URL", value="https://api.deepseek.com")
    model_name = st.text_input("模型名称", value="deepseek-chat")
    
    st.divider()
    st.header("🌐 外部工具配置")
    search_api_key = st.text_input("Tavily Search API (选填)", placeholder="输入 Tavily 密钥获取真实网络数据", type="password")
    st.caption("前往 tavily.com 免费获取，留空则使用模拟网络数据。")

topic_query = st.text_input("💡 请输入你想创作的爆款主题：", value="2026年AI全自动驾驶在硅谷普及")

if st.button("启动 Multi-Agent 引擎", type="primary", use_container_width=True):
    if not api_key:
        st.error("请先在左侧边栏配置有效的 大模型 API Key！")
    else:
        factory = ContentFactoryWeb(api_key, base_url, model_name, search_api_key)
        
        with st.status("🔗 管线运行中，正在调动算力...", expanded=True) as status:
            
            st.write("🌍 **[感知层]** 正在驱动智能体抓取全网实时热点与 RAG 经验库...")
            real_time_data = factory.fetch_real_time_trends(topic_query)
            
            st.write("🧠 **[Agent 1: 趋势专家]** 正在拆解爆款情绪点与冲突矩阵...")
            trend_analysis = factory.trend_analyzer_agent(real_time_data)
            
            st.write("✍️ **[Agent 2: 工业级编剧]** 正在起草包含 Midjourney 专业级指令的分镜表格...")
            script = factory.script_writer_agent(trend_analysis, rag_guidelines=factory.retrieve_successful_cases(topic_query))
            
            st.write("⚖️ **[Agent 3: 毒舌操盘手]** 正在对脚本进行降维打击式审核...")
            max_retries = 3
            passed = False
            for i in range(max_retries):
                if "API 调用异常" in script:
                    st.error("编剧 Agent 发生异常，管线终止。")
                    break
                    
                st.write(f"> 🔄 第 {i+1} 轮质量抗压测试中...")
                review = factory.critic_agent(script)
                
                if review["passed"]:
                    st.write("✅ 操盘手审核通过！已达成工业级爆款标准。")
                    passed = True
                    break
                else:
                    # 提取部分毒舌反馈展示给用户
                    feedback_preview = review['feedback'][:80].replace('\n', ' ')
                    st.write(f"⚠️ 遭到驳回！操盘手痛批：_{feedback_preview}..._ \n> 编剧正在含泪重写...")
                    script = factory.script_writer_agent(
                        analysis=trend_analysis, 
                        rag_guidelines=factory.retrieve_successful_cases(topic_query),
                        previous_feedback=f"原脚本:\n{script}\n\n操盘手修改建议:\n{review['feedback']}"
                    )
            
            if not passed and "API 调用异常" not in script:
                st.write("⚠️ 达到最大内部博弈次数，已输出当前最高质量妥协版本。")

            status.update(label="🎉 工业级脚本生产完毕！", state="complete", expanded=False)

        st.subheader("📝 最终生成的爆款分镜脚本")
        st.markdown(script)
        
        st.download_button(
            label="💾 下载 Markdown 脚本文件",
            data=script,
            file_name=f"爆款脚本_{topic_query}.md",
            mime="text/markdown"
        )