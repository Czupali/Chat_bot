import gradio as gr
import requests

RASA_URL = "http://localhost:5005/webhooks/rest/webhook"

def chat_with_rasa(message, history):
    payload = {"sender": "user", "message": message}
    try:
        response = requests.post(RASA_URL, json=payload)
        response.raise_for_status()
        data = response.json()
        bot_reply = "\n".join([d["text"] for d in data if "text" in d])
    except Exception as e:
        bot_reply = f"⚠️ Error: {e}"
    history.append((message, bot_reply))
    return history, history

with gr.Blocks() as demo:
    gr.Markdown("## 🤖 AI Chatbot (Rasa + Gradio)")
    chatbot = gr.Chatbot()
    msg = gr.Textbox(label="Your message")
    clear_btn = gr.Button("Clear")

    state = gr.State([])

    msg.submit(chat_with_rasa, [msg, state], [chatbot, state])
    clear_btn.click(lambda: ([], []), None, [chatbot, state])

if __name__ == "__main__":
    demo.launch()
