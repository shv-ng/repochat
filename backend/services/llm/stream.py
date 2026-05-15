import logging

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_groq import ChatGroq
from services.vectorstore.chroma import QueryResult

SYSTEM_PROMPT = """You are a code assistant for the repo: {repo_url}.
Answer using ONLY the provided code context.
Always cite file_path when referencing code.
If answer not in context, say so — don't hallucinate."""

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7)
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder("history"),
        ("user", "{query}"),
    ]
)

chain = prompt | llm


def format_context(result: list[QueryResult]) -> str:
    return "\n\n".join(f"# {r.metadata['file_path']}\n\n{r.content}" for r in result)


def stream_answer(
    repo_url: str,
    query: str,
    context_results: list[QueryResult],
    history: list[dict],
):
    """Stream answer
    Args:
        repo_url (str): repo url
        query (str): query
        context_results (list[QueryResult]): context results
        history (list[dict]): history
    """
    logging.info(f"Streaming answer for {repo_url} with query: {query}")

    context = format_context(context_results)
    full_query = f"Context:\n{context}\n\nquery: {query}"

    for chunk in chain.stream(
        {
            "repo_url": repo_url,
            "query": full_query,
            "history": history,
        }
    ):
        yield chunk.content
