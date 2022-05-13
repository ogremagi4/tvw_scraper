import websockets
import json
import regex
import string
import random
import asyncio
from .schemas import *

json_rgx = regex.compile(r'''
(?(DEFINE)
(?P<json>(\s*(?&object)\s*|\s*(?&array)\s*))
(?P<object>(\{\s*((?&pair)(\s*,\s*(?&pair))*)?\s*\}))
(?P<pair>((?&STRING)\s*:\s*(?&value)))
(?P<array>(\[\s*((?&value)(\s*,\s*(?&value))*)?\s*\]))
(?P<value>(true|false|null|(?&STRING)|(?&NUMBER)|(?&object)|(?&array)))
(?P<STRING>("(\\?!(["\\bfnrt]|u[a-fA-F0-9]{4})|[^"\0-\x1F\x7F]+)*"))
(?P<NUMBER>(\-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?))
)
(?&json)
''', regex.VERBOSE | regex.MULTILINE)

class TradingviewBase:
    websocket_url = 'wss://data.tradingview.com/socket.io/websocket'

class TradingViewWsMessages:
    
    def create_message(self, func_name, param_list):
        return self.prepend_header(self.construct_message(func_name, param_list))
    
    def prepend_header(self, st):
        return "~m~" + str(len(st)) + "~m~" + st

    def construct_message(self, func_name, param_list):
        return json.dumps({
            "m":func_name,
            "p":param_list
            }, separators=(',', ':'))
    
    def set_auth_token(self, token):
        message = self.create_message('set_auth_token',[token])
        return message

    def chart_create_session(self, chart_session_string):
        message = self.create_message('chart_create_session',[chart_session_string, ""])
        return message

    def resolve_symbol(self, chart_session_string, tradingview_symbol):#
        symbol_param  = f'={json.dumps({"symbol":tradingview_symbol, "adjustment":"splits"})}'.replace('"','\"')
        message = self.create_message('resolve_symbol', [chart_session_string, 'sds_sym_1', symbol_param])#TODO maybe you'd make symbol_{index} and use it somehow
        return message
    
    def create_series(self, chart_session_string, tradingview_timeframe, limit=5000):
        message = self.create_message('create_series', [chart_session_string, "sds_1", "s1", "sds_sym_1", tradingview_timeframe, 300, "12M"])#TODO map arguments insetad of hardcode
        return message
    
    def quote_fast_symbols(self, quote_session_string, tradingview_symbol):
        message = self.create_message('quote_fast_symbols', [quote_session_string,tradingview_symbol])
        return message
    
    def set_data_quality(self, quality):
        message = self.create_message('set_data_quality', [quality])
        return message
    
    def quote_create_session(self, quote_session_string):
        message = self.create_message('quote_create_session', [quote_session_string])
        return message
    
    def quote_add_symbols(self, quote_session_string, tradingview_symbol):
        message = self.create_message('quote_add_symbols', [quote_session_string,tradingview_symbol])
        return message
    

class TradingviewWsScraper(TradingviewBase):

    headers =  {
        # 'Connection': 'upgrade',
        # 'Host': 'data.tradingview.com',
        'Origin': 'https://data.tradingview.com'
        # 'Cache-Control': 'no-cache',
        # 'Upgrade': 'websocket',
        # 'Sec-WebSocket-Extensions': 'permessage-deflate; client_max_window_bits',
        # 'Sec-WebSocket-Key': '2C08Ri6FwFQw2p4198F/TA==',
        # 'Sec-WebSocket-Version': '13',
        # 'User-Agent': 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36 Edg/83.0.478.56',
        # 'Pragma': 'no-cache',
        # 'Upgrade': 'websocket'
    }


    def __init__(self, token = 'unauthorized_user_token') -> None:
        self.token = token
        self.messages = TradingViewWsMessages()
        self.queue = asyncio.Queue()
    
    def _generate_session(self, prefix = 'qs_'):
        string_length=12
        letters = string.ascii_lowercase
        digits = string.digits
        random_string= ''.join(random.choice(letters+digits) for i in range(string_length))
        return prefix + random_string

    def chart_session(self):
        return self._generate_session(prefix='cs_')
    
    def quote_session(self):
        return self._generate_session(prefix='qs_')
        
    def message_handler(self, message: str):
        return [json.loads(i) for i in json_rgx.findall(message.replace('\\"',''))]
        


    async def get_candles(self, tradingview_symbol:str, tradingview_timeframe):
        chart_session_string = self.chart_session()

        messages = [self.messages.set_auth_token(self.token), 
                    self.messages.set_data_quality('low'),
                    self.messages.chart_create_session(chart_session_string), 
                    self.messages.resolve_symbol(chart_session_string, tradingview_symbol),
                    self.messages.create_series(chart_session_string,
                     tradingview_timeframe)]
        
        async with websockets.connect(self.websocket_url, extra_headers=self.headers) as connection:#TODO make a generic iterator
            for message in messages:#TODO wrap it somehow to a separate method sending and receiving messages
                await connection.send(message)
            while True:
                response = await connection.recv()
                for item in self.message_handler(response):
                    try:
                        timescale_update = factory.load(item, TimescaleUpdateMessage)
                        return timescale_update.symbol_data_series.ohlcv
                    except (TypeError, ValueError):
                        await asyncio.sleep(0)
                        continue#XXX play with exceptions a bit
    
    async def get_symbol(self, tradingview_symbol:str):#TODO add bonds support
        """
        retrieve symbol info (descriptions, currency, etc)
        """
        quote_session_string = self.quote_session()

        messages = [self.messages.set_auth_token(self.token), 
                    self.messages.set_data_quality('low'),
                    self.messages.quote_create_session(quote_session_string),
                    self.messages.quote_add_symbols(quote_session_string, tradingview_symbol),
                    self.messages.quote_fast_symbols(quote_session_string, tradingview_symbol)]
        
        async with websockets.connect(self.websocket_url, extra_headers=self.headers) as connection: #TODO make a generic iterator
            for message in messages:#
                await connection.send(message)
            while True:
                response = await connection.recv()
                for item in self.message_handler(response):
                    try:
                        while not 'main_data' in locals():
                            main_data = factory.load(item, MainData)
                        additional_data = factory.load(item, AdditionalData)
                        return CombinedSymbolInfo(main_data.main_info, additional_data.additional_info)
                    except (TypeError, ValueError):
                        await asyncio.sleep(0)
                        continue#XXX play with exceptions a bit
        