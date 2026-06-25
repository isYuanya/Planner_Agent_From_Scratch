def rag(query):

    if "DPO" in query:
        return "2023"
    if "温度" in query:
        return "25"
    return "unknown"

TOOLS = {
    "rag": rag,

}