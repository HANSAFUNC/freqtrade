from freqtrade.strategy import IStrategy
from pandas import DataFrame
import numpy as np
import talib.abstract as ta

class FreqAIStrategy(IStrategy):
    """
    FreqAI 策略示例
    """
    INTERFACE_VERSION = 3
    
    # 最小ROI表
    minimal_roi = {
        "0": 0.1,  # 10% 利润
        "30": 0.05,  # 5% 利润
        "60": 0.02,  # 2% 利润
        "120": 0  # 0% 利润
    }

    # 止损设置
    stoploss = -0.1  # 10% 止损

    # 时间周期
    timeframe = '1h'

    # 定义最大启动蜡烛数
    startup_candle_count: int = 20

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        填充指标
        """
        # FreqAI 启动
        dataframe = self.freqai.start(dataframe, metadata, self)
        return dataframe

    def feature_engineering_expand_all(self, dataframe: DataFrame, period, **kwargs) -> DataFrame:
        """
        FreqAI 特征工程扩展
        """
        dataframe["%-rsi-period"] = ta.RSI(dataframe, timeperiod=period)
        dataframe["%-mfi-period"] = ta.MFI(dataframe, timeperiod=period)
        dataframe["%-adx-period"] = ta.ADX(dataframe, timeperiod=period)
        dataframe["%-sma-period"] = ta.SMA(dataframe, timeperiod=period)
        dataframe["%-ema-period"] = ta.EMA(dataframe, timeperiod=period)
        return dataframe

    def feature_engineering_expand_basic(self, dataframe: DataFrame, **kwargs) -> DataFrame:
        """
        FreqAI 基础特征工程
        """
        dataframe["%-pct-change"] = dataframe["close"].pct_change()
        dataframe["%-raw_volume"] = dataframe["volume"]
        dataframe["%-raw_price"] = dataframe["close"]
        return dataframe

    def feature_engineering_standard(self, dataframe: DataFrame, **kwargs) -> DataFrame:
        """
        FreqAI 标准特征工程
        """
        dataframe["%-day_of_week"] = (dataframe["date"].dt.dayofweek + 1) / 7
        return dataframe

    def set_freqai_targets(self, dataframe: DataFrame, metadata: dict, **kwargs) -> DataFrame:
        """
        设置 FreqAI 目标变量
        """
        # 设置分类目标
        self.freqai.class_names = ["down", "up"]
        dataframe['&s-up_or_down'] = np.where(
            dataframe["close"].shift(-100) > dataframe["close"], 'up', 'down'
        )
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        填充买入信号
        """
        dataframe.loc[
            (
                (dataframe['rsi'] < 30) &  # RSI 超卖
                (dataframe['macd'] > dataframe['macdsignal']) &  # MACD 金叉
                (dataframe['close'] < dataframe['bb_lowerband'])  # 价格低于布林带下轨
            ),
            'enter_long'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        填充卖出信号
        """
        dataframe.loc[
            (
                (dataframe['rsi'] > 70) &  # RSI 超买
                (dataframe['macd'] < dataframe['macdsignal']) &  # MACD 死叉
                (dataframe['close'] > dataframe['bb_upperband'])  # 价格高于布林带上轨
            ),
            'exit_long'] = 1

        return dataframe

    def rsi(self, dataframe: DataFrame, timeperiod: int = 14) -> DataFrame:
        """
        计算 RSI
        """
        delta = dataframe['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=timeperiod).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=timeperiod).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def macd(self, dataframe: DataFrame, fastperiod: int = 12, slowperiod: int = 26, signalperiod: int = 9) -> DataFrame:
        """
        计算 MACD
        """
        exp1 = dataframe['close'].ewm(span=fastperiod, adjust=False).mean()
        exp2 = dataframe['close'].ewm(span=slowperiod, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=signalperiod, adjust=False).mean()
        hist = macd - signal
        return {'macd': macd, 'macdsignal': signal, 'macdhist': hist}

    def bollinger_bands(self, dataframe: DataFrame, timeperiod: int = 20, stddev: float = 2.0) -> DataFrame:
        """
        计算布林带
        """
        mid = dataframe['close'].rolling(window=timeperiod).mean()
        std = dataframe['close'].rolling(window=timeperiod).std()
        upper = mid + stddev * std
        lower = mid - stddev * std
        return {'upper': upper, 'mid': mid, 'lower': lower} 