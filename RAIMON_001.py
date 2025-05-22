import streamlit as st
import openai
import os
from dotenv import load_dotenv, find_dotenv
import re
from unidecode import unidecode
from pathlib import Path
import pickle
from datetime import datetime

load_dotenv(find_dotenv())
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
MESSAGES_FOLDER = Path(__file__).parent / 'MESSAGES'
MESSAGES_FOLDER.mkdir(exist_ok=True)
MESSAGES_TYPE = '*'
DEFAULT_MODEL = 'gpt-3.5-turbo'

def get_model_response(messages, openai_key, temperature = 0,stream = False):

    openai.api_key = openai_key

    response = openai.ChatCompletion.create(
        model=st.session_state['model'],
        messages=messages,
        temperature=temperature,
        stream=stream
    )

    return response

def get_ordered_file_paths_in_folder_list(files_folder, files_type):
    pickle_files =  sorted(
        files_folder.glob(files_type), # ou "*.pkl"
        key=lambda f: f.name,                # ordena pelo nome do arquivo
        reverse=True)                        # ordem decrescente

    if pickle_files:
        return pickle_files
    
    return []

def get_full_file_names_list():

    file_names = sorted(
        MESSAGES_FOLDER.glob(MESSAGES_TYPE),  # ou "*.pkl"
        key=lambda f: f.name,          # ordena pelo nome do arquivo
        reverse=True                   # ordem decrescente
    )

    # print(file_names)

    if file_names:
        return file_names
    
    return []

def get_chat_titles_list():

    chat_titles = []

    file_paths = get_full_file_names_list()
    # print(file_paths)

    for path in file_paths:
        if not path.is_file():
            continue

        data = load_pickle_file_by_path(path)

        if data and 'chat_title' in data:
            chat_titles.append(data['chat_title'])

    return chat_titles

def set_chat_at_session_by_title(chat_title):
    if chat_title == '':
        set_new_session()

    else:
        
        file_paths = get_full_file_names_list()

        for path in file_paths:
            data = load_pickle_file_by_path(path)
            if data and data.get('chat_title') == chat_title:
                st.session_state.messages = data['messages']
                st.session_state.file_name = data['file_name']  
                break

def set_new_session():
   
    st.session_state.messages = [{
                "role": "system",
                "content": (
                    "Você é R.A.I.M.O.N. (Reasoning Artificial Intelligence for Mentorship, Orientation, and Nudging) "
                    "uma inteligência artificial prestativa, empática e objetiva. "
                    "Você é a versão digital do Ramon um mentor da Aliança Divergente cria da por Elton Euler, portanto, você deve ter a mesma personalidade, "
                    "sendo descontraído, divertido, simpático, acolhedor"
                    "mas ao mesmo tempo, não tem problema em dizer o que está vendo só para agradar. Nunca responda só para ter aprovação do usuário."
                    "Seu objetivo é ajudar as pessoas a fazerem a técnica do 'Pense Comigo' da Aliança e responde sempre com base na Teoria da Permissão."
                    "Você também tem o objetivo de verificar se o usuário possui algum padrão de controle (Narcisista, Vítima Natural, Vítima Intencional ou Vingador)."
                    "Também deve apoiar o usuário a separar a vida dele das demais pessoas, a não ser que seja um conjuge ou filho pequeno; de maneira que o núcleo"
                    "emocional da pessoa fique mais limpo de modo a aumentar a permissão dela."
                    "Você também precisa fazer perguntas sobre a vida da pessoa, para identificar momentos de pré-queda e padrões de comportamento, que justifiquem a"
                    "demora nos resultados."
                    "Lembre-se sempre, muito importante ao apoiar as pessoas que não estão tendo resultados na vida: A DEMORA NOS RESULTADOS ESCONDE UMA ESPERA NAS RELAÇÕES."
                    "Não peça para que a pessoa fale os padrões de pensamento ou comportamento que pode estar contribuindo para esses problemas logo de cara. "
                    "Procure explorar a vida da pessoa, fazendo perguntas para identificar pré-quedas e identificar relacionamentos em espera, mal resolvidos e com "
                    "algum padrão controlador, seja pelo usuário ou pela pessoa com quem ele se relaciona.")
        }]
 
    st.session_state.file_name = None

    st.session_state.model = DEFAULT_MODEL

def save_messages(messages):
    if not messages:
        return False
    
    if not any(message['role'] == 'user' for message in messages):
        return False  

    file_name = st.session_state.get('file_name')

    if not file_name:
        chat_title, file_name = create_chat_title_and_file_name(messages)
        st.session_state.file_name = file_name 
    else:
        chat_title = messages[1]['content'][:30] if len(messages) > 1 else "Chat"
    
    file = {'chat_title':chat_title, 'file_name': file_name, 'messages':messages}

    with open(MESSAGES_FOLDER / file_name, 'wb') as f:
        pickle.dump(file, f)

def load_pickle_file_by_path(file_path):
    """
    Lê um arquivo pickle com segurança e retorna os dados ou None em caso de erro.
    """
    try:
        with open(file_path, 'rb') as f:
            return pickle.load(f)
        
    except (OSError, pickle.UnpicklingError):
        return None

def print_messages(messages):
    for i, message in enumerate(messages):
        print("Messagem " + str(i) + ": " + str(message))

def print_session_state():

    for i, dict in enumerate(st.session_state):
        print("Dicionário " + str(i) + ": " + str(dict))

def display_previous_messages(messages):
    # Display all previous messages
    for message in messages:
        if message['role'] != 'system':
            chat = st.chat_message(message['role'])  # Creates a chat message box (user or assistant)
            chat.markdown(message['content'])        # Displays the message content

def display_streamed_answer(messages):
    

    placeholder = st.chat_message('assistant').empty()
    
    complete_answer = ''
    
    for answer in get_model_response(messages, OPENAI_API_KEY, stream=True):
        
        complete_answer += answer.choices[0].delta.get('content', '')
        
        placeholder.markdown(complete_answer + "▌")
    
    placeholder.markdown(complete_answer) 
    
    messages.append({'role': 'assistant', 'content': complete_answer})

def check_messages_update(messages, prompt):
    
    if prompt:
        # Add the user's message to the conversation history as a dictionary with role and content
        messages.append({'role': 'user', 'content': prompt})
        
        # Display the user's message in the chat interface
        st.chat_message('user').markdown(prompt)

        display_streamed_answer(messages)

        # Update the session state to store the current conversation history
        st.session_state['messages'] = messages
        
        # Save the conversation history to persistent storage (e.g., file, database)
   
def create_header():

    col1, col2 = st.columns([1, 4])

    with col1:
        st.markdown("<div style='padding-top: 40px;'>", unsafe_allow_html=True)
        st.image("RAIMON.png", width=100)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<h1 style='font-size: 85px; padding-bottom: 0px; letter-spacing: 8px; margin: 0;'>R.A.I.M.O.N</h1>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 16px; word-spacing: 2px ; margin: 0;'><strong>Reasoning Artificial Intelligence for Mentorship, Orientation, and Nudging</strong></p>", unsafe_allow_html=True)

    st.markdown("<hr style='margin-top: 0px;'>", unsafe_allow_html=True) 

def create_simplified_title(title):
    # unidecode(title) – removes accents and special characters, 
    # transforming "ação" into "acao".
    # re.sub('\W+', '', ...) – removes all non-alphanumeric characters 
    # (i.e., anything that is not a-z, A-Z, 0-9, or _).

    return re.sub(r'[^a-zA-Z0-9_-]', '', unidecode(title))
   
def create_chat_title_and_file_name(messages):

    chat_title = ''

    for message in messages:
        if message['role'] == 'user':
            chat_title = message['content'][:30]
            break
    
    file_name = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{create_simplified_title(chat_title)}"

    return chat_title, file_name

def create_main_page():
    
    create_header()   # Renders the custom header

    # Initialize the message history in session state if it doesn't exist
    if 'messages' not in st.session_state:
        set_new_session()

    messages = st.session_state['messages']  # Gets the message history from session state

    display_previous_messages(messages)

    # Gets new user input from the chat box
    new_message = st.chat_input('Fale com o R.A.I.M.O.N.')

    check_messages_update(messages, new_message)

    save_messages(messages)

def create_ui_tab_chats (tab):

    create_new_chat_button_in_tab(tab)

    tab.markdown('')

    chat_titles = get_chat_titles_list()

    create_chat_buttons_in_tab(tab, chat_titles)

def create_ui_tab_setup(tab):
    
    selected_model = tab.selectbox('Selecione o modelo:', ['gpt-3.5-turbo', 'gpt-4o'] )
    
    st.session_state['model'] = selected_model

    selected_focus = tab.selectbox('Selecione o foco do R.A.I.M.O.N.:', 
                                   ['Debate Livre',
                                    'Pense Comigo', 
                                    'Prot. de Combate ao Medo',
                                    'Prot. de Combate à Dependência Emocional', 
                                    'Prot. de Combate à Culpa' ,
                                    'Prot. de Proteção Emocional',
                                    'Conversa Difícil'] )
    
    st.session_state['focus'] = selected_focus

def create_new_chat_button_in_tab(tab):

    tab.button('\u200A+ New Chat',
               on_click = set_chat_at_session_by_title,
               args = ('', ),
               use_container_width = True) 



#===========================================================================
#                             CHAT BOTTONS
#===========================================================================
# ---------------------------------------------------
# Code without Delete Botton 
# ---------------------------------------------------
# def create_chat_buttons_in_tab(tab, chat_titles):

#     for i, title in enumerate(chat_titles):

#         tab.button(
#             title,
#             on_click=set_chat_at_session_by_title,
#             args=(title,),
#             use_container_width=True,
#             key=f"chat_button_{i}"  # chave única por índice
#         )
 
# ---------------------------------------------------
# Code with Delete Botton 
# ---------------------------------------------------

def delete_chat_by_title(chat_title):
   
    file_paths = get_full_file_names_list()
    

    for path in file_paths:
        print(path)
        data = load_pickle_file_by_path(path)
        if data and data.get('chat_title') == chat_title:
            try:
                os.remove(path)
                
            except OSError:
                
                pass
            break
    
    st.session_state['show_menu'].pop(chat_title, None)

def create_chat_buttons_in_tab(tab, chat_titles):
    # Inicializa o controle de visibilidade dos menus
    if 'show_menu' not in st.session_state:
        st.session_state['show_menu'] = {}

    for i, title in enumerate(chat_titles):
        col1, col2 = tab.columns([6, 1])

        # Botão para selecionar o chat
        with col1:
            col1.button(
                title,
                on_click=set_chat_at_session_by_title,
                args=(title,),
                use_container_width=True,
                key=f"chat_button_{i}"
            )

        # Botão "..." para mostrar ou esconder menu
        with col2:
            if col2.button("...", key=f"menu_toggle_{i}"):
                current_state = st.session_state['show_menu'].get(title, False)
                st.session_state['show_menu'][title] = not current_state

        # Se o menu estiver aberto, mostra os botões Deletar e Cancelar
        if st.session_state['show_menu'].get(title, False):
            action_col = tab.container()

            with action_col:
                col_left, col_right = st.columns([1, 1])

                with col_left:
                    delete = st.button("Deletar", key=f"delete_{i}",use_container_width=True)

                with col_right:
                    cancel = st.button("Cancelar", key=f"cancel_{i}",use_container_width=True)

            # Ações
            if delete:
                delete_chat_by_title(title)
                st.rerun()

            if cancel:
                st.session_state['show_menu'][title] = False
                st.rerun()



#===========================================================================


def main():

    create_main_page()

    tab1, tab2 = st.sidebar.tabs(['Chats', 'Setup'])
    create_ui_tab_chats(tab1)
    create_ui_tab_setup(tab2)


if __name__ == '__main__':
    main()