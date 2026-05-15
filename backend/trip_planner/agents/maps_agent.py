from typing import Dict
from langchain_core.messages import HumanMessage, SystemMessage
from trip_planner.state import PlannerState
from trip_planner.tools.maps import get_transport_options
from trip_planner.agents.llm_config import get_llm
from trip_planner.prompts.maps_prompts import MAPS_AGENT_SYSTEM_PROMPT, MAPS_AGENT_USER_PROMPT

def maps_node(state: PlannerState) -> Dict:
    llm = get_llm().bind_tools([get_transport_options])
    
    user_prompt = MAPS_AGENT_USER_PROMPT.format(
        origin=state['origin'],
        destination=state['destination']
    )
    
    response = llm.invoke([
        SystemMessage(content=MAPS_AGENT_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt)
    ])
    
    if response.tool_calls:
        tool_call = response.tool_calls[0]
        tool_result = get_transport_options.invoke(tool_call["args"])
        return {"transport_data": tool_result}
    
    return {"transport_data": {"status": "error", "message": "Agent failed to call tool."}}
