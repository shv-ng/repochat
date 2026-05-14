from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from dotenv import load_dotenv
from langchain_groq import ChatGroq

from embed import QueryResult

load_dotenv()

SYSTEM_PROMPT = """You are a code assistant for the repo: {repo_url}.
Answer using ONLY the provided code context.
Always cite file_path when referencing code.
If answer not in context, say so — don't hallucinate."""

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7)
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder("history"),
        ("user", "{question}"),
    ]
)

chain = prompt | llm


def format_context(result: list[QueryResult]) -> str:
    return "\n\n".join(f"# {r.metadata['file_path']}\n\n{r.content}" for r in result)
