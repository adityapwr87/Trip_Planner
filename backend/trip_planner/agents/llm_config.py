from langchain_groq import ChatGroq
from trip_planner.config import GROQ_API_KEY, MODEL_NAME

def get_llm():
    """Returns a configured instance of the ChatGroq model."""
    # Using Llama 3.3 70B which natively supports very reliable tool calling
    model = "llama-3.3-70b-versatile" 
    return ChatGroq(model=model, api_key=GROQ_API_KEY)
