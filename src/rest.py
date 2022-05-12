import uplink

# Constants
SCANNER_API = 'https://scanner.tradingview.com/'
SYMBOL_SEARCH_API = 'https://symbol-search.tradingview.com'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 Safari/537.36'}
@uplink.headers(headers)
class Scanner(uplink.Consumer):
    @uplink.returns.json
    @uplink.get("/{sector}/scan")
    def get_sector_symbols(self,sector):
        """Gets tradingview symbols from specified sector"""
        
@uplink.headers(headers)
class SymbolSearch(uplink.Consumer):
    @uplink.returns.json
    @uplink.params({"hl": True, 'lang': "ru", 'domain':'production'})#static params
    @uplink.get('/symbol_search/')
    def search_symbol(self, symbol: uplink.Query("text")):
        """Search symbol in tradingview api"""

SymbolScanner =  Scanner(SCANNER_API)
SymbolSearcher = SymbolSearch(SYMBOL_SEARCH_API)