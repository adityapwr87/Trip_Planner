import warnings
from langgraph.graph import StateGraph, START, END
from trip_planner.state import PlannerState
from trip_planner.agents.supervisor import supervisor_node
from trip_planner.agents.weather_agent import weather_node
from trip_planner.agents.maps_agent import maps_node
from trip_planner.agents.activities_agent import activities_node
from trip_planner.agents.budget_agent import budget_node
from trip_planner.agents.itinerary_agent import itinerary_node

warnings.filterwarnings("ignore")

# Define Graph
builder = StateGraph(PlannerState)

# Add Nodes
builder.add_node("Supervisor", supervisor_node)
builder.add_node("WeatherAgent", weather_node)
builder.add_node("MapsAgent", maps_node)
builder.add_node("ActivitiesAgent", activities_node)
builder.add_node("BudgetAgent", budget_node)
builder.add_node("ItineraryAgent", itinerary_node)

# Add edges from Supervisor to Workers and back
def router_edge(state: PlannerState) -> str:
    # Look at the 'next' key left by supervisor
    next_node = state.get("next")
    
    mapping = {
        "WeatherAgent": "WeatherAgent",
        "MapsAgent": "MapsAgent",
        "ActivitiesAgent": "ActivitiesAgent",
        "BudgetAgent": "BudgetAgent",
        "ItineraryAgent": "ItineraryAgent",
        "FINISH": END
    }
    
    return mapping.get(next_node, END)

builder.add_edge(START, "Supervisor")

# Route back to supervisor after workers
builder.add_conditional_edges("Supervisor", router_edge)

builder.add_edge("WeatherAgent", "Supervisor")
builder.add_edge("MapsAgent", "Supervisor")
builder.add_edge("ActivitiesAgent", "Supervisor")
builder.add_edge("BudgetAgent", "Supervisor")
builder.add_edge("ItineraryAgent", "Supervisor")

graph = builder.compile()

def run_planner(origin: str, dest: str, start: str, end: str, budget: int):
    initial_state = {
        "messages": [],
        "origin": origin,
        "destination": dest,
        "start_date": start,
        "end_date": end,
        "budget_limit": budget,
        "weather_data": None,
        "transport_data": None,
        "activities_data": None,
        "budget_insights": None,
        "final_itinerary": None,
        "next": "Supervisor"
    }

    # Execute graph
    print("Starting Trip Planner Multi-Agent Flow...")
    for event in graph.stream(initial_state, {"recursion_limit": 20}):
        node_name = list(event.keys())[0]
        print(f"--- Finished executing: {node_name} ---")
        if node_name == "ItineraryAgent":
            print("\n================ FINAL ITINERARY ================\n")
            print(event["ItineraryAgent"].get("final_itinerary"))
            break
            
    return event