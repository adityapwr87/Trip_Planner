from typing import Dict
from langchain_core.messages import HumanMessage, SystemMessage
from trip_planner.state import PlannerState
from trip_planner.tools.activities import destination_activities
from trip_planner.agents.llm_config import get_llm
from trip_planner.prompts.activities_prompts import ACTIVITIES_AGENT_SYSTEM_PROMPT, ACTIVITIES_AGENT_USER_PROMPT

def activities_node(state: PlannerState) -> Dict:
    llm = get_llm().bind_tools([destination_activities])
    
    user_prompt = ACTIVITIES_AGENT_USER_PROMPT.format(
        destination=state['destination'],
        user_preferences=state.get('user_preferences', "")
    )
    
    response = llm.invoke([
        SystemMessage(content=ACTIVITIES_AGENT_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt)
    ])
    
    if response.tool_calls:
        tool_call = response.tool_calls[0]
        tool_result = destination_activities.invoke(tool_call["args"])
        return {"activities_data": tool_result}
    
    return {"activities_data": {"status": "error", "message": "Agent failed to call tool."}}
