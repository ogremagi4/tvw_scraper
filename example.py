import asyncio
import websockets
from queue import Queue
import logging
from functools import partial
from concurrent.futures import ThreadPoolExecutor
import time

logging.basicConfig(format='%(asctime)-15s %(threadName)s %(message)s')
logger = logging.getLogger("")
logger.setLevel(logging.DEBUG)

class Application:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=8)

    def getExecutor(self):
        return self.executor
    
    def close(self):
        self.executor.shutdown()


class Client:
    
    ###########################################################################
    # Business Logic
        
    def sendMessage(self, message):
        self.messageQueue.put(message)
    
    async def consumer(self, message):
        logger.debug(f"Consumed message {message}")
        
    ###########################################################################
    
    ###########################################################################
    # General
    
    def __init__(self, app):
        
        self.app = app
        
        self.messageQueue = Queue()
        self.ws = None
    
    async def producer(self):
        logger.debug("In producer")
        return self.messageQueue.get()
    
    
    def connect(self, uri):
        self.app.getExecutor().submit(partial(self._connect, uri))
    
    def _connect(self, uri):
        asyncio.run(self.__connect(uri), debug=True)
    
    async def __connect(self, uri):
        self.loop = asyncio.get_event_loop()
        logger.debug("Connecting")
        self.ws = await websockets.connect(uri)  
        await self.handler(self.ws, uri)
    
    def close(self):
        asyncio.run_coroutine_threadsafe(self.__close(), self.loop)

    async def __close(self):
        logger.debug("Ending client")
        await self.ws.close()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # remaining part of class is from 
    # https://websockets.readthedocs.io/en/stable/intro.html#both

    async def consumer_handler(self, websocket, path):
        try:
            logger.debug("Beginning consumer")
            async for message in websocket:
                logger.debug(f"Recieved message {message}")
                await self.consumer(message)
        finally:
            logger.debug("Ended consumer")

            
    async def producer_handler(self, websocket, path):
        logger.debug("Beginning producer")
        try:
            while True:
                message = await self.producer()
                await websocket.send(message)
                logger.debug(f"Sent: {message}")
                await asyncio.sleep(1)
        finally:
            logger.debug("Ended producer")
            

    async def handler(self, websocket, path):
        '''This simply schedules the sequential execution of the producer_task
        and consumer_task. It does NOT run them in parallel!'''
        producer_task = asyncio.ensure_future(
            self.producer_handler(websocket, path))
        consumer_task = asyncio.ensure_future(
            self.consumer_handler(websocket, path))
        done, pending = await asyncio.wait(
            [consumer_task, producer_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()

def main():
    
    ADDRESS = "ws://echo.websocket.org/"
    
    logger.debug("Beginning client")
    
    app = Application()
    try:
        client = Client(app)
        try:
            client.connect(ADDRESS)
        