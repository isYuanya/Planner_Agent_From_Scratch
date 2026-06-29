from tavily import TavilyClient

client = TavilyClient(
    api_key="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"
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