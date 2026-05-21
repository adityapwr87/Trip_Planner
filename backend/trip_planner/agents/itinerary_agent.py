import json
from typing import Dict

from langchain_core.messages import HumanMessage, SystemMessage
from trip_planner.state import PlannerState
from trip_planner.agents.llm_config import get_llm
from trip_planner.prompts.itinerary_prompts import (
    ITINERARY_AGENT_SYSTEM_PROMPT,
    ITINERARY_AGENT_USER_PROMPT,
)

def itinerary_node(state: PlannerState) -> Dict:
    llm = get_llm()
    
    weather_data = state.get('weather_data', [])
    transport_data = state.get('transport_data', [])
    activities_data = state.get('activities_data', [])
    budget_insights = state.get('budget_insights', "")
    
    # Truncate context to avoid token limits
    weather_data_str = json.dumps(weather_data)[:2000] if weather_data else "[]"
    transport_data_str = json.dumps(transport_data)[:2500] if transport_data else "[]"
    activities_data_str = json.dumps(activities_data)[:4000] if activities_data else "[]"
    budget_insights_str = str(budget_insights)[:2000]
    
    prompt = ITINERARY_AGENT_USER_PROMPT.format(
        destination=state['destination'],
        start_date=state['start_date'],
        end_date=state['end_date'],
        user_preferences=state.get('user_preferences', ""),
        weather_data=weather_data_str,
        transport_data=transport_data_str,
        budget_insights=budget_insights_str,
        activities_data=activities_data_str
    )
    
    res = llm.invoke([
        SystemMessage(content=ITINERARY_AGENT_SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ])
    return {"final_itinerary": res.content}
