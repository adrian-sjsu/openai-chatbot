"""
PART 4

https://rohitraj-iit.medium.com/part-two-how-to-chat-with-your-documents-in-a-local-chatbot-using-openai-api-6f4285a4e11a 

In this article I will show step by step how to create a local chatbot which can take multiple files as input. 
Our chatbot would be able to answer our questions using information contained in files.

To achieve our goal I will modify my code in part one in following four steps

a) In part one, I used gradio chatinterface. In this step, I will use gradio block interface to enable more flexibility in our code

b) In the second step, I will add streaming support to our chatbot. Instead of waiting for the entire output of OpenAi API. 
Our chatbot will start replying as early as possible

c) In the third step, I will add support for uploading a single text file as input.

d) In the final step , I will allow adding multiple files as input where each file can be either Word doc, a PDF or a text file.
"""


import gradio as gr
from openai import OpenAI
import docx2txt
import PyPDF2

# remember to pip install os
# remember to pip install python-dotenv
import os
from dotenv import load_dotenv
load_dotenv()
api_key  = os.environ.get('OPENAI_API_KEY')  # In file .env, replace with your own key


def read_text_from_file(file_path):
    # Check the file type and read accordingly
    if file_path.endswith('.docx'):
        text = docx2txt.process(file_path)
    elif file_path.endswith('.pdf'):
        with open(file_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ''
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()
    elif file_path.endswith('.txt'):
        with open(file_path, 'r', encoding='utf-8') as txt_file:
            text = txt_file.read()

    
    return text

with gr.Blocks() as demo:
    gr.Markdown("""<h1><center>SJSU ChatGPT ChatBot</center></h1> """)
    chatbot = gr.Chatbot(placeholder="<strong>My name is Spartan V1.0</strong><br>I am here to help you with your class.")
    msg = gr.Textbox(placeholder="What can I help you?")
    clear = gr.Button("Clear")
    filename = gr.File(file_count='multiple')

    def user(user_message, history):
        return "", history + [[user_message, None]]

    def bot(msg, history,filename):
        history_openai_format = []

        if filename is not None:
            for files in filename:
                file_contents = read_text_from_file(files)
                history_openai_format.append({"role": "user", "content": file_contents })

        
        for human, assistant in history:
            history_openai_format.append({"role": "user", "content": human })
            if assistant is not None:
                history_openai_format.append({"role": "assistant", "content":assistant})
        
        client = OpenAI(
        api_key=api_key,)
        response = client.chat.completions.create(
        messages=history_openai_format,
        # model="gpt-3.5-turbo" # gpt 3.5 turbo
        # model="gpt-4",
        model = "gpt-4o-mini-2024-07-18", #gpt-4-mini
        stream = True
        )
        history[-1][1] = ""
        partial_message = ""
        for chunk in response:
            text = (chunk.choices[0].delta.content)
            if text is not None:
                for character in text:
                        history[-1][1] += character
                        yield history

    msg.submit(user, [msg, chatbot], [msg, chatbot], queue=False).then(bot, [msg, chatbot,filename], chatbot)
    clear.click(lambda: None, None, chatbot, queue=False)
    
demo.queue()
demo.launch()