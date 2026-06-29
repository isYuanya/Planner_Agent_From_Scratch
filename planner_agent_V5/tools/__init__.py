from .rag_tool import rag_tool
from .calculator_tool import calculator_tool
from .weather_tool import weather_tool
from .db_tool import db_tool

TOOLS = {
    "rag": rag_tool,
    "calculator": calculator_tool,
    "weather": weather_tool,
    "db": db_tool,
}