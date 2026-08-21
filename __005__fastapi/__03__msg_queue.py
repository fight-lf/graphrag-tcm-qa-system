import asyncio


# 键 设置成user_id, 值
# 队列管理器
class MsgQueueManager:
    def __init__(self):
        self.msg_queue_dict = {}   # 缓存用户ID,通过队列里面是否有user_id,来判断是否已经存在队列

    # 获取或者是创建队列(user_id)
    def get_msg_queue(self, user_id):
        if user_id not in self.msg_queue_dict:
            self.msg_queue_dict[user_id] = asyncio.Queue() # 创建队列
        return self.msg_queue_dict[user_id]

    def del_msg_queue(self, user_id):
        if user_id in self.msg_queue_dict:
            del self.msg_queue_dict[user_id]


msg_queue_manager = MsgQueueManager()


# async def put_msg_content(user_id, put_content):
#     await msg_queue_manager.get_msg_queue(user_id).put({"type": "msg", "msg": put_content})
#     await asyncio.sleep(0.1)


# 往队列添加内容-标识(思考)
async def put_msg_sentence_content(user_id, put_content):
    await msg_queue_manager.get_msg_queue(user_id).put({"type": "msg", "msg": put_content})
    await asyncio.sleep(0.1)
    await msg_queue_manager.get_msg_queue(user_id).put({"type": "msg", "msg": "\n"})
    await asyncio.sleep(0.1)

# 往队列添加内容-回复(大模型)(响应)
async def put_reply_content(user_id, put_content):
    await msg_queue_manager.get_msg_queue(user_id).put({"type": "reply", "msg": put_content})
    await asyncio.sleep(0.1)

# 结束任务,表示流程结束
async def put_done_content(user_id, final_output=""):
    """结束流时传入最终回复内容，前端若未收到 reply 可用 done 的 msg 显示。"""
    await msg_queue_manager.get_msg_queue(user_id).put({"type": "done", "msg": final_output or ""})
    await asyncio.sleep(0.1)

def remove_msg_queue(user_id):
    msg_queue_manager.del_msg_queue(user_id)
