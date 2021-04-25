import websockets
import asyncio

async def hello(websocket, path):
    name = await websocket.recv()
    print("< {}".format(name))

start_server = websockets.serve(hello, 'wss://api-aws.huobi.pro/ws')

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
