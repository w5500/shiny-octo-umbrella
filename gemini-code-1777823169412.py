import asyncio
import os
import datetime
from typing import List, Dict
from openai import OpenAI

# ⚠️ 强烈建议：运行成功后请去 DeepSeek 后台重置你的 API Key，避免被盗刷
client = OpenAI(
    api_key="sk-ad4c1fe9fb8d42a596a07738affeff80", 
    base_url="https://api.deepseek.com" # 已修正 URL，去掉了冒号
)

class ContentFactory:
    def __init__(self):
        # 使用 DeepSeek 标准聊天模型
        self.model = "deepseek-chat" 

    # ================= 阶段 1：感知与检索层 =================
    
    async def fetch_real_time_trends(self, query: str) -> str:
        """【新增功能】感知层：模拟调用 Tavily/Serper 搜索 API 获取实时网络数据"""
        print(f"[感知层] 正在全网检索 '{query}' 的实时热点与讨论...")
        await asyncio.sleep(1) # 模拟网络请求延迟
        # 在真实应用中，这里会替换为 httpx 对搜索引擎 API 的调用
        mock_search_results = f"全网搜索结果：近期关于'{query}'的讨论热度极高。核心争议点在于AI安全性、对人类就业的冲击，网友普遍带有焦虑且期待的复杂情绪。某大V发布的预测视频获得了百万点赞。"
        return mock_search_results

    async def retrieve_successful_cases(self, topic: str) -> str:
        """【新增功能】检索层：模拟 RAG 从向量数据库获取历史爆款经验"""
        print(f"[检索层] 正在从内部知识库匹配相关的爆款方法论...")
        await asyncio.sleep(0.5)
        mock_rag_content = "爆款知识库提示：1. 黄金前3秒必须制造强烈的视觉反差或提出颠覆常理的疑问；2. 视频中间加入具体的数据或引发共鸣的痛点；3. 结尾必须抛出开放性问题引导评论区互动。"
        return mock_rag_content

    # ================= 阶段 2：长链推理与编排层 =================

    async def trend_analyzer_agent(self, raw_data: str) -> str:
        """Agent 1: 趋势分析专家 - 提取爆款因子"""
        print("[Agent 1] 趋势分析专家正在提炼核心爆款逻辑...")
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个资深趋势分析师。请从提供的数据中提取3个核心爆款逻辑，并判定其传播潜力。"},
                {"role": "user", "content": raw_data}
            ]
        )
        return response.choices[0].message.content

    async def script_writer_agent(self, analysis: str, rag_guidelines: str) -> str:
        """Agent 2: 创意编剧 - 撰写脚本并生成【视觉指令】"""
        print("[Agent 2] 创意编剧正在基于趋势和爆款法则撰写分镜脚本...")
        
        system_prompt = (
            "你是一个短视频爆款编剧。请根据趋势分析和爆款法则，写一个完整的短视频内容脚本。\n"
            "【强制要求】：\n"
            "1. 脚本必须分为表格或分段形式（包含：秒数、画面描述、旁白/字幕、背景音乐）。\n"
            "2. 针对每一个重要画面，必须提供一段英文的 Midjourney/Sora 图像提示词（以 [Image Prompt: xxx] 的格式放在画面描述后）。"
        )
        
        user_prompt = f"【爆款法则参考】\n{rag_guidelines}\n\n【趋势分析结果】\n{analysis}"
        
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        return response.choices[0].message.content

    async def critic_agent(self, script: str) -> Dict:
        """Agent 3: 审核与反思专家 - 自我迭代"""
        print("[Agent 3] 审核专家正在对脚本进行合规性与爆款潜力毒舌审查...")
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个挑剔的千万级网红操盘手。请指出剧本中不够吸引人、逻辑漏洞或违规风险的地方，给出具体修改建议。如果脚本已经具备爆款潜质且完美，请必须在回复开头包含大写的 'PASS'。"},
                {"role": "user", "content": script}
            ]
        )
        feedback = response.choices[0].message.content
        return {"passed": "PASS" in feedback.upper(), "feedback": feedback}

    # ================= 阶段 3：动作层 =================

    def export_to_file(self, content: str, topic: str):
        """【新增功能】动作层：将最终成果输出为 Markdown 文件"""
        # 确保存在一个输出文件夹
        os.makedirs("output_scripts", exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"output_scripts/爆款脚本_{topic.replace(' ', '')}_{timestamp}.md"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# 自动生成 AIGC 脚本主题：{topic}\n")
            f.write(f"> 生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(content)
            
        print(f"\n🎉 [动作层] 任务完成！脚本已成功保存到本地文件: {filename}")

    # ================= 核心管线调度 =================

    async def run_pipeline(self, topic_query: str):
        """执行端到端多 Agent 任务流"""
        print(">>> 🚀 启动全自动内容生产管线 <<<\n")
        
        # 1. 外部数据获取
        real_time_data = await self.fetch_real_time_trends(topic_query)
        rag_guidelines = await self.retrieve_successful_cases(topic_query)
        
        # 2. 趋势分析
        trend_analysis = await self.trend_analyzer_agent(real_time_data)
        print("  -> 趋势提炼完成。")
        
        # 3. 初始脚本生成 (结合了热点分析和爆款知识库)
        script = await self.script_writer_agent(trend_analysis, rag_guidelines)
        
        # 4. 闭环反馈循环 (Reflection 架构)
        max_retries = 3
        for i in range(max_retries):
            review = await self.critic_agent(script)
            if review["passed"]:
                print(f"  ✅ 脚本通过操盘手审核 (总迭代次数: {i})")
                break
            else:
                print(f"  ⚠️ 第 {i+1} 次审核未通过，编剧正在根据毒舌建议回炉重造...")
                # 带着反馈重写
                script = await self.script_writer_agent(
                    analysis=trend_analysis, 
                    rag_guidelines=f"原脚本: {script}\n\n操盘手修改建议: {review['feedback']}"
                )
        
        # 5. 动作执行：保存文件
        self.export_to_file(script, topic_query)
        
        return script

# --- 运行入口 ---
if __name__ == "__main__":
    factory = ContentFactory()
    
    # 你可以在这里修改你想做的主题
    target_topic = "2026年AI全自动驾驶"
    
    # 运行异步管线
    asyncio.run(factory.run_pipeline(target_topic))