from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from __004__langgraph_more_nodes.nodes.langgraph_more_nodes import zhongyi_response
from __03__msg_queue import msg_queue_manager,put_done_content,remove_msg_queue
import asyncio
import json
app = FastAPI()


@app.post("/process")
async def process(data: dict):
    input = data.get("input", "")
    user_id = data.get("user_id") or ""
    if not user_id:
        import uuid
        user_id = str(uuid.uuid4()) # 生成临时 user_id(随机数)
        print(f"未传 user_id，使用临时: {user_id}")
    else:
        print(f"输入>>>>>>>: {user_id}")

    return StreamingResponse(generate_data(input, user_id), media_type="text/plain")

async def my_zhongyi_project(input, user_id):
    output = ""
    try:
        output = await zhongyi_response(input, user_id)
    except Exception as e:
        output = f"回复生成异常：{e!s}"
    finally:
        # 把最终回复内容放进 done，前端可直接显示
        await put_done_content(user_id, output or "")

# 异步方法
async def generate_data(input, user_id):
    # 先拿到队列再起任务，保证生产者和消费者用的是同一个 queue
    queue = msg_queue_manager.get_msg_queue(user_id) # 获取队列
    asyncio.create_task(my_zhongyi_project(input, user_id))

    while True:
        msg = await queue.get() # 从指定队列中获取数据
        if msg is None:
            # 防御：若有人 put(None) 或异常，避免 msg.get 报错
            break
        print(msg)
        # 每行一个 JSON，方便前端按行解析
        yield json.dumps(msg, ensure_ascii=False) + "\n"
        if msg.get("type") == "done":
            remove_msg_queue(user_id)
            break


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000) # 启动异步服务
