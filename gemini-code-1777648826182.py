import asyncio
from typing import List, Dict
from openai import OpenAI

# 初始化客户端 (此处可替换为任意支持 OpenAI 格式的 API 端点)
client = OpenAI(api_key="sk-ad4c1fe9fb8d42a596a07738affeff80", base_url="https://api.deepseek.com")

class ContentFactory:
    def __init__(self):
        self.model = "deepseek-v4-pro" # 建议使用具备长链推理能力的模型

    async def trend_analyzer_agent(self, raw_data: str) -> str:
        """Agent 1: 趋势分析专家 - 负责从海量信息中提取爆款因子"""
        print("[Agent 1] 正在分析全球社交媒体热点...")
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个资深趋势分析师。请从数据中提取3个核心爆款逻辑，并判定其传播潜力。"},
                {"role": "user", "content": raw_data}
            ]
        )
        return response.choices[0].message.content

    async def script_writer_agent(self, analysis: str) -> str:
        """Agent 2: 创意编剧 - 负责撰写多版本脚本"""
        print("[Agent 2] 正在基于分析结果撰写视频脚本...")
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个短视频爆款编剧。请根据趋势分析，写一个包含视觉指令和对白的内容脚本。"},
                {"role": "user", "content": analysis}
            ]
        )
        return response.choices[0].message.content

    async def critic_agent(self, script: str) -> Dict:
        """Agent 3: 审核与反思专家 - 模拟监管和观众反馈进行自我迭代"""
        print("[Agent 3] 正在对脚本进行合规性与爆款潜力审查...")
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个挑剔的审核员。请指出脚本中的逻辑漏洞或违规风险，并给出修改建议。如果脚本完美，请回复'PASS'。"},
                {"role": "user", "content": script}
            ]
        )
        feedback = response.choices[0].message.content
        return {"passed": "PASS" in feedback.upper(), "feedback": feedback}

    async def run_pipeline(self, raw_input: str):
        """执行长链推理任务流"""
        # 1. 趋势分析
        trend_analysis = await self.trend_analyzer_agent(raw_input)
        
        # 2. 初始脚本生成
        script = await self.script_writer_agent(trend_analysis)
        
        # 3. 闭环反馈循环 (反思架构)
        max_retries = 3
        for i in range(max_retries):
            review = await self.critic_agent(script)
            if review["passed"]:
                print(f"\n✅ 脚本通过审核 (迭代次数: {i})")
                break
            else:
                print(f"⚠️ 第 {i+1} 次审核未通过，正在根据建议重写...")
                # 带着反馈重写，体现长链推理
                script = await self.script_writer_agent(f"原脚本: {script}\n修改建议: {review['feedback']}")
        
        return script

# --- 模拟运行 ---
if __name__ == "__main__":
    factory = ContentFactory()
    raw_trending_topics = "2026年AI全自动驾驶在硅谷普及，用户对安全性有争议，同时对未来生活充满好奇。"
    
    final_output = asyncio.run(factory.run_pipeline(raw_trending_topics))
    
    print("\n--- 最终生成的 Agent 产出成果 ---")
    print(final_output)