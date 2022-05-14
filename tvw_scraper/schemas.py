from dataclasses import dataclass
from typing import Literal, List, Tuple, Optional
from inflection import underscore

import dataclass_factory
from dataclass_factory import Factory, Schema, NameStyle


default_name_mapping = {"message":'m','timestamp':'t','timestamp_milliseconds':'t_ms'}

@dataclass
class InitialResponse:
    session_id: str
    timestamp: int
    timestamp_ms: int
    release : str
    studies_metadata_hash: str
    protocol: str
    javastudies: str
    auth_scheme_vsn: int
    via: str

initial_response_schema = Schema(
    name_mapping={
        'timestamp_ms':'timestampMs'
    }
)

@dataclass
class SeriesLoadingMessage:
    message: Literal['series_loading']
    chart_session: Optional[str] = None
    timestamp: int = None
    timestamp_milliseconds: int = None

series_loading_schema = Schema(
    name_mapping={
        **default_name_mapping,
        "chart_session": ("p", 0)
    }
)

@dataclass
class SymbolResolvedMessage:
    message: Literal['symbol_resolved']
    chart_session: str = None
    timestamp: int = None
    timestamp_milliseconds: int = None
    symbol_info : dict = None
    
symbol_resolved_schema = Schema(
    name_mapping={
        **default_name_mapping,
        "chart_session": ("p", 0),
        "symbol_info":("p",2)
    }
)

@dataclass 
class SeriesTimeframeMessage:#TODO identify what other fields mean. but now theyre worthless ['cs_mmnwr6m6ed90', 'sds_1', 's1', 0, 365, '12M', False] 
    message: Literal['series_timeframe']
    chart_session: str = None

series_timeframe_schema = series_loading_schema

@dataclass
class Ohlcv:
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class SymbolDataSeries:
    node: str = None
    ohlcv: List[Ohlcv] = None

ohlcv_schema = Schema(
    name_mapping={
        'timestamp':('v',0),
        'open':('v',1),
        'high':('v',2),
        'low':('v',3),
        'close':('v',4),
        'volume':('v',5)
    }
)

@dataclass 
class TimescaleUpdateMessage:
    message: Literal['timescale_update']
    chart_session: str = None
    symbol_data_series: SymbolDataSeries = None

symbol_data_series_schema = Schema(
    name_mapping = {
        'ohlcv':'s'
    }
)

timescale_update_schema = Schema(
    name_mapping={
        **default_name_mapping,
        "chart_session": ("p", 0),
        "symbol_data_series":("p",1,'sds_1')
    }
)

@dataclass
class SeriesCompletedMessage:#['cs_vqn2b9kbmahp', 'sds_1', 'streaming', 's1']#
    message: Literal['series_completed']

series_completed_schema = Schema(
    name_mapping={
        **default_name_mapping
    }
)

@dataclass
class MainInfo:
    country_code: str
    nsin: str
    isin: str
    sedol: str
    currency_code: str
    currency_id: str
    local_code: str
    sedol: str
    short_name: str
    listed_exchange: str
    timezone: str
    type: str
    pro_perm: str
    pro_name: str
    session_holidays: str
    original_name: str
    subsessions: list
    is_tradable: bool
    logoid: Optional[str] = None



@dataclass
class AdditionalInfo:#TODO more fields
    symbol_proname: str
    country: Optional[str] = None
    country_fund: Optional[str] = None
    exchange_traded: Optional[str]= None
    industry: Optional[str]= None
    business_description: Optional[str]= None
    local_description: Optional[str]= None
    short_description: Optional[str]= None
    group: Optional[str]= None
    mic: Optional[str]= None
    sector: Optional[str]= None
    web_site_url: Optional[str]= None
    location: Optional[str]= None
    fundamental_currency_code: Optional[str]= None
    rt_update_time: Optional[str]= None
    exchange_listed: Optional[str]= None
    exchange_ticker: Optional[str]= None
    exchange_listed_symbol: Optional[str]= None
    currency_id: Optional[str]= None
    ceo: Optional[str] = None


additional_info_schema = Schema(
    name_mapping = {underscore(k):k for k in ['exchange-traded','local-description','symbol-proname','rt-update-time','exchange-ticker','exchange-listed','exchange-listed-symbol','short-description','currency-id']}
)

@dataclass 
class MainData:
    message: Literal['qsd']
    quote_session: str
    symbol_name: str
    main_info: MainInfo

main_data_schema  = Schema(
    name_mapping = {
        'message':'m',
        'quote_session':('p',0),
        'symbol_name':('p',1,'n'),
        'main_info':('p',1,'v')
    }
)

@dataclass
class AdditionalData:
    message: Literal['qsd']
    quote_session: str
    symbol_name: str
    additional_info: AdditionalInfo

additional_data_schema  = Schema(
    name_mapping = {
        'message':'m',
        'quote_session':('p',0),
        'symbol_name':('p',1,'n'),
        'additional_info':('p',1,'v')
    }
)

@dataclass
class CombinedSymbolInfo:
    main_info: MainInfo
    additional_info: AdditionalInfo


factory = dataclass_factory.Factory(schemas={
    InitialResponse:initial_response_schema,
    SeriesLoadingMessage: series_loading_schema, 
    SymbolResolvedMessage: symbol_resolved_schema,
    SeriesTimeframeMessage: series_timeframe_schema,
    TimescaleUpdateMessage: timescale_update_schema,
    SeriesCompletedMessage: series_completed_schema,
    SymbolDataSeries: symbol_data_series_schema,
    Ohlcv: ohlcv_schema,
    MainData:main_data_schema,
    AdditionalData: additional_data_schema,
    AdditionalInfo:additional_info_schema
    })