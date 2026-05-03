# 🚀 Auto-AIGC-Factory: 多 Agent 协作的内容生产管线

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![DeepSeek](https://img.shields.io/badge/LLM-DeepSeek-green.svg)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-red.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

> 本项目是一个基于 **Multi-Agent（多智能体）架构**与 **Reflection（反思机制）** 构建的全自动短视频/爆款图文生成管线。

## 💡 项目背景与解决痛点
在矩阵化自媒体运营中，从热点追踪到脚本撰写的人工链路极长，且传统单次 Prompt 生成的内容往往缺乏“爆款逻辑”和“合规安全性”。
本项目通过引入多 Agent 博弈与 RAG 经验库检索，实现了 **“感知-推理-反思-生成”** 的无人值守闭环，将单条高质量脚本的产出时间从 4 小时压缩至 3 分钟。

## 🧠 核心逻辑流 (Workflow)
本项目由 3 个核心 Agent 协同工作：
1. **Trend Analyst (感知与分析 Agent)：** 接入全网实时热点数据，提取传播规律。
2. **Script Architect (编剧 Agent)：** 结合 RAG 向量库中的历史爆款法则，运用 CoT 思维链输出包含视觉指令 (Midjourney Prompts) 的分镜脚本。
3. **Critic & Auditor (毒舌操盘手 Agent)：** 模拟千万级网红操盘手，对生成的初稿进行严苛的逻辑与合规审查。**若不达标，将强制打回重写（支持多轮内部博弈迭代）。**

## 📊 Token 消耗模型与资源需求
由于本项目采用了 **长链推理** 与 **多轮审核打回机制**：
- 每次任务需在 Agent 间流转大量的 System Prompt、RAG 知识库与历史生成的长文本。
- 单次完整闭环运行的 Context 消耗量平均在 **60k - 120k Tokens**。
- 面对日均 1000+ 条实时热点的并发处理需求，对算力和 Token 额度有极高的持续性要求。

## 💻 本地运行与在线演示
本项目内置了基于 Streamlit 的可视化 Web 界面。

**安装依赖：**
```bash
pip install openai streamlit

<img width="1397" height="1409" alt="image" src="https://github.com/user-attachments/assets/4b1789c5-48bf-45d9-91cb-fcbcca6b5eac" />
