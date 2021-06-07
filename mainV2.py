"""
Based on the Traility Bot structure

MACD, EMA, RSI and BollBands of original defined value.

Sell condition: at Top BollBand(30Periods), RSI(13Periods) < 70
Buy condition: ema_short > ema_long and rsi < 40 and current_price < bbands_lower
"""

def initialize(state):
    state.number_offset_trades = 0;



@schedule(interval="5m", symbol="BTCUSDT")
def handler(state, data):

    '''
    1) Compute indicators from data
    '''

    """
        BBANDS
    """

    bbands = data.bbands(20, 2)
    
    # on erronous data return early (indicators are of NoneType)
    if bbands is None:
        return

    #BBANDS
    bbands_lower = bbands["bbands_lower"].last
    bbands_upper = bbands["bbands_upper"].last

    """
        RSI
    """

    ema_long = data.ema(40).last
    ema_short = data.ema(20).last
    rsi = data.rsi(14).last
    
    # on erronous data return early (indicators are of NoneType)
    if rsi is None or ema_long is None:
        return
    
    """
        MACD
    """

    macd_ind = data.macd(12,26,9)

    # on erronous data return early (indicators are of NoneType)
    if macd_ind is None:
        return

    signal = macd_ind['macd_signal'].last
    macd = macd_ind['macd'].last



    current_price = data.close_last
    
    '''
    2) Fetch portfolio
        > check liquidity (in quoted currency)
        > resolve buy value
    '''
    
    portfolio = query_portfolio()
    balance_quoted = portfolio.excess_liquidity_quoted
    # we invest only 80% of available liquidity
    buy_value = float(balance_quoted) * 0.40
    
    
    '''
    3) Fetch position for symbol
        > has open position
        > check exposure (in base currency)
    '''

    position = query_open_position_by_symbol(data.symbol,include_dust=False)
    has_position = position is not None

    '''
    4) Resolve buy or sell signals
        > create orders using the order api
        > print position information
        
    '''
    if macd > signal and ema_short > ema_long and rsi < 40 and current_price < bbands_lower and not has_position:
        print("-------")
        print("Buy Signal: creating market order for {}".format(data.symbol))
        print("Buy value: ", buy_value, " at current market price: ", data.close_last)
        
        order_market_value(symbol=data.symbol, value=buy_value)

    elif macd < signal and ema_short < ema_long and rsi > 60 and current_price > bbands_upper and has_position:
        print("-------")
        logmsg = "Sell Signal: closing {} position with exposure {} at current market price {}"
        print(logmsg.format(data.symbol,float(position.exposure),data.close_last))

        close_position(data.symbol)

    '''
    5) Check strategy profitability
        > print information profitability on every offsetting trade
    '''
    
    if state.number_offset_trades < portfolio.number_of_offsetting_trades:
        
        pnl = query_portfolio_pnl()
        print("-------")
        print("Accumulated Pnl of Strategy: {}".format(pnl))
        
        offset_trades = portfolio.number_of_offsetting_trades
        number_winners = portfolio.number_of_winning_trades
        print("Number of winning trades {}/{}.".format(number_winners,offset_trades))
        print("Best trade Return : {:.2%}".format(portfolio.best_trade_return))
        print("Worst trade Return : {:.2%}".format(portfolio.worst_trade_return))
        print("Average Profit per Winning Trade : {:.2f}".format(portfolio.average_profit_per_winning_trade))
        print("Average Loss per Losing Trade : {:.2f}".format(portfolio.average_loss_per_losing_trade))
        # reset number offset trades
        state.number_offset_trades = portfolio.number_of_offsetting_trades


