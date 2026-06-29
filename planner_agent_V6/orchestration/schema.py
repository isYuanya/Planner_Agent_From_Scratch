PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "plan": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string"
                    },
                    "tool": {
                        "type": "string"
                    },
                    "input": {
                        "type": "string"
                    }
                },
                "required": [
                    "id",
                    "tool",
                    "input"
                ],
                "additionalProperties": False
            }
        }
    },
    "required": [
        "plan"
    ],
    "additionalProperties": False
}