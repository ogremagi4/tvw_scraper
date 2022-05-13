# tvw_scraper
use asyncio and websockets to retrieve candles and symbol info from tradingview.com

Usage example:

retrieve symbols to use them later in websocket queries
```python
from tvw_scraper.rest import SymbolScanner
from tvw_scraper.models import Sectors

SymbolScanner.get_sector_symbols(Sectors.russia)
{'totalCount': 937, 'data': [{'s': 'MOEX:AFKS', 'd': []}, {'s': 'MOEX:JNJ-RM', 'd': []} . . .
```

retrieve candles and some info from tradingview websocket:
```python
import asyncio
from tvw_scraper.scraper import TradingviewWsScraper
from tvw_scraper.models import Intervals

scraper = TradingviewWsScraper()

async def main():
    result = await asyncio.gather(*[
        scraper.get_candles('NASDAQ:NVDA',Intervals.interval_1day), 
        scraper.get_candles('NASDAQ:NVDA',Intervals.interval_1hour), 
        scraper.get_symbol('NASDAQ:NVDA')
        ])


asyncio.get_event_loop().run_until_complete(main())
```