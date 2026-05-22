from typing import Dict
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from trip_planner.state import PlannerState
from trip_planner.agents.llm_config import get_llm
from trip_planner.prompts.supervisor_prompts import SUPERVISOR_SYSTEM_PROMPT, SUPERVISOR_USER_PROMPT

class RouterRoute(BaseModel):
    next: str = Field(description="The next agent to route to, or 'FINISH' if itinerary is complete") 

def supervisor_node(state: PlannerState) -> Dict:
    llm = get_llm()
    router_llm = llm.with_structured_output(RouterRoute)
    
    # Format the dynamic message mapping missing items clearly
    msg_content = SUPERVISOR_USER_PROMPT.format(
        weather_status="MISSING" if not state.get("weather_data") else "Acquired",
        transport_status="MISSING" if not state.get("transport_data") else "Acquired",
        activities_status="MISSING" if not state.get("activities_data") else "Acquired",
        budget_status="MISSING" if not state.get("budget_insights") else "Acquired",
        itinerary_status="MISSING" if not state.get("final_itinerary") else "Acquired",
    )

    res = router_llm.invoke([
        SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
        HumanMessage(content=msg_content)
    ])
    
    return {"next": res.next}
