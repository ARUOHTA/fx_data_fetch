from oandapyV20 import API
import os
import copy
import pandas as pd
import datetime
import bisect
from datetime import datetime ,timedelta
import oandapyV20.endpoints.instruments as instruments
from oandapyV20.types import DateTime
from dateutil.relativedelta import relativedelta

import your_account as ya

class OrderBook(object):
    """オーターデータ取得クラス"""

    def __init__(self, granularity):
        self.__BUCKETS = "buckets"

        self.__ORD_BOOK = "orderBook"
        self.__PSI_BOOK = "positionBook"
        self.__PRICE = "price"
        self.__LONG = "longCountPercent"
        self.__SHORT = "shortCountPercent"

        self.__TIME = "time"
        self.__CUR_PRICE = "price"
        self.__BUCKET_WIDTH = "bucketWidth"

        self.__DT_FMT = "%Y-%m-%dT%H:%M:00Z"
        self.__GRANULARITY = granularity

        self.__CUT_TH = 100  # 現レートから上下何本残すか

        self.__api = API(access_token=ya.access_token_live, environment="live")


    def __changeDateTimeFmt(self, dt):
        """"日付フォーマットの変換メソッド
        引数:
            dt (str): DT_FMT形式でフォーマットされた日付
        戻り値:
            tf_dt (str): 変換後の日付
        """
        tdt = datetime.strptime(dt, self.__DT_FMT)

        return tdt

    #二分探索(getInstrumentsOrderPositionBookでしか使えない)
    def __BinarySearch(self, list, item):
        """二分探索
        引数：
            list (list): 探索したいリスト
            item (object): 場所を探して入れたい対象物
        戻り値：
            mid (int): 入るインデックス
            guess: 挿入する一つ隣の値(右か左かわからないので調整が必要）
        """
        low = 0
        high = len(list) - 1
        while low <= high:
            mid = (low + high) //2
            guess = float(list[mid][self.__PRICE])
            if guess == item:
                return mid, guess
            if guess > item:
                high = mid-1
            else:
                low = mid+1
        return mid, guess

    def getInstrumentsOrderPositionBook(self, instrument, dt, former_ord=None, former_pos=None):
        """注文情報とポジション情報の取得
        引数：
            instrument (str): 通貨ペア
            dt (datetime): datetime型の時刻
        戻り値：
            ord_df (pd.DataFrame): 時刻dtにおける注文情報とポジション情報
            cur_price (時刻dtにおけるレート)
        """
        params = {
            "time": DateTime( dt ).value , #時刻
            #"alignmentTimezone": "Japan", # タイムゾーン　※タイムゾーンはプログラム内部はGMT、入力と出力だけは日本時間で行っています
            #"alignmentTimezone":"America/New_York"
        }

        #orderを取得
        ic_ord = instruments.InstrumentsOrderBook(instrument=instrument,
                                            params=params)

        try:
            self.__api.request(ic_ord)
        except:
            ic_ord.response = former_ord

        #現在のレートを取得
        cur_price = float(ic_ord.response[self.__ORD_BOOK][self.__CUR_PRICE])
        bucket_width = float(ic_ord.response[self.__ORD_BOOK][self.__BUCKET_WIDTH])

        #一応取得したときについてきた時刻を保存
        time = pd.to_datetime(self.__changeDateTimeFmt(
                    ic_ord.response[self.__ORD_BOOK][self.__TIME]))

        #二分探索で現在レートのインデックスを探す
        idx_th = bucket_width * self.__CUT_TH
        ord_cur_ind, ord_guess = self.__BinarySearch(ic_ord.response[self.__ORD_BOOK][self.__BUCKETS], cur_price)
        if ord_guess < cur_price:
            ord_cur_ind += 1

        #生データをから配列に変換
        price_data = [0]*(self.__CUT_TH*2)
        ord_long_data = [0]*(self.__CUT_TH*2)
        ord_short_data = [0]*(self.__CUT_TH*2)
        for i, raw in enumerate(ic_ord.response[self.__ORD_BOOK][self.__BUCKETS][ord_cur_ind-self.__CUT_TH:ord_cur_ind+self.__CUT_TH]):
            price_data[i] = float(raw[self.__PRICE])
            ord_long_data[i] = float(raw[self.__LONG])
            ord_short_data[i] = -float(raw[self.__SHORT])
        
        #positionを取得
        ic_pos = instruments.InstrumentsPositionBook(instrument=instrument,
                                                    params=params)
        #orderの時と同じ処理
        try:
            self.__api.request(ic_pos)
        except:
            ic_pos.response = former_pos

        pos_cur_ind, pos_guess = self.__BinarySearch(ic_pos.response[self.__PSI_BOOK][self.__BUCKETS], cur_price)
        if pos_guess < cur_price:
            pos_cur_ind += 1

        pos_long_data = [0]*(self.__CUT_TH*2)
        pos_short_data = [0]*(self.__CUT_TH*2)
        for i, raw in enumerate(ic_pos.response[self.__PSI_BOOK][self.__BUCKETS][pos_cur_ind-self.__CUT_TH:pos_cur_ind+self.__CUT_TH]):
            pos_long_data[i] = float(raw[self.__LONG])
            pos_short_data[i] = -float(raw[self.__SHORT])

        #DataFrameとして出力
        #ord_df = pd.DataFrame([dt.strftime('%H:%M')] + [cur_price] + price_data + ord_long_data + ord_short_data + pos_long_data + pos_short_data, columns=[dt.strftime('%Y-%m-%d')]).T
        ord_df = pd.DataFrame([cur_price] + price_data + ord_long_data + ord_short_data + pos_long_data + pos_short_data, columns=[dt + timedelta(hours=9)]).T

        return ord_df, cur_price, ic_ord.response, ic_pos.response

        
    def getInstrumentsCandles(self, instrument, since, until):
        """ろうそく足でのレート変動情報を取得
        引数：
            instrument (str): 通貨ペア
            since (datetime): 始まりの時刻
            until (datetime): 終わりの時刻
        戻り値：
            df (pd.DataFrame): sinceからuntilまでのろうそく足のレート情報
        """

        params = {
            "granularity": self.__GRANULARITY,  # 取得する足
            "from": DateTime( since ).value,
            "to": DateTime( until ).value,          # 取得する足数
            "price": "B",        # Bid
            #"alignmentTimezone": "Japan", # タイムゾーン 
            #"alignmentTimezone":"America/New_York"
        }


        instruments_candles = instruments.InstrumentsCandles(instrument=instrument, params=params)

        #データの取得
        self.__api.request(instruments_candles)
        response = instruments_candles.response

        #データを配列に変換
        data = []
        for raw in response['candles']:
            dt = datetime.strptime(raw['time'], "%Y-%m-%dT%H:%M:00.000000000Z") + timedelta(hours=9)
            bids = raw['bid']
            data.append([dt, 
                        bids['o'], 
                        bids['h'], 
                        bids['l'], 
                        bids['c']])

        df = pd.DataFrame(data, columns= ['Time', 'Open', 'High', 'Low', 'Close']).set_index('Time')
        return df


    def getHistoryOrderPosition(self, instrument, since, until): 
        """一定期間の注文情報とポジション情報を5分おきに取得
        引数：
            instrument (str): 通貨ペア
            since (datetime): 始まりの時刻
            until (datetime): 終わりの時刻
        戻り値：
            df (pd.DataFrame): sinceからuntilまでの注文情報とポジション情報
        """

        #配列のインデックスの名前を指定
        price_name = ['Price:'+str(i-self.__CUT_TH) for i in list(set(range(2*self.__CUT_TH+1))-set([self.__CUT_TH]))]
        ord_long_name = ['Od-L:'+str(i-self.__CUT_TH) for i in list(set(range(2*self.__CUT_TH+1))-set([self.__CUT_TH]))]
        ord_short_name = ['Od-S:'+str(i-self.__CUT_TH) for i in list(set(range(2*self.__CUT_TH+1))-set([self.__CUT_TH]))]
        pos_long_name = ['Po-L:'+str(i-self.__CUT_TH) for i in list(set(range(2*self.__CUT_TH+1))-set([self.__CUT_TH]))]
        pos_short_name = ['Po-S:'+str(i-self.__CUT_TH) for i in list(set(range(2*self.__CUT_TH+1))-set([self.__CUT_TH]))]

        #col_name = ['Time'] + ['CurrentPrice'] + price_name + ord_long_name + ord_short_name + pos_long_name + pos_short_name 
        col_name = ['CurrentPrice'] + price_name + ord_long_name + ord_short_name + pos_long_name + pos_short_name 
        dt = since

        #5分ごとにデータを取得してDataFrameを作成、ただし市場が閉じている週末は飛ばす
        df = pd.DataFrame([])
        days = ["Fri", "Sat", "Sun"]
        former_ord = None
        former_pos = None
        while True:
            if dt >= until: break
            if (dt.strftime("%a") not in days) or (dt.strftime("%a") == "Fri" and dt.strftime("%H%M") < "2200") or (dt.strftime("%a") == "Sun" and dt.strftime("%H%M") >= "2100"):
                raw, price, former_ord, former_pos  = self.getInstrumentsOrderPositionBook(instrument, dt, former_ord, former_pos)
                print(f"{instrument}:{dt + timedelta(hours=9)}:{price}")
                df = pd.concat([df, raw])
            dt = dt + timedelta(minutes=5)

        df.columns = col_name
        return df


    def getHistoryCandles(self, instrument, since, until):
        """1週間おきに区切ってCandle情報を取得
        引数:
            instrument (str): 通貨ペア
            since (datetime): 始まりの時刻
            until (datetime): 終わりの時刻
        戻り値:
            df (pd.DataFrame): sinceからuntilまでのろうそく足のレート情報
        """
        df = pd.DataFrame([])
        dt1 = since
        dt2 = min(since + timedelta(weeks=1), until)
        while True:
            if dt1 == dt2:
                break
            try:
                raw = self.getInstrumentsCandles(instrument, dt1, dt2)
            except:
                raw = pd.Series([])
            df = pd.concat([df, raw])
            dt1 = dt2
            dt2 = min(dt2 + timedelta(weeks=1), until)
        return df

    def getCandleOrders(self, instrument, since, until):
        """一定期間の注文情報とポジション情報、レート変動を一度に取得
        引数：
            instrument (str): 通貨ペア
            since (datetime): 始まりの時刻
            until (datetime): 終わりの時刻
        戻り値：
            df (pd.DataFrame): sinceからuntilまでの注文情報とポジション情報、レート変動
        """

        df1 = self.getHistoryOrderPosition(instrument, since, until)
        df2 = self.getHistoryCandles(instrument, since, until)
        return df1.join(df2, how="outer")

if __name__ == "__main__":
    cs = OrderBook("M5")
    instrument_list = ["EUR_USD", "GBP_USD", "AUD_USD", "USD_JPY", "USD_CAD", "USD_CHF", "EUR_JPY", "GBP_JPY", "AUD_JPY", "EUR_AUD", "EUR_GBP", "EUR_CHF", "GBP_CHF", "NZD_USD", "XAG_USD", "XAU_USD"]
    start    = datetime.strptime( '2020-07-01 00:00:00' ,'%Y-%m-%d %H:%M:%S' ) #日本時間で指定してください
    end      = datetime.strptime( '2020-07-02 00:00:00' ,'%Y-%m-%d %H:%M:%S' ) #日本時間で指定してください

    
    #テスト用1通貨ペア
    df = cs.getCandleOrders(instrument_list[0], start - timedelta(hours=9), end - timedelta(hours=9))
    df = df.fillna(method='ffill')
    df.to_csv(f"data/{instrument_list[0]}_{start.strftime('%Y%m%d%H%M')}_{end.strftime('%Y%m%d%H%M')}.csv")
    
    """
    #本番用全通貨ペア
    os.makedirs(f"data/{start.strftime('%Y%m%d%H%M')}_{end.strftime('%Y%m%d%H%M')}", exist_ok = True)
    for i in range(len(instrument_list)):
        df = cs.getCandleOrders(instrument_list[i], start - timedelta(hours=9), end - timedelta(hours=9))
        df = df.fillna(method='ffill')
        df.to_csv(f"data/{start.strftime('%Y%m%d%H%M')}_{end.strftime('%Y%m%d%H%M')}/{instrument_list[i]}_{start.strftime('%Y%m%d%H%M')}_{end.strftime('%Y%m%d%H%M')}.csv")
    """