from typing import Dict
from datetime import datetime
import json
from langchain_core.messages import HumanMessage
from trip_planner.state import PlannerState
from trip_planner.agents.llm_config import get_llm
from trip_planner.prompts.budget_prompts import BUDGET_AGENT_PROMPT

def budget_node(state: PlannerState) -> Dict:
    llm = get_llm()
    
    # Calculate duration
    start = datetime.strptime(state['start_date'], "%Y-%m-%d")
    end = datetime.strptime(state['end_date'], "%Y-%m-%d")
    duration = (end - start).days + 1
    
    transport_data = state.get('transport_data', [])
    activities_data = state.get('activities_data', [])
    
    # Truncate context to avoid token limits
    transport_data_str = json.dumps(transport_data)[:2000] if transport_data else "[]"
    activities_data_str = json.dumps(activities_data)[:2000] if activities_data else "[]"

    prompt = BUDGET_AGENT_PROMPT.format(
        destination=state['destination'],
        duration=duration,
        start_date=state['start_date'],
        end_date=state['end_date'],
        budget=state['budget_limit'],
        user_preferences=state.get('user_preferences', ""),
        transport_data=transport_data_str,
        activities_data=activities_data_str
    )
    
    res = llm.invoke([HumanMessage(content=prompt)])
    return {"budget_insights": res.content}
