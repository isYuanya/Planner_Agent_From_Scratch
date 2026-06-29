import os
from tavily import TavilyClient

client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY", "")
)


def web_search_tool(query):

    result = client.search(
        query=query,
        search_depth="basic",
        max_results=5
    )

    contents = []

    for item in result["results"]:

        contents.append(
            item["content"]
        )

    return "\n".join(contents)