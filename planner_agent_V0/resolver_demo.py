import re

state = {
    "step1": 2023
}

template = "2026-{step1}"


def resolve(text):
    match = re.findall(r"\{(.*?)\}", text)

    for key in match:
        text = text.replace(
            "{" + key + "}",
            str(state[key])
        )

    return text


result = resolve(template)

print(result)