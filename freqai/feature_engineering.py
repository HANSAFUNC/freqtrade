from freqtrade.freqai.base_models.BaseRegressionModel import BaseRegressionModel
from freqtrade.freqai.data_kitchen import FreqaiDataKitchen
import pandas as pd
import numpy as np
from typing import Any, Dict

class FeatureEngineering(BaseRegressionModel):
    """
    FreqAI 特征工程示例
    """
    def feature_engineering_expand_all(self, dataframe: pd.DataFrame, period: int,
                                     metadata: Dict, **kwargs) -> pd.DataFrame:
        """
        特征工程扩展
        """
        # 价格特征
        dataframe['price_change'] = dataframe['close'].pct_change()
        dataframe['price_volatility'] = dataframe['close'].rolling(window=period).std()
        dataframe['price_momentum'] = dataframe['close'].pct_change(periods=period)
        
        # 成交量特征
        dataframe['volume_change'] = dataframe['volume'].pct_change()
        dataframe['volume_ma'] = dataframe['volume'].rolling(window=period).mean()
        dataframe['volume_std'] = dataframe['volume'].rolling(window=period).std()
        
        # 技术指标特征
        dataframe['rsi'] = self.rsi(dataframe, period=14)
        dataframe['macd'] = self.macd(dataframe)
        dataframe['bb_upper'], dataframe['bb_middle'], dataframe['bb_lower'] = self.bollinger_bands(dataframe)
        
        # 价格波动特征
        dataframe['high_low_ratio'] = dataframe['high'] / dataframe['low']
        dataframe['close_open_ratio'] = dataframe['close'] / dataframe['open']
        
        # 时间特征
        dataframe['hour'] = pd.to_datetime(dataframe['date']).dt.hour
        dataframe['day_of_week'] = pd.to_datetime(dataframe['date']).dt.dayofweek
        
        return dataframe

    def feature_engineering_expand_basic(self, dataframe: pd.DataFrame, period: int,
                                       metadata: Dict, **kwargs) -> pd.DataFrame:
        """
        基础特征工程
        """
        # 基础价格特征
        dataframe['price_change'] = dataframe['close'].pct_change()
        dataframe['volume_change'] = dataframe['volume'].pct_change()
        
        return dataframe

    def feature_engineering_standard(self, dataframe: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        标准特征工程
        """
        # 标准化特征
        for col in dataframe.columns:
            if col not in ['date', 'open', 'high', 'low', 'close', 'volume']:
                dataframe[col] = (dataframe[col] - dataframe[col].mean()) / dataframe[col].std()
        
        return dataframe

    def set_freqai_targets(self, dataframe: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        设置目标变量
        """
        # 计算未来收益率作为目标变量
        dataframe['&s-price_change'] = dataframe['close'].shift(-1) / dataframe['close'] - 1
        
        return dataframe

    def rsi(self, dataframe: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        计算 RSI
        """
        delta = dataframe['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def macd(self, dataframe: pd.DataFrame) -> pd.Series:
        """
        计算 MACD
        """
        exp1 = dataframe['close'].ewm(span=12, adjust=False).mean()
        exp2 = dataframe['close'].ewm(span=26, adjust=False).mean()
        return exp1 - exp2

    def bollinger_bands(self, dataframe: pd.DataFrame) -> tuple:
        """
        计算布林带
        """
        mid = dataframe['close'].rolling(window=20).mean()
        std = dataframe['close'].rolling(window=20).std()
        upper = mid + 2 * std
        lower = mid - 2 * std
        return upper, mid, lower 