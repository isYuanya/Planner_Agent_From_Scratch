def rag(query):

    if "DPO" in query:
        return "2023"
    if "温度" in query:
        return "25"
    return "unknown"


def calculator(expression):
    # 安全的数学计算：限制 eval 只能访问内置的数学运算
    return eval(expression, {"__builtins__": {}}, {})


TOOLS = {
    "rag": rag,
    "calculator": calculator
}