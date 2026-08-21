import requests


def query_zhongyi_fastapi(input: str) -> str:
    url = "http://127.0.0.1:8000/process"
    payload = {"input": input,'user_id':'user_001'}

    res = requests.post(url, json=payload)
    json_dict = res.json()
    return json_dict["output"]


print(query_zhongyi_fastapi("大枣"))
