from typing import Dict, Any
import json
import logging
from langchain_core.messages import HumanMessage, SystemMessage
from trip_planner.state import PlannerState
from trip_planner.tools.weather import get_weather
from trip_planner.agents.llm_config import get_llm
from trip_planner.prompts.weather_prompts import WEATHER_AGENT_SYSTEM_PROMPT, WEATHER_AGENT_USER_PROMPT

logger = logging.getLogger(__name__)


def _extract_tool_args(tool_call: Any) -> Dict:
    # Support several possible tool_call shapes returned by LLM tool-calling
    if not tool_call:
        return {}
    # Common keys: 'args', 'arguments', 'kwargs'
    for key in ("args", "arguments", "kwargs"):
        if key in tool_call and tool_call[key]:
            args = tool_call[key]
            if isinstance(args, str):
                try:
                    return json.loads(args)
                except Exception:
                    # fallback: try eval-ish parse (very conservative)
                    try:
                        return json.loads(args.replace("'", '"'))
                    except Exception:
                        return {}
            if isinstance(args, dict):
                return args
    # Some models put the tool call payload in a single positional list
    if isinstance(tool_call, (list, tuple)) and len(tool_call) > 0:
        first = tool_call[0]
        if isinstance(first, dict):
            return first
    return {}


def weather_node(state: PlannerState) -> Dict[str, Any]:
    # Validate required fields
    required = ("destination", "start_date", "end_date")
    missing = [k for k in required if not state.get(k)]
    if missing:
        msg = f"Missing required state fields for weather: {', '.join(missing)}"
        logger.warning(msg)
        return {"weather_data": {"status": "error", "message": msg}}

    # Return cached weather if present
    if state.get("weather_data"):
        return {"weather_data": state["weather_data"]}

    # Prepare LLM and prompt
    llm = get_llm()
    try:
        llm = llm.bind_tools([get_weather])
    except Exception:
        # bind_tools may not be available on some LLM wrappers; continue without binding
        logger.debug("LLM does not support bind_tools; proceeding without tool registration")

    user_prompt = WEATHER_AGENT_USER_PROMPT.format(
        destination=state["destination"],
        start_date=state["start_date"],
        end_date=state["end_date"],
    )

    try:
        response = llm.invoke([
            SystemMessage(content=WEATHER_AGENT_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ])
    except Exception as exc:
        logger.exception("LLM invocation failed")
        return {"weather_data": {"status": "error", "message": f"LLM error: {exc}"}}

    # If the model used tool-calling, handle tool call
    tool_calls = getattr(response, "tool_calls", None)
    if tool_calls:
        tool_call = tool_calls[0]
        args = _extract_tool_args(tool_call)
        try:
            result = get_weather.invoke(args)
            return {"weather_data": result}
        except Exception as exc:
            logger.exception("Weather tool invocation failed")
            return {"weather_data": {"status": "error", "message": f"Tool error: {exc}"}}

    # Fallback: try to parse assistant text as JSON containing weather
    assistant_text = getattr(response, "content", None) or getattr(response, "text", None)
    if assistant_text:
        try:
            data = json.loads(assistant_text)
            if isinstance(data, dict) and "weather" in data or "daily" in data:
                return {"weather_data": data}
        except Exception:
            # Not JSON — return assistant text for debugging
            logger.debug("Assistant returned non-JSON content as fallback")
            return {"weather_data": {"status": "ok", "summary": assistant_text}}

    return {"weather_data": {"status": "error", "message": "Agent failed to call tool or return usable output."}}
