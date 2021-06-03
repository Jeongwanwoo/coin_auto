import pyupbit
import requests
import pandas as pd
import pprint
import time
import datetime
from functions import *
from get_ValuedAssets import *
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

key_file = open("key 저장 텍스트")
lines = key_file.readlines()
access = lines[0].strip() # access 키 불러오기,  \n제거 메소드 strip().
secret = lines[1].strip() # secret 키 불러오기.
key_file.close()
upbit = pyupbit.Upbit(access, secret) 


def get_ValuedAssets():
    temp = upbit.get_balances() 
    target = pd.DataFrame(temp)
    CoinSum = 0.0
    for i in range(1, len(target)): 
        time.sleep(0.05)
        ticker = "KRW-"+ target.iloc[i,0]
        locked_balance = float(target.iloc[i,2])
        cur_price = pyupbit.get_current_price(ticker)

        temp = cur_price*locked_balance
        CoinSum += temp

    KRW_Money = upbit.get_balance_t('KRW')
    ValuedAssets = KRW_Money + CoinSum
    print('총 보유자산:',format(int(ValuedAssets),","),"원")
    return ValuedAssets

