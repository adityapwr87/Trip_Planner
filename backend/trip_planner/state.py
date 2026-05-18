import operator
from typing import TypedDict, Annotated, Sequence, Any
from langchain_core.messages import BaseMessage

class PlannerState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    origin: str
    destination: str
    start_date: str
    end_date: str
    budget_limit: int
    user_preferences: str
    
    # Store partial results for context
    weather_data: Any
    transport_data: Any
    activities_data: Any
    budget_insights: str
    final_itinerary: str

    # Next node to execute
    next: str
