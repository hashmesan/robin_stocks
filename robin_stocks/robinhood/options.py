"""Contains functions for getting information about options."""
import sys
from robin_stocks.robinhood.helper import *
from robin_stocks.robinhood.urls import *

def spinning_cursor():
    """ This is a generator function to yield a character. """
    while True:
        for cursor in '|/-\\':
            yield cursor

spinner = spinning_cursor()

def write_spinner():
    """ Function to create a spinning cursor to tell user that the code is working on getting market data. """
    if get_output()==sys.stdout:
        marketString = 'Loading Market Data '
        sys.stdout.write(marketString)
        sys.stdout.write(next(spinner))
        sys.stdout.flush()
        sys.stdout.write('\b'*(len(marketString)+1))

@login_required
def get_aggregate_positions(info=None, account_number=None):
    """Collapses all option orders for a stock into a single dictionary.

    :param info: Will filter the results to get a specific value.
    :type info: Optional[str]
    :returns: Returns a list of dictionaries of key/value pairs for each order. If info parameter is provided, \
    a list of strings is returned where the strings are the value of the key that matches info.

    """
    url = aggregate_url(account_number=account_number)
    data = request_get(url, 'pagination')
    return(filter_data(data, info))

@login_required
def get_aggregate_open_positions(info=None, account_number=None):
    """Collapses all open option positions for a stock into a single dictionary.

    :param info: Will filter the results to get a specific value.
    :type info: Optional[str]
    :returns: Returns a list of dictionaries of key/value pairs for each order. If info parameter is provided, \
    a list of strings is returned where the strings are the value of the key that matches info.

    """
    url = aggregate_url(account_number=account_number)
    payload = {'nonzero': 'True'}
    data = request_get(url, 'pagination', payload)
    return(filter_data(data, info))


@login_required
def get_market_options(info=None):
    """Returns a list of all options.

    :param info: Will filter the results to get a specific value.
    :type info: Optional[str]
    :returns: Returns a list of dictionaries of key/value pairs for each option. If info parameter is provided, \
    a list of strings is returned where the strings are the value of the key that matches info.

    """
    url = option_orders_url()
    data = request_get(url, 'pagination')

    return(filter_data(data, info))


@login_required
def get_all_option_positions(info=None, account_number=None):
    """Returns all option positions ever held for the account.

    :param info: Will filter the results to get a specific value.
    :type info: Optional[str]
    :returns: Returns a list of dictionaries of key/value pairs for each option. If info parameter is provided, \
    a list of strings is returned where the strings are the value of the key that matches info.

    """
    url = option_positions_url(account_number=account_number)
    data = request_get(url, 'pagination')
    return(filter_data(data, info))


@login_required
def get_open_option_positions(account_number=None, info=None):
    """Returns all open option positions for the account.
    
    :param acccount_number: the robinhood account number.
    :type acccount_number: Optional[str]
    :param info: Will filter the results to get a specific value.
    :type info: Optional[str]
    :returns: Returns a list of dictionaries of key/value pairs for each option. If info parameter is provided, \
    a list of strings is returned where the strings are the value of the key that matches info.

    """
    url = option_positions_url(account_number=account_number)
    payload = {'nonzero': 'True'}
    data = request_get(url, 'pagination', payload)

    return(filter_data(data, info))


def get_chains(symbol, info=None):
    """Returns the chain information of an option.

    :param symbol: The ticker of the stock.
    :type symbol: str
    :param info: Will filter the results to get a specific value.
    :type info: Optional[str]
    :returns: Returns a dictionary of key/value pairs for the option. If info parameter is provided, \
    a list of strings is returned where the strings are the value of the key that matches info.

    """
    try:
        symbol = symbol.upper().strip()
    except AttributeError as message:
        print(message, file=get_output())
        return None

    url = chains_url(symbol)
    data = request_get(url)

    return(filter_data(data, info))

@login_required
def find_tradable_options(symbol, expirationDate=None, strikePrice=None, optionType=None, info=None):
    """Returns a list of all available options for a stock.

    :param symbol: The ticker of the stock.
    :type symbol: str
    :param expirationDate: Represents the expiration date in the format YYYY-MM-DD.
    :type expirationDate: str
    :param strikePrice: Represents the strike price of the option.
    :type strikePrice: str
    :param optionType: Can be either 'call' or 'put' or left blank to get both.
    :type optionType: Optional[str]
    :param info: Will filter the results to get a specific value.
    :type info: Optional[str]
    :returns: Returns a list of dictionaries of key/value pairs for all calls of the stock. If info parameter is provided, \
    a list of strings is returned where the strings are the value of the key that matches info.

    """
    try:
        symbol = symbol.upper().strip()
    except AttributeError as message:
        print(message, file=get_output())
        return [None]

    url = option_instruments_url()
    if not id_for_chain(symbol):
        print("Symbol {} is not valid for finding options.".format(symbol), file=get_output())
        return [None]

    payload = {'chain_id': id_for_chain(symbol),
               'chain_symbol': symbol,
               'state': 'active'}

    if expirationDate:
        payload['expiration_dates'] = expirationDate
    if strikePrice:
        payload['strike_price'] = strikePrice
    if optionType:
        payload['type'] = optionType

    data = request_get(url, 'pagination', payload)
    return(filter_data(data, info))

@login_required
def find_options_by_expiration(inputSymbols, expirationDate, optionType=None, info=None):
    """Returns a list of all the option orders that match the seach parameters

    :param inputSymbols: The ticker of either a single stock or a list of stocks.
    :type inputSymbols: str
    :param expirationDate: Represents the expiration date in the format YYYY-MM-DD.
    :type expirationDate: str
    :param optionType: Can be either 'call' or 'put' or leave blank to get both.
    :type optionType: Optional[str]
    :param info: Will filter the results to get a specific value.
    :type info: Optional[str]
    :returns: Returns a list of dictionaries of key/value pairs for all options of the stock that match the search parameters. \
    If info parameter is provided, a list of strings is returned where the strings are the value of the key that matches info.

    """
    try:
        symbols = inputs_to_set(inputSymbols)
        if optionType:
            optionType = optionType.lower().strip()
    except AttributeError as message:
        print(message, file=get_output())
        return [None]

    data = []
    print(symbols)
    for symbol in symbols:
        allOptions = find_tradable_options(symbol, expirationDate, None, optionType, None)
        filteredOptions = [item for item in allOptions if item.get("expiration_date") == expirationDate]
        ids = [item['id'] for item in allOptions if item.get("expiration_date") == expirationDate]
        marketData = get_option_market_data_by_multiple_id(ids)
        merged = merge_option_and_market_data(filteredOptions, marketData)
        data.extend(merged)

    return(filter_data(data, info))

@login_required
def find_options_by_strike(inputSymbols, strikePrice, optionType=None, info=None):
    """Returns a list of all the option orders that match the seach parameters

    :param inputSymbols: The ticker of either a single stock or a list of stocks.
    :type inputSymbols: str
    :param strikePrice: Represents the strike price to filter for.
    :type strikePrice: str
    :param optionType: Can be either 'call' or 'put' or leave blank to get both.
    :type optionType: Optional[str]
    :param info: Will filter the results to get a specific value.
    :type info: Optional[str]
    :returns: Returns a list of dictionaries of key/value pairs for all options of the stock that match the search parameters. \
    If info parameter is provided, a list of strings is returned where the strings are the value of the key that matches info.

    """
    try:
        symbols = inputs_to_set(inputSymbols)
        if optionType:
            optionType = optionType.lower().strip()
    except AttributeError as message:
        print(message, file=get_output())
        return [None]

    data = []
    for symbol in symbols:
        filteredOptions = find_tradable_options(symbol, None, strikePrice, optionType, None)

        for item in filteredOptions:
            marketData = get_option_market_data_by_id(item['id'])
            if marketData:
                item.update(marketData[0])
            write_spinner()

        data.extend(filteredOptions)

    return(filter_data(data, info))

@login_required
def find_options_by_expiration_and_strike(inputSymbols, expirationDate, strikePrice, optionType=None, info=None):
    """Returns a list of all the option orders that match the seach parameters

    :param inputSymbols: The ticker of either a single stock or a list of stocks.
    :type inputSymbols: str
    :param expirationDate: Represents the expiration date in the format YYYY-MM-DD.
    :type expirationDate: str
    :param strikePrice: Represents the strike price to filter for.
    :type strikePrice: str
    :param optionType: Can be either 'call' or 'put' or leave blank to get both.
    :type optionType: Optional[str]
    :param info: Will filter the results to get a specific value.
    :type info: Optional[str]
    :returns: Returns a list of dictionaries of key/value pairs for all options of the stock that match the search parameters. \
    If info parameter is provided, a list of strings is returned where the strings are the value of the key that matches info.

    """
    try:
        symbols = inputs_to_set(inputSymbols)
        if optionType:
            optionType = optionType.lower().strip()
    except AttributeError as message:
        print(message, file=get_output())
        return [None]

    data = []
    for symbol in symbols:
        allOptions = find_tradable_options(symbol, expirationDate, strikePrice, optionType, None)
        filteredOptions = [item for item in allOptions if item.get("expiration_date") == expirationDate]

        ids = [item['id'] for item in filteredOptions]
        marketData = get_option_market_data_by_multiple_id(ids)
        merged = merge_option_and_market_data(filteredOptions, marketData)
        data.extend(merged)

    return filter_data(data, info)

#filtereddata {'chain_id': '7a0285ed-21b2-483e-8b5e-759e1ad86e3c', 'chain_symbol': 'KTOS', 'created_at': '2026-02-06T02:09:22.751611Z', 'expiration_date': '2026-03-20', 'id': '80260940-6eca-453f-9045-b55c7d40c4f7', 'issue_date': '2026-02-06', 'min_ticks': {'above_tick': '0.10', 'below_tick': '0.05', 'cutoff_price': '3.00'}, 'rhs_tradability': 'tradable', 'state': 'active', 'strike_price': '50.0000', 'tradability': 'tradable', 'type': 'put', 'updated_at': '2026-02-06T02:09:22.751613Z', 'url': 'https://api.robinhood.com/options/instruments/80260940-6eca-453f-9045-b55c7d40c4f7/', 'sellout_datetime': '2026-03-20T19:30:00+00:00', 'long_strategy_code': '80260940-6eca-453f-9045-b55c7d40c4f7_L1', 'short_strategy_code': '8026<PASSWORD>-<PASSWORD>-<PASSWORD>-<PASSWORD>-<PASSWORD>', '<PASSWORD>underlying_type': '<PASSWORD>'}
#data {'adjusted_mark_price': '0.010000', 'adjusted_mark_price_round_down': '0.010000', 'ask_price': '0.750000', 'ask_size': 403, 'bid_price': '0.000000', 'bid_size': 0, 'break_even_price': '49.990000', 'high_price': None, 'instrument': 'https://api.robinhood.com/options/instruments/80260940-6eca-453f-9045-b55c7d40c4f7/', 'instrument_id': '80260940-6eca-453f-9045-b55c7d40c4f7', 'last_trade_price': '0.080000', 'last_trade_size': 2, 'low_price': None, 'mark_price': '0.375000', 'open_interest': 8, 'previous_close_date': '2026-02-25', 'previous_close_price': '0.010000', 'updated_at': '2026-02-26T20:59:45.088165891Z', 'volume': 0, 'symbol': 'KTOS', 'occ_symbol': 'KTOS  260320P00050000', 'state': 'active', 'chance_of_profit_long': '0.003224', 'chance_of_profit_short': '0.996776', 'delta': '-0.001642', 'gamma': '0.000269', 'implied_volatility': '0.889823', 'rho': '-0.000096', 'theta': '-0.002427', 'vega': '0.001189', 'pricing_model': 'Bjerksund-Stensland 1993', 'high_fill_rate_buy_price': None, 'high_fill_rate_sell_price': None, 'low_fill_rate_buy_price': None, 'low_fill_rate_sell_price': None}
def merge_option_and_market_data(filteredOptions, marketData):
    """Merges option instrument dicts with market data dicts by matching id == instrument_id.
    Skips None entries and options with no matching market data."""
    market_by_id = {d['instrument_id']: d for d in marketData if d is not None and 'instrument_id' in d}
    return [{**opt, **market_by_id[opt['id']]} for opt in filteredOptions if opt is not None and opt.get('id') in market_by_id]

@login_required
def find_options_by_specific_profitability(inputSymbols, expirationDate=None, strikePrice=None, optionType=None, typeProfit="chance_of_profit_short", profitFloor=0.0, profitCeiling=1.0, info=None):
    """Returns a list of option market data for several stock tickers that match a range of profitability.

    :param inputSymbols: May be a single stock ticker or a list of stock tickers.
    :type inputSymbols: str or list
    :param expirationDate: Represents the expiration date in the format YYYY-MM-DD. Leave as None to get all available dates.
    :type expirationDate: str
    :param strikePrice: Represents the price of the option. Leave as None to get all available strike prices.
    :type strikePrice: str
    :param optionType: Can be either 'call' or 'put' or leave blank to get both.
    :type optionType: Optional[str]
    :param typeProfit: Will either be "chance_of_profit_short" or "chance_of_profit_long".
    :type typeProfit: str
    :param profitFloor: The lower percentage on scale 0 to 1.
    :type profitFloor: int
    :param profitCeiling: The higher percentage on scale 0 to 1.
    :type profitCeiling: int
    :param info: Will filter the results to get a specific value.
    :type info: Optional[str]
    :returns: Returns a list of dictionaries of key/value pairs for all stock option market data. \
    If info parameter is provided, a list of strings is returned where the strings are the value of the key that matches info.

    """
    symbols = inputs_to_set(inputSymbols)
    data = []

    if (typeProfit != "chance_of_profit_short" and typeProfit != "chance_of_profit_long"):
        print("Invalid string for 'typeProfit'. Defaulting to 'chance_of_profit_short'.", file=get_output())
        typeProfit = "chance_of_profit_short"
    
    for symbol in symbols:
        allOptions = find_tradable_options(symbol, expirationDate, None, optionType, None)
        filteredOptions = [item for item in allOptions if item.get("expiration_date") == expirationDate]
        ids = [item['id'] for item in allOptions if item.get("expiration_date") == expirationDate]
        marketData = get_option_market_data_by_multiple_id(ids)

        merged = merge_option_and_market_data(filteredOptions, marketData)
        merged_profit = [item for item in merged if float(item.get(typeProfit, 0)) >= profitFloor and float(item.get(typeProfit, 0)) <= profitCeiling]
        data.extend(merged_profit)

        # tempData = find_tradable_options(symbol, expirationDate, strikePrice, optionType, info=None)
        # for option in tempData:
        #     if expirationDate and option.get("expiration_date") != expirationDate:
        #         continue

        #     market_data = get_option_market_data_by_id(option['id'])
            
        #     if len(market_data):
        #         option.update(market_data[0])
        #         write_spinner()

        #         try:
        #             floatValue = float(option[typeProfit])
        #             if (floatValue >= profitFloor and floatValue <= profitCeiling):
        #                 data.append(option)
        #         except:
        #             pass

    return(filter_data(data, info))

@login_required
def get_option_market_data_by_multiple_id(ids, info=None):
    ids_query = ','.join(ids)
    url = marketdata_options_url()
    return request_get(url, 'results', {'ids': ids_query})

@login_required
def get_option_instrument_data_by_multiple_id(ids, info=None):
    ids_query = ','.join(ids)
    url = option_instruments_url()
    return request_get(url, 'results', {'ids': ids_query})

@login_required
def get_option_market_data_by_id(id, info=None):
    """Returns the option market data for a stock, including the greeks,
    open interest, change of profit, and adjusted mark price.

    :param id: The id of the stock.
    :type id: str
    :param info: Will filter the results to get a specific value.
    :type info: Optional[str]
    :returns: Returns a dictionary of key/value pairs for the stock. \
    If info parameter is provided, the value of the key that matches info is extracted.

    """
    url = marketdata_options_url()
    payload = {
        "instruments" : option_instruments_url(id)
    }
    print(url, payload)

    data = request_get(url, 'results', payload)

    return(filter_data(data, info))

@login_required
def get_option_market_data(inputSymbols, expirationDate, strikePrice, optionType, info=None):
    """Returns the option market data for the stock option, including the greeks,
    open interest, change of profit, and adjusted mark price.

    :param inputSymbols: The ticker of the stock.
    :type inputSymbols: str
    :param expirationDate: Represents the expiration date in the format YYYY-MM-DD.
    :type expirationDate: str
    :param strikePrice: Represents the price of the option.
    :type strikePrice: str
    :param optionType: Can be either 'call' or 'put'.
    :type optionType: str
    :param info: Will filter the results to get a specific value.
    :type info: Optional[str]
    :returns: Returns a dictionary of key/value pairs for the stock. \
    If info parameter is provided, the value of the key that matches info is extracted.

    """
    try:
        symbols = inputs_to_set(inputSymbols)
        if optionType:
            optionType = optionType.lower().strip()
    except AttributeError as message:
        print(message, file=get_output())
        return [None]

    data = []
    for symbol in symbols:
        optionID = id_for_option(symbol, expirationDate, strikePrice, optionType)
        marketData = get_option_market_data_by_id(optionID)
        data.append(marketData)

    return(filter_data(data, info))


def get_option_instrument_data_by_id(id, info=None):
    """Returns the option instrument information.

    :param id: The id of the stock.
    :type id: str
    :param info: Will filter the results to get a specific value.
    :type info: Optional[str]
    :returns: Returns a dictionary of key/value pairs for the stock. \
    If info parameter is provided, the value of the key that matches info is extracted.

    """
    url = option_instruments_url(id)
    data = request_get(url)
    return(filter_data(data, info))


def get_option_instrument_data(symbol, expirationDate, strikePrice, optionType, info=None):
    """Returns the option instrument data for the stock option.

    :param symbol: The ticker of the stock.
    :type symbol: str
    :param expirationDate: Represents the expiration date in the format YYYY-MM-DD.
    :type expirationDate: str
    :param strikePrice: Represents the price of the option.
    :type strikePrice: str
    :param optionType: Can be either 'call' or 'put'.
    :type optionType: str
    :param info: Will filter the results to get a specific value.
    :type info: Optional[str]
    :returns: Returns a dictionary of key/value pairs for the stock. \
    If info parameter is provided, the value of the key that matches info is extracted.

    """
    try:
        symbol = symbol.upper().strip()
        optionType = optionType.lower().strip()
    except AttributeError as message:
        print(message, file=get_output())
        return [None]

    optionID = id_for_option(symbol, expirationDate, strikePrice, optionType)
    url = option_instruments_url(optionID)
    data = request_get(url)

    return(filter_data(data, info))


def get_option_historicals(symbol, expirationDate, strikePrice, optionType, interval='hour', span='week', bounds='regular', info=None):
    """Returns the data that is used to make the graphs.

    :param symbol: The ticker of the stock.
    :type symbol: str
    :param expirationDate: Represents the expiration date in the format YYYY-MM-DD.
    :type expirationDate: str
    :param strikePrice: Represents the price of the option.
    :type strikePrice: str
    :param optionType: Can be either 'call' or 'put'.
    :type optionType: str
    :param interval: Interval to retrieve data for. Values are '5minute', '10minute', 'hour', 'day', 'week'. Default is 'hour'.
    :type interval: Optional[str]
    :param span: Sets the range of the data to be either 'day', 'week', 'year', or '5year'. Default is 'week'.
    :type span: Optional[str]
    :param bounds: Represents if graph will include extended trading hours or just regular trading hours. Values are 'regular', 'trading', and 'extended'. \
    regular hours are 6 hours long, trading hours are 9 hours long, and extended hours are 16 hours long. Default is 'regular'
    :type bounds: Optional[str]
    :param info: Will filter the results to have a list of the values that correspond to key that matches info.
    :type info: Optional[str]
    :returns: Returns a list that contains a list for each symbol. \
    Each list contains a dictionary where each dictionary is for a different time.

    """
    try:
        symbol = symbol.upper().strip()
        optionType = optionType.lower().strip()
    except AttributeError as message:
        print(message, file=get_output())
        return [None]

    interval_check = ['5minute', '10minute', 'hour', 'day', 'week']
    span_check = ['day', 'week', 'year', '5year']
    bounds_check = ['extended', 'regular', 'trading']
    if interval not in interval_check:
        print(
            'ERROR: Interval must be "5minute","10minute","hour","day",or "week"', file=get_output())
        return([None])
    if span not in span_check:
        print('ERROR: Span must be "day", "week", "year", or "5year"', file=get_output())
        return([None])
    if bounds not in bounds_check:
        print('ERROR: Bounds must be "extended","regular",or "trading"', file=get_output())
        return([None])

    optionID = id_for_option(symbol, expirationDate, strikePrice, optionType)

    url = option_historicals_url(optionID)
    payload = {'span': span,
               'interval': interval,
               'bounds': bounds}
    data = request_get(url, 'regular', payload)
    if (data == None or data == [None]):
        return data

    histData = []
    for subitem in data['data_points']:
        subitem['symbol'] = symbol
        histData.append(subitem)

    return(filter_data(histData, info))
