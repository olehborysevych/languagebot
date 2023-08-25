import telebot
import requests
import openai     
import os
import langchain

from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

source_language_prompt = PromptTemplate(
    template="""Your task to say in what language user input is written. 
    User input is located inside <<<>>> tag. .
    Ignore all the words related to the names of languages, countries or nationalities in user input. 
    If no language name is infered from the user input, output English
    You should produce only a single word - name of the inferred language in Enlish
    
    User input: <<<{description}>>>
    
    
    """,
    input_variables=["description"],
)

target_language_prompt = PromptTemplate(
    template="""Your task to say what language is explicitly mentioned in user input.  
    User input is located inside <<<>>> tag. 
    If some language or nationality name or mentioned in the input, output corresponding language name.
    If no language name or nationality is present in user input then output "German"
    You should produce only a single word - name of the inferred language in Enlish
    Never output the language in which the user input is written. Output German instead
    
    User input: <<< {description} >>>
    
    """,
    input_variables=["description"],
)

dialog_creator_prompt = PromptTemplate(
    template = """You are a native speaker and teacher of {target_language}. You've been presented with a situation description encapsulated by <<<>>> tags. The situation might be conveyed as a thorough description or just a few pivotal keywords and phrases.

Based on the given context, you need to model a situation by given description and prepare several dialogs in {target_language} that appropriately represent real life communication in this context.

Your response should encompass:

Phrases: Provide 7-10 essential phrases in {target_language} language pertinent to the situation. For each word provide a phonetic transcription, translation in {source_language}.

Dialogues: Construct and output two distinctive dialogs in {target_language} with inline translation to {source_language}. Dialogs should pertain to the given situation. Each dialogue should consist of at least 6 lines. Ensure the dialogues account for various outcomes — positive, negative, or neutral.

Key Vocabulary: Identify and list 7-10 pivotal words for this situation. For each word provide a phonetic transcription, translation in {source_language}, grammatical annotations. Each pivotal word should be presented in the following format: pivotal word [transcription] - translation, grammatic annotaion.

Language Usage: Ensure the vocabulary and dialogues employ colloquial language consistent with typical informal conversations. Dialogs should be fun to read.

The entirety of your response should only consist of content in {target_language} and {source_language}. Refrain from introducing any other languages.

Situation Description: <<<{description}>>>

""",
input_variables=["description", "target_language", "source_language"],
)

# take tokens from environment variables
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
BOT_TOKEN = os.environ['BOT_TOKEN']


openai.api_key  = OPENAI_API_KEY
llm = OpenAI(openai_api_key=OPENAI_API_KEY, model='text-davinci-003', temperature=0.0, max_tokens = -1)

source_language_chain = LLMChain(llm=llm, prompt=source_language_prompt)
target_language_chain = LLMChain(llm=llm, prompt=target_language_prompt)
dialog_creator_chain = LLMChain(llm=llm, prompt=dialog_creator_prompt)

bot = telebot.TeleBot(BOT_TOKEN)
    
def germandialogcreatorbot(request):
    print(request.json)
    prompt = ""
        
    if request.method == "POST":
        
        message = request.json["message"]
        message_id = message["message_id"]
        chat = message["chat"]
        chat_id = chat["id"]
        bot.send_chat_action(chat_id=chat_id, action="typing")
        
        # process voice message
        if request.json.get("message", {}).get("voice"):
            voice = message["voice"]
            file_info = bot.get_file(voice["file_id"])
            voice_file = bot.download_file(file_info.file_path)
            file_name = str(message_id) + ".ogg"
            
            with open(file_name, "wb") as f:
                # Write bytes to file
                f.write(voice_file)
            
            with open(file_name, 'rb') as f:
                result = openai.Audio.transcribe("whisper-1", f)
                prompt = result["text"]
            
            os.remove(file_name)
            
        elif request.json.get("message", {}).get("text"):
            message_text = message["text"]
            prompt = message_text
        
        if not prompt:
            bot.send_message(chat_id=chat_id, text="Sorry, I didn't understand you. Please try again.")
            return "ok"
        
        source_lang = source_language_chain.run(prompt)
        target_lang = target_language_chain.run(prompt)
        dialog_response = dialog_creator_chain.run(description = prompt, target_language=target_lang, source_language=source_lang)
        
        while dialog_response:
            # Send the first 4096 characters and then remove them from the response
            bot.send_message(chat_id=chat_id, text=dialog_response[:4096])
            dialog_response = dialog_response[4096:]
                
    return "ok"


