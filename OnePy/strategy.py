import datetime
import pandas as pd
from math import isnan

from abc import ABCMeta, abstractmethod

from event import SignalEvent,events

class Strategy(object):

    __metaclass__ = ABCMeta

    def __init__(self,bars):
        self.bars = bars  # object of feed

        self.symbol_list = self.bars.symbol_list
        self.latest_bar_dict = self.bars.latest_bar_dict


        self.bought = self._calculate_initial_bought()

        self.bar = None

    @abstractmethod
    def luffy(self):
        raise NotImplemented('Should implement luffy()')

    def _calculate_initial_bought(self):
        bought = {}
        for s in self.symbol_list:
            bought[s] = False
        return bought

    def get_df(self,symbol):
        return pd.DataFrame(self.latest_bar_dict[symbol])

###################### Order function ############################

    def long(self,symbol,strength=1,risky=False,percent=False):
        bar = self.bars.get_latest_bars(symbol, N=1)
        def put():
            if bar is not None and bar !=[]:
                signal = SignalEvent(symbol, bar[0]['date'],bar[0]['close'],
                                    'LONG', strength, percent)
                events.put(signal)
        if risky:
            put()
        else:
            if self.bought[symbol] == False:
                if bar is not None and bar !=[]:
                    put()
                    self.bought[symbol] = True

    def short(self,symbol,strength=1,risky=False,percent=False):
        bar = self.bars.get_latest_bars(symbol, N=1)
        def put():
            if bar is not None and bar !=[]:
                signal = SignalEvent(symbol, bar[0]['date'],bar[0]['close'],
                                     'SHORT',strength, percent)
                events.put(signal)
        if not risky:
            if self.bought[symbol] == False:
                if bar is not None and bar !=[]:
                    put()
                    self.bought[symbol] = True
        else:
            put()

    def exitlong(self,symbol,strength=1):
        bar = self.bars.get_latest_bars(symbol, N=1)
        def put():
            if bar is not None and bar !=[]:
                signal = SignalEvent(symbol, bar[0]['date'],bar[0]['close'], 'EXITLONG',strength)
                events.put(signal)
        put()

    def exitshort(self,symbol,strength=1,risky=False):
        bar = self.bars.get_latest_bars(symbol, N=1)
        def put():
            if bar is not None and bar !=[]:
                signal = SignalEvent(symbol, bar[0]['date'],bar[0]['close'], 'EXITSHORT',strength)
                events.put(signal)
        put()



    def exitall(self,symbol):
        bar = self.bars.get_latest_bars(symbol, N=1)
        def put():
            if bar is not None and bar !=[]:
                signal = SignalEvent(symbol, bar[0]['date'],bar[0]['close'], 'EXITALL',strength=1)
                events.put(signal)
        put()

#########################  Indicator  ###########################

def indicator(ind_func, name, df, timeperiod, select, index=False):
    """
    ind_func: function from tablib
    ind_name: name of indicator
    df: DataFrame
    timeperiod: int
    select: list or int.
        - Attention:
            index start from -1, select=[0] or [0,n] is invalid.
    index: default False, if True, select df by index
        - for example:
            select=[1,2] means df.iloc[1:2,:]
    """
    def offset(select):
        if min(select)<0:
            return abs(min(select))
        else:
            return 0
    off = offset(select)

    ori_df = df
    df = df.iloc[-timeperiod-off:,:]
    total_df = pd.DataFrame()
    ind_df = ind_func(df,timeperiod)
    ind_df = pd.DataFrame(ind_df)


    if ori_df.shape[0] < timeperiod:
        return float('nan')

    def check():
        check = df_selected.empty or isnan(df_selected.iat[0,0])
        if check:
            raise SyntaxError ('select NaN values!')

    if index:
        if type(select) is list:
            if len(select) == 1:
                df_selected = ind_df.iloc[select[0]:,:]
            else:
                i = select[0]
                j = select[1]
                df_selected = ind_df.iloc[i:j,:]

            check()
            total_df = total_df.append(df_selected)
        else:
            print 'Params select wrong! Maybe out of range or something'
    else:
        if type(select) is list:
            for i in select:
                if i >= 0:
                    df_selected = ind_df.iloc[i:i+1,:]
                if i == -1:
                    df_selected = ind_df.iloc[-1:,:]
                if i < -1:
                    df_selected = ind_df.iloc[i-1:i,:]

                check()
                total_df = total_df.append(df_selected)
        else:
            print 'Params select wrong! Maybe out of range or something'

    total_df.rename(columns={total_df.columns[0]:name},inplace=True)

    if index:
        return total_df
    else:
        return total_df.iat[0,0]

##################### Customize Strategy #########################

from talib.abstract import *
class SMAStrategy(Strategy):
    """
    Attention! Do not put exitall and (exit_long or exit_short) together
    """
    def __init__(self,bars):
        self.prepare(bars)

    def luffy(self):
        for s in self.symbol_list:

            df = self.bar_df_dict[s]

            sma1=indicator(SMA, 'sma5', df, 5, select=[-1])
            sma2=indicator(SMA, 'sma10', df, 15, select=[-1])
            if sma1 > sma2:
                self.short(s,strength=3,percent=True,risky=True)
            if sma1 < sma2:
                self.exitall(s)#,risky=True)

class BuyAndHoldStrategy(Strategy):
    def __init__(self,bars):
        super(BuyAndHoldStrategy,self).__init__(bars)

    def luffy(self):
        # if event.type == 'Market':
        self.long('000001')
