from openai import OpenAI
from dotenv import load_dotenv
from myTools import *
import json
import os

# load all environment varibles
load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPEN_AI_TOKEN")
)

# fast LLM model
MODEL = "gpt-5.4-mini"

AVAILABLE_FUNCTIONS = {
    "get_weather": get_weather_by_city,
}
 

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a given city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The city name, e.g. 'Toronto'",
                    }
                },
                "required": ["city"],
            },
        },
    }
]
 
 
def run_agent(user_message: str, max_turns: int = 5) -> str:
    # prompt engineering
    messages = [
        {"role": "system", "content": """
        You are a helpful assistant that works for the Toronto District School Board (TDSB) 
        staff to show them the weather.

        ## Role
        You support TDSB employees (teachers, administrators, custodial staff, transportation 
        coordinators, and office staff) who need accurate, current weather information to make 
        decisions about: outdoor activities, recess, field trips, bus routes, school closures, 
        and general planning.

        ## Tool Use
        You have access to a weather-fetching tool. Follow this reasoning process:
        1. Identify the location the user is asking about. If no location is given, ask which city
        2. You explain the weather data to the user like a new reporter
        3. If the tool fails or returns incomplete data, tell the user plainly rather than 
        filling gaps with assumptions.

        ## Response Requirements
        When you return weather information, you must give it in FULL DETAIL, not just a 
        one-line summary. Staff are making real operational decisions (recess, buses, outdoor 
        events) based on your answer, so vague responses like "It's cold today" are not 
        acceptable. Always include, where available:
        - Current temperature and "feels like" temperature
        - Sky conditions (sunny, overcast, rain, snow, etc.)
        - Wind speed and direction
        - Precipitation chance/amount
        - Humidity
        - Any relevant alerts (extreme cold, storm, air quality)
        - A brief practical note (e.g., "Recommend indoor recess" or "Bus delays possible 
        due to snow accumulation") when conditions are notable

        ## Tone
        Professional, clear, and concise — but complete. Avoid jargon. Write for staff who 
        need to act on this information quickly, not meteorologists.
        You are a helpful assistant that works for the Toronto District School Board (TDSB) 
        staff to show them the weather.
         
        PLEASE RETURN A MEDIUM SIZED PARAGRAPH DESCRIBING THE WEATHER, DO NOT PRINT IT OUT AND JUST DISPLAY, but do remember you are in a terminal so do not return markdown.
        """},
        {"role": "user", "content": user_message},
    ]
 
    for _ in range(max_turns):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
        )
        msg = response.choices[0].message
 
        
        if not msg.tool_calls:
            return msg.content
 
        
        messages.append(msg)
 
        
        for tool_call in msg.tool_calls:
            fn_name = tool_call.function.name
            fn_args = json.loads(tool_call.function.arguments or "{}")
            fn = AVAILABLE_FUNCTIONS.get(fn_name)
 
            if fn is None:
                result = f"Error: unknown tool '{fn_name}'"
            else:
                result = fn(**fn_args)
 
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result),
                }
            )
 
    return "Max turns reached without a final answer."
 
 
if __name__ == "__main__":
    print("Simple Tool-Calling Agent (type 'quit' to exit)\n")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"quit", "exit"}:
            break
        answer = run_agent(user_input)
        print(f"\nAgent: {answer}\n")