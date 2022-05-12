from src.scraper import TradingviewWsScraper
from src.models import Intervals, Sectors
from src.rest import scanner, searcher
import asyncio

scraper = TradingviewWsScraper()

russian_stocks = scanner.get_sector_symbols(Sectors.russia)
c=0


async def main():
    result = await asyncio.gather(*[
        scraper.get_candles('NASDAQ:NVDA',Intervals.interval_1day), 
        scraper.get_candles('NASDAQ:NVDA',Intervals.interval_1hour), 
        scraper.get_candles('NASDAQ:NVDA',Intervals.interval_1hour), 
        scraper.get_candles('NASDAQ:NVDA',Intervals.interval_1hour), 
        scraper.get_candles('NASDAQ:NVDA',Intervals.interval_1hour), 
        scraper.get_candles('NASDAQ:NVDA',Intervals.interval_1hour), 
        scraper.get_symbol('NASDAQ:NVDA')
        ])
    c=0

asyncio.get_event_loop().run_until_complete(main())