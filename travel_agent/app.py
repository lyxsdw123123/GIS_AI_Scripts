"""旅行智能体 — Gradio 对话界面"""
from __future__ import annotations

import gradio as gr
from travel_agent.services.planner import run_agent


async def chat_fn(message: str, history: list) -> str:
    """
    Gradio ChatInterface 回调。
    history 格式: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    """
    if not message.strip():
        return "请告诉我你的需求吧 😊"

    # 转换 Gradio history → 内部格式
    internal_history = []
    for h in history:
        internal_history.append({"role": h["role"], "content": h["content"]})

    try:
        reply = await run_agent(message, internal_history)
        return reply or "抱歉，我好像卡住了，能换个方式再说一下吗？"
    except Exception as e:
        return f"出错了 😢\n{type(e).__name__}: {e}"


def create_app() -> gr.Blocks:
    with gr.Blocks(title="小旅 - 旅行智能体") as app:
        gr.Markdown(
            """
            <div class="travel-header">
            <h1>🧳 小旅 — 你的私人旅行规划师</h1>
            <p>告诉我你的位置和心情，我帮你发现身边的好去处</p>
            </div>
            """,
        )

        chat = gr.ChatInterface(
            fn=chat_fn,
            chatbot=gr.Chatbot(height=500),
            textbox=gr.Textbox(
                placeholder="比如：我在杭州西湖区，心情一般，有点累，想去安静的地方坐坐...",
                container=False,
                scale=7,
            ),
            title="",
            description="",
            examples=[
                "我在北京朝阳区，心情很好精力充沛，想看展或者逛有意思的胡同",
                "我在成都，有点累心情一般，想找个安静舒服的茶馆或书店呆着",
                "我在上海，和女朋友一起，想去浪漫一点的地方",
                "我在三亚，精力旺盛好奇心爆棚，推荐小众不要人多的景点",
            ],
            cache_examples=False,
        )

    return app


if __name__ == "__main__":
    app = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        theme=gr.themes.Soft(),
        css="""
        footer {display: none !important;}
        .travel-header {text-align: center; margin-bottom: 10px;}
        """,
    )
