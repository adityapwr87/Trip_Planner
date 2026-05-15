from typing import Dict
from langchain_core.messages import HumanMessage, SystemMessage
from trip_planner.state import PlannerState
from trip_planner.tools.weather import get_weather
from trip_planner.agents.llm_config import get_llm
from trip_planner.prompts.weather_prompts import WEATHER_AGENT_SYSTEM_PROMPT, WEATHER_AGENT_USER_PROMPT

def weather_node(state: PlannerState) -> Dict:
    llm = get_llm().bind_tools([get_weather])
    
    user_prompt = WEATHER_AGENT_USER_PROMPT.format(
        destination=state['destination'],
        start_date=state['start_date'],
        end_date=state['end_date']
    )
    
    response = llm.invoke([
        SystemMessage(content=WEATHER_AGENT_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt)
    ])
    
    if response.tool_calls:
        tool_call = response.tool_calls[0]
        tool_result = get_weather.invoke(tool_call["args"])
        return {"weather_data": tool_result}
    
    return {"weather_data": {"status": "error", "message": "Agent failed to call tool."}}
