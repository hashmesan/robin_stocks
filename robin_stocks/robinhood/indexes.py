"""Contains functions for getting market index data such as VIX and NDX."""
from typing import Dict, List, Optional, Union

from robin_stocks.robinhood.helper import *
from robin_stocks.robinhood.urls import *

INDEX_IDS: Dict[str, str] = {
    'VIX': '3b912aa2-88f9-4682-8ae3-e39520bdf4db',
    'NDX': '50c298f7-27a8-44a1-b049-ec153cf2892f',
}
"""Mapping of well-known index symbols to their Robinhood instrument UUIDs."""


def get_index_id_by_name(symbol: str) -> Optional[str]:
    """Takes an index symbol and returns the Robinhood UUID associated with that index.

    :param symbol: The index symbol (e.g., 'VIX', 'NDX'). Case-insensitive.
    :type symbol: str
    :returns: [str] A string representing the index UUID, or None if the symbol is not recognized. \
    Available indexes can be found in the ``INDEX_IDS`` dictionary.

    """
    try:
        symbol = symbol.upper().strip()
    except AttributeError as message:
        print(message, file=get_output())
        return None

    if symbol not in INDEX_IDS:
        print('Error: "{0}" is not a recognized index symbol. '
              'Available indexes are: {1}'.format(symbol, ', '.join(INDEX_IDS.keys())),
              file=get_output())
        return None

    return INDEX_IDS[symbol]


@login_required
def get_index_fundamentals(input_symbols: Union[str, List[str]], info: Optional[str] = None) -> Union[dict, list, None]:
    """Gets fundamental data for one or more market indexes.

    Uses the Robinhood ``/marketdata/indexes/fundamentals/v1/`` endpoint to retrieve
    fundamental information such as 52-week high/low, daily high/low, open, and
    previous close for the specified indexes.

    :param input_symbols: May be a single index symbol (e.g., 'VIX') or a list of \
    index symbols (e.g., ['VIX', 'NDX']). Symbols are case-insensitive. Available \
    symbols can be found in the ``INDEX_IDS`` dictionary.
    :type input_symbols: str or list
    :param info: Will filter the results to get a specific value.
    :type info: Optional[str]
    :returns: [list] If info parameter is left as None then the list will contain a dictionary \
    of key/value pairs for each index. Otherwise, it will be a list of strings where the strings \
    are the values of the key that corresponds to info.
    :Dictionary Keys: * id
                      * symbol
                      * high_52_weeks
                      * low_52_weeks
                      * pe_ratio (may not be present for all indexes)
                      * high
                      * low
                      * open
                      * previous_close
                      * previous_close_date
                      * updated_at

    """
    symbols = inputs_to_set(input_symbols)
    ids: List[str] = []
    for symbol in symbols:
        index_id = get_index_id_by_name(symbol)
        if index_id:
            ids.append(index_id)

    if not ids:
        print('Error: No valid index symbols were provided.', file=get_output())
        return [None]

    url = index_fundamentals_url()
    payload: Dict[str, str] = {'ids': ','.join(ids)}
    data = request_get(url, 'regular', payload)

    # Response is {"status": "SUCCESS", "data": [{"status": "SUCCESS", "data": {...}}, ...]}
    # Unwrap the nested structure to return a flat list of fundamental dicts.
    if data and isinstance(data, dict) and 'data' in data:
        items: List[dict] = []
        for entry in data['data']:
            if isinstance(entry, dict) and entry.get('status') == 'SUCCESS' and 'data' in entry:
                items.append(entry['data'])
        return filter_data(items, info)

    return filter_data(data, info)


@login_required
def get_index_historicals(
    symbol: str,
    display_span: str = 'day',
    show_candlesticks: bool = False,
    info: Optional[str] = None,
) -> Union[list, None]:
    """Gets historical chart data for a market index.

    Uses the Robinhood Bonfire ``/indexes/{id}/historical-chart/`` endpoint to retrieve
    historical price data points for a given index over the specified time span. The raw
    API returns chart rendering data which this function flattens into a list of
    price data points.

    :param symbol: The index symbol (e.g., 'VIX', 'NDX'). Case-insensitive. \
    Available symbols can be found in the ``INDEX_IDS`` dictionary.
    :type symbol: str
    :param display_span: The time span for the historical data. Can be 'day', 'week', \
    'month', '3month', 'year', or '5year'. Default is 'day'.
    :type display_span: Optional[str]
    :param show_candlesticks: Whether to include candlestick (OHLC) data in the response. \
    Default is False.
    :type show_candlesticks: Optional[bool]
    :param info: Will filter the results to have a list of the values that correspond \
    to key that matches info.
    :type info: Optional[str]
    :returns: [list] If info parameter is left as None then the list will contain a dictionary \
    of key/value pairs for each data point. Otherwise, it will be a list of strings where the \
    strings are the values of the key that corresponds to info.
    :Dictionary Keys: * symbol
                      * label (timestamp label, e.g. '9:30 AM' or 'Feb 20')
                      * value (price as a string)
                      * change (price change with percentage, e.g. '1.23 (6.60%)')
                      * x (normalized x-axis position, 0.0 to 1.0)
                      * y (normalized y-axis position)

    """
    span_check: List[str] = ['day', 'week', 'month', '3month', 'year', '5year']

    if display_span not in span_check:
        print('ERROR: display_span must be "day","week","month","3month","year",or "5year"',
              file=get_output())
        return [None]

    index_id = get_index_id_by_name(symbol)
    if not index_id:
        return [None]

    url = index_historical_chart_url(index_id)
    payload: Dict[str, str] = {
        'display_span': display_span,
        'show_candlesticks': str(show_candlesticks).lower(),
    }
    data = request_get(url, 'regular', payload)

    # Response structure: {chart_data: {chart: {lines: [{identifier, segments: [{points}]}]}}}
    # Extract the "price" line's points and flatten cursor_data into simple dicts.
    if data and isinstance(data, dict):
        chart_data = data.get('chart_data', {})
        chart = chart_data.get('chart', {}) if isinstance(chart_data, dict) else {}
        lines = chart.get('lines', []) if isinstance(chart, dict) else []

        price_line = next((l for l in lines if l.get('identifier') == 'price'), None)
        if price_line:
            hist_data: List[dict] = []
            for segment in price_line.get('segments', []):
                for point in segment.get('points', []):
                    cursor = point.get('cursor_data') or {}
                    item: Dict[str, Optional[str]] = {
                        'symbol': symbol.upper().strip(),
                        'label': cursor.get('label', {}).get('value') if cursor.get('label') else None,
                        'value': cursor.get('primary_value', {}).get('value') if cursor.get('primary_value') else None,
                        'change': cursor.get('secondary_value', {}).get('main', {}).get('value') if cursor.get('secondary_value') else None,
                        'x': point.get('x'),
                        'y': point.get('y'),
                    }
                    hist_data.append(item)
            return filter_data(hist_data, info)

    return filter_data(data, info)
