import uvicorn

if __name__ == "__main__":
    print("Starting AI Trip Planner FastAPI Server...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
