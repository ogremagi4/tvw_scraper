from tvw_scraper.rest import SymbolScanner, SymbolSearcher
from tvw_scraper.scraper import TradingviewWsScraper
from tvw_scraper.models import Intervals, Sectors
import asyncio

scraper = TradingviewWsScraper()

async def main():
    result = await asyncio.gather(*[
        scraper.get_symbol('NASDAQ:NVDA')
        ])
    c=0


asyncio.get_event_loop().run_until_complete(main())