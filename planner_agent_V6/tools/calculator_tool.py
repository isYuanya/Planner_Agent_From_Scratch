import ast
import operator
import re


class SafeCalculator:

    OPS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
    }

    def calculate(self, expression: str):

        node = ast.parse(
            expression,
            mode="eval"
        )

        return self._eval(node.body)

    def _eval(self, node):

        if isinstance(node, ast.Constant):
            return node.value

        if isinstance(node, ast.BinOp):

            left = self._eval(node.left)

            right = self._eval(node.right)

            op = self.OPS[type(node.op)]

            return op(left, right)

        raise ValueError(
            f"非法表达式: {type(node)}"
        )


calculator = SafeCalculator()


def calculator_tool(expression: str):
    """
    安全计算器入口 —— 带输入清洗 (仅对含自然语言的长文本)。

    当 VariableResolver 将 RAG 返回的段落替换到数学表达式时
    (如 "2026-DPO 是 2023 年提出的。..."),
    自动提取纯数学部分; 短 ASCII 表达式直接走 AST 白名单校验。
    """
    # 仅当输入明显是自然语言时才清洗 (含中文 / CJK 标点 / 换行)
    if re.search(r"[一-鿿　-〿\n。，！？；：]", expression):
        cleaned = re.sub(r"[^\d+\-*/().%]", "", expression).strip()
        if not cleaned:
            raise ValueError(f"无法从输入中提取有效数学表达式: {expression[:60]}")
        expression = cleaned

    return calculator.calculate(expression)