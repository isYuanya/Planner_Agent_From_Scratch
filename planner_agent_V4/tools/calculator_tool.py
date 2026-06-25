import ast
import operator


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

    return calculator.calculate(expression)