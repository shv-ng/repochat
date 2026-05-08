from dotenv import load_dotenv
from embed import Embed
from langchain.agents import create_agent
from langchain_groq import ChatGroq
from pydantic import BaseModel, ConfigDict

load_dotenv()

"""
TODO:
- prompt likhna h
- query seach kr k prompt k sath dena h
- user id/auth setup
- add chat/history
- add redis for progress
"""


class Context(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    embed: Embed


llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7)

SYSTEM_PROMPT = """ """

agent = create_agent(
    model=llm,
    tools=[],
    system_prompt=SYSTEM_PROMPT,
    context_schema=Context,
)

github_url = "https://github.com/shv-ng/frec"
embed = Embed(github_url)

response = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "Find the exact logic and value used for the starred item score multiplier.",
            },
        ],
    },
    context=Context(embed=embed),
)

print(response)
