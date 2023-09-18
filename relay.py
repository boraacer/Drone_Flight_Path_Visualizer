import asyncio
import atexit
import websockets
import threading
import sys

class WebSocketServer:

    def __init__(self, host="localhost", port=8765):
        self.host = host
        self.port = port
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.start_asyncio)  # Reference to the thread

    async def echo(self, websocket, path):
        async for message in websocket:
            print(f"Received message: {message}")
            await websocket.send(f"Echo: {message}")

    def start_asyncio(self):
        # Set the new event loop for this thread
        asyncio.set_event_loop(self.loop)
        
        start_server = websockets.serve(self.echo, self.host, self.port)
        
        self.loop.run_until_complete(start_server)
        self.loop.run_forever()

    def start(self):
        self.thread = threading.Thread(target=self.start_asyncio)
        self.thread.start()
        print(f"WebSocketServer started on thread {self.thread.name} on port {self.port}")

    def stop(self):
        atexit.register(self.loop.call_soon_threadsafe, self.loop.stop)
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(0))
        print(f"WebSocketServer stopped on thread {self.thread.name} on port {self.port}")

        
if __name__ == "__main__":
    server = WebSocketServer(port=8765)
    server.start()
