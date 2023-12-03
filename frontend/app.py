import io
import openai
from openai import OpenAI

import streamlit as st
import pandas as pd
import os
import time
import tempfile
import requests
import csv
import json
from PIL import Image

def init():
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "run" not in st.session_state:
        st.session_state.run = None

    if "file_ids" not in st.session_state:
        st.session_state.file_ids = []
    
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = None

def set_apikey():
    st.sidebar.header('Configure')
    api_entry = st.sidebar.text_input("Enter your OpenAI API key", type="password")
    if api_entry:
        os.environ["OPENAI_API_KEY"] = api_entry

    return True
    

def config(client):
    my_assistants = client.beta.assistants.list(
        order="desc",
        limit="20",
    )
    assistants = my_assistants.data
    assistants_dict = {"Create Assistant": "create-assistant"}
    for assistant in assistants:
        assistants_dict[assistant.name] = assistant.id
    print(assistants_dict)
    assistant_option = st.sidebar.selectbox("Select Assistant", options=list(assistants_dict.keys()))
    return assistants_dict[assistant_option]

def upload_file(client, assistant_id, uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_file.close()
        with open(tmp_file.name, "rb") as f:
            response = client.files.create(
            file=f,
            purpose = 'assistants'
            )
            print(response)
            os.remove(tmp_file.name)
    assistant_file = client.beta.assistants.files.create(
        assistant_id=assistant_id,
        file_id=response.id,
    )
    return assistant_file.id
        
def assistant_handler(client, assistant_id):
    def delete_file(file_id):
        client.beta.assistants.files.delete(
                    assistant_id=assistant_id,
                    file_id=file_id,
                ) 

    
    assistant = client.beta.assistants.retrieve(assistant_id)
    with st.sidebar:
        assistant_name = st.text_input("Name", value = assistant.name)
        assistant_instructions = st.text_area("Instructions", value=assistant.instructions)
        model_option = st.sidebar.radio("Model", ('gpt-4', 'gpt-3.5-turbo', 'gpt-3.5-turbo-1106', 'gpt-4-1106-preview'))
        st.subheader("Files")
        grid = st.columns(2)
        print(assistant.file_ids)
        for file_id in assistant.file_ids:
            with grid[0]:
                st.text(file_id)
            with grid[1]:
                st.button("Delete", on_click = delete_file(file_id), key = file_id)
        uploaded_file = st.file_uploader("Upload a file", type=["txt", "csv"])
    
        if st.button("Update Assistant"):
            assistant = client.beta.assistants.update(
                assistant_id,
                instructions = assistant_instructions,
                name = assistant_name,
                model = model_option,

            )   
            if uploaded_file is not None:
                new_file_id = upload_file(client, assistant_id, uploaded_file)
                print(new_file_id)
                st.session_state.file_ids.append(new_file_id)
            st.success("Assistant updated successfully")
    return assistant, model_option, assistant_instructions

def create_assistant(client):
    assistants_dict = {"Create Assistant": "create-assistant"}
    assistant_name = st.text_input("Name")
    assistant_instructions = st.text_area("Instructions")
    model_option = st.radio("Model", ('gpt-4', 'gpt-3.5-turbo', 'gpt-3.5-turbo-1106', 'gpt-4-1106-preview'))
    def create_new_assistant():
        new_assistant = client.beta.assistants.create(
            name=assistant_name,
            instructions=assistant_instructions,
            model=model_option,
            tools =[
                {
                    "type": "code_interpreter",
                }
            ]
        )

    my_assistants = client.beta.assistants.list(
        order="desc",
        limit="20",
    ).data
    assistants_dict = {"Create Assistant": "create-assistant"}
    for assistant in my_assistants:
        assistants_dict[assistant.name] = assistant.id
    if assistant_name not in assistants_dict:
        new_assistant = st.button("Create Assistant", on_click=create_new_assistant)
        if new_assistant:
            my_assistants = client.beta.assistants.list(
                order="desc",
                limit="20",
            ).data
            assistants_dict = {"Create Assistant": "create-assistant"}
            for assistant in my_assistants:
                assistants_dict[assistant.name] = assistant.id
            st.success("Assistant created successfully")
            st.stop()
            print(assistants_dict)
            print("\n NEW: ", assistants_dict[assistant_name])
            return assistants_dict[assistant_name]
    else:
        st.warning("Assistant name does exist in assistants_dict. Please choose another name.")
             
def chat_prompt(client, assistant_option):
    if prompt := st.chat_input("Enter your message here"):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages = st.session_state.messages.append(client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="user",
            content=prompt,
        ))

        st.session_state.current_assistant = client.beta.assistants.update(
            st.session_state.current_assistant.id,
            instructions=st.session_state.assistant_instructions,
            name=st.session_state.current_assistant.name,
            tools = st.session_state.current_assistant.tools,
            model=st.session_state.model_option,
            file_ids=st.session_state.file_ids,
        )


        st.session_state.run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=assistant_option,
            tools = [{"type": "code_interpreter"}],

        )
        
        print(st.session_state.run)
        pending = False
        while st.session_state.run.status != "completed":
            if not pending:
                with st.chat_message("assistant"):
                    st.markdown("AnalAssist is thinking...")
                pending = True
            time.sleep(3)
            st.session_state.run = client.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id,
                run_id=st.session_state.run.id,
            )
            
             
                    
        if st.session_state.run.status == "completed": 
            st.empty()
            chat_display(client)

def chat_display(client):
    st.session_state.messages = client.beta.threads.messages.list(
        thread_id=st.session_state.thread_id
    ).data

    #Used this for debugging
    # x = 0
    # for message in st.session_state.messages:
    #     print(x)
    #     print(message)
    #     x += 1

    for message in reversed(st.session_state.messages):
        if message.role in ["user", "assistant"]:
            with st.chat_message(message.role):
                for content in message.content:
                    if content.type == "text":
                        st.markdown(content.text.value)
                    elif content.type == "image_file":
                        image_file = content.image_file.file_id
                        image_data = client.files.content(image_file)
                        image_data = image_data.read()
                        #save image to temp file
                        temp_file = tempfile.NamedTemporaryFile(delete=False)
                        temp_file.write(image_data)
                        temp_file.close()
                        #display image
                        image = Image.open(temp_file.name)
                        st.image(image)
                    else:
                        st.markdown(content)
                    
    

    # with st.chat_message("assistant"):
    #         st.markdown(st.session_state.messages.data.content)
    #st.write(st.session_state.messages)
    # for message in reversed(st.session_state.messages):
    #     if message[0] in ["user", "assistant"]:
    #         with st.chat_message(message[0]):
    #             st.markdown(message[1])

def main():
    st.title('AI AnalAssist 📈')
    st.caption('Data analysis assistant using OpenAI Assistants API')
    st.divider()
    api_key = set_apikey()
    if api_key:
        client = OpenAI()
        assistant_option = config(client)

        if assistant_option == "create-assistant":
            print ("Create assistant")
            with st.sidebar:
                assistant_option = create_assistant(client)
                print(assistant_option)
        else:
            print ("Use existing assistant")
            st.session_state.current_assistant, st.session_state.model_option, st.session_state.assistant_instructions = assistant_handler(client, assistant_option)
            if st.session_state.thread_id is None:
                st.session_state.thread_id = client.beta.threads.create().id
                print(st.session_state.thread_id)
            chat_prompt(client, assistant_option)
            
    else:
        st.warning("Please enter your OpenAI API key")
             


if __name__ == '__main__':
    init()
    main() 
    print(st.session_state.file_ids)




