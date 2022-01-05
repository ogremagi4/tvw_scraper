from threading import Thread, Lock, Event
from queue import Queue, Empty
from websocket import create_connection
from collections import ChainMap
from loguru import logger
import json
import regex
import string
import random
import traceback
from requests import Session
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from requests.exceptions import HTTPError


json_rgx = regex.compile(r'''
(?(DEFINE)
# Note that everything is atomic, JSON does not need backtracking if it's valid
# and this prevents catastrophic backtracking
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
    
    


class WS:

    headers =  json.dumps({
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
        })

    class Receiver(Thread):
        def __init__(self, ws):
            super().__init__(daemon = True)
            self.queue = Queue()
            self.ws = ws
            self.start()

        def get(self):
            try:
                msg = self.queue.get_nowait()
                if msg:
                    #logger.debug(f'Msg from ws: {msg}')
                    return msg
            except Empty:
                return None
                
        def run(self):
            while True:
                if self.ws.connected:
                    self.queue.put( self.ws.recv() )
                else:
                    break

    class Sender(Thread):
        
        def __init__(self, ws):
            super().__init__(daemon = True)
            self.queue = Queue()
            self.ws = ws
            self.kill = Event()
            self.start()

        def send(self, item):
            return self.queue.put(item)


        def run(self):
            while not self.kill.is_set():
                if not self.queue.empty():
                    self.ws.send( self.queue.get_nowait())


    def __init__(self):
        self.ws = create_connection('wss://data.tradingview.com/socket.io/websocket',headers=self.headers)
        self.sender = self.Sender(self.ws)
        self.receiver = self.Receiver(self.ws)

    def get(self):
        return self.receiver.get()

    def send(self, item):
        self.sender.send(item)


class TradingviewWsScraper:

    def __init__(self, token = 'unauthorized_user_token') -> None:
        self.token = token
        self.messages = TradingViewWsMessages()
    
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
        

    def _init_websocket_and_authorize(self):
        """
        init ws and authorize
        """
        ws = WS()
        ws.send(self.messages.set_auth_token(self.token))
        return ws
    
    def get_symbol(self, tradingview_symbol):
        logger.debug(f'Trying to get {tradingview_symbol}')
        result = []
        quote_session_string = self.quote_session()
        ws = self._init_websocket_and_authorize()
        
        messages = [self.messages.set_auth_token(self.token), 
                    self.messages.set_data_quality('low'),
                    self.messages.quote_create_session(quote_session_string),
                    self.messages.quote_add_symbols(quote_session_string, tradingview_symbol),
                    self.messages.quote_fast_symbols(quote_session_string, tradingview_symbol)]
        for message in messages:
            ws.send(message)
        
        while True:
            resp = ws.get()
            if resp:
                if resp == '~m~4~m~~h~1': #TODO less hardcode
                    break
                logger.debug(resp)
                result.extend([json.loads(i) for i in json_rgx.findall(resp.replace('\\"',''))])
            if (result or [{}])[-1].get('m') == 'quote_completed':
                try:
                    ws.sender.kill.set()
                    ws.ws.send_close()
                except:
                    logger.error(traceback.format_exc())
                
                return [i.get('p')[1].get('v') for i in result if (isinstance(i,dict) and isinstance(i.get('p',[[],[]])[1],dict))]
            
        

    def get_candles(self, tradingview_symbol, tradingview_timeframe):
        result = []
        quote_session_string = self.quote_session()
        chart_session_string = self.chart_session()
        ws = self._init_websocket_and_authorize()
        messages = [self.messages.set_auth_token(self.token), 
                    self.messages.set_data_quality('low'),
                    # self.messages.quote_create_session(quote_session_string), 
                    #self.messages.quote_add_symbols(quote_session_string, tradingview_symbol),
                    #self.messages.quote_fast_symbols(quote_session_string, tradingview_symbol),
                    self.messages.chart_create_session(chart_session_string), 
                    self.messages.resolve_symbol(chart_session_string, tradingview_symbol),
                    self.messages.create_series(chart_session_string, tradingview_timeframe)]

        for message in messages:#TODO wrap it somehow to a separate method sending and receiving messages
            ws.send(message)
            logger.debug(message)
        while True:
            resp = ws.get()
            if resp:
                logger.debug(resp)
                result.extend([json.loads(i) for i in json_rgx.findall(resp)])
            for response_message in result:
                if response_message.get('m')=='timescale_update':
                    candles = [i.get('v') for i in dict(ChainMap(*[i for i in response_message.get('p') if isinstance(i, dict)]))['sds_1']['s']]#TODO validate response somehow
                    ws.ws.send_close()
                    return candles


class TradingViewRestScraper:
    def __init__(self) -> None:
        self.headers = {
         #'Origin': 'https://ru.tradingview.com',
         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 Safari/537.36' #TODO dynamic user-agent
        }

        self.session = Session()

    @retry(stop = stop_after_attempt(10), wait = wait_fixed(60), retry=retry_if_exception_type(HTTPError))
    def get(self, endpoint, params={}, jdata={}, headers={}):
        r = self.session.get(endpoint, params=params, json=jdata, headers={**self.session.headers, **headers})
        r.raise_for_status()
        return r.json()
    
    def search_symbol(self, symbol, **kwargs):
        params = {
            'text':symbol,
            'hl':True,
            'lang':'ru',
            'domain':'production',
            **kwargs
        }
        response = self.get('https://symbol-search.tradingview.com/symbol_search/', params=params) #TODO wrap urls
        return response
    
    def get_sector_symbols(self, sector):
        response = self.get(f'https://scanner.tradingview.com/{sector}/scan') #TODO wrap urls
        return [i.get('s') for i in response.get('data')]
