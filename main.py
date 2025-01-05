import os
import asyncio
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.models.gemini import GeminiModel
import PyPDF2
import docx

class DebateManager:
    def __init__(self, openai_api_key, gemini_api_key):
        self._initialize_agents(openai_api_key, gemini_api_key)

    def _initialize_agents(self, openai_api_key, gemini_api_key):
        openai_model = OpenAIModel(
            "gpt-4o-mini",
            api_key=openai_api_key
        )
        gemini_model = GeminiModel(
            "gemini-2.0-flash-exp",
            api_key=gemini_api_key
        )
        
        self.openai_agent = Agent(model=openai_model)
        self.gemini_agent = Agent(model=gemini_model)
    
    def run_debate(self, topic, affirmative_doc, negative_doc, num_rounds=3):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        try:
            debate_history = []
            debate_outputs = []
            
            openai_prompt = f"You are arguing FOR {topic}. Refer to the following background document: {affirmative_doc}. Be concise (within 100 words)."
            gemini_prompt = f"You are arguing AGAINST {topic}. Refer to the following background document: {negative_doc}. Be concise (within 100 words)."
            
            for round in range(num_rounds):
                result = self.openai_agent.run_sync(openai_prompt, message_history=debate_history)
                pro_response = result.data
                debate_history.extend(result.new_messages())
                debate_outputs.append(("affirmative", pro_response))
                
                result = self.gemini_agent.run_sync(gemini_prompt, message_history=debate_history)
                against_response = result.data
                debate_history.extend(result.new_messages())
                debate_outputs.append(("negative", against_response))
                
                openai_prompt = f"Review the full debate history and respond to the latest argument from the Negative. Refer to {negative_doc} and attack points that might suport the negative side. Continue arguing FOR {topic}. Be concise (within 100 words)."
                gemini_prompt = f"Review the full debate history and respond to the latest argument from the Affirmative. Refer to {affirmative_doc} and attack points that might suport the affirmative side. Continue arguing AGAINST {topic}. Be concise (within 100 words)."
            
            summary_prompt = f"Summarize the key points from both sides of this debate about {topic}, and provide a balanced conclusion. Be concise (within 200 words)."
            summary_result = self.openai_agent.run_sync(summary_prompt, message_history=debate_history)
            summary = summary_result.data
        
            return debate_outputs, summary
        
        except Exception as e:
            return None, None

def extract_text_from_file(uploaded_file):
    """
    Extracts text from a single uploaded file.
    :param uploaded_file: File-like object uploaded via Streamlit.
    :return: Extracted text from the file or an empty string if the file type is unsupported.
    """
    try:
        if uploaded_file.type == "application/pdf":
            reader = PyPDF2.PdfReader(uploaded_file)
            return " ".join(page.extract_text() for page in reader.pages if page.extract_text())
        elif uploaded_file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
            doc = docx.Document(uploaded_file)
            return " ".join([para.text for para in doc.paragraphs])
        elif uploaded_file.type == "text/plain":
            return str(uploaded_file.read(), "utf-8")
        else:
            return ""
    except Exception as e:
        return ""

def extract_text_from_multiple_files(uploaded_files):
    """
    Extracts and combines text from multiple uploaded files.
    :param uploaded_files: List of file-like objects uploaded via Streamlit.
    :return: Combined text from all files.
    """
    extracted_text = [extract_text_from_file(file) for file in uploaded_files]
    return " ".join(extracted_text)