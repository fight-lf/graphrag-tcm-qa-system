from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.staticfiles import StaticFiles

from __004__langgraph_more_nodes.nodes.langgraph_more_nodes import zhongyi_response
from common.path_utils import get_file_path

app = FastAPI()
app.mount("/picture", StaticFiles(directory=get_file_path("picture")))


@app.post("/process")
async def process(request: Request):
    data = await request.json()
    user_input = data.get("input", "")
    user_id = data.get("user_id", "default_user")

    try:
        output = await zhongyi_response(user_input, user_id)
        result = {
            "input": user_input,
            "output": output,
        }
    except Exception:
        import traceback
        traceback.print_exc()
        result = {
            "input": user_input,
            "output": "系统出错了，请重试！",
        }

    return JSONResponse(content=result)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
