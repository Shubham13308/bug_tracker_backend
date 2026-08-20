from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connection:dict[str, WebSocket] = {}
    async def connect(self,user_id:str,ws:WebSocket):
        await ws.accept()
        self.active_connection[user_id] = ws
    def disconnect(self,user_id:str):
        self.active_connection.pop(user_id,None)

    async def send_to_user(self,user_id:str,message:str):
        ws = self.active_connection.get(user_id)
        if ws:
            await ws.send_json(message)
manager = ConnectionManager()
    