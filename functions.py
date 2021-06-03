import pyupbit
import requests
import pandas as pd
import pprint
import time
import datetime
from functions import *
pd.set_option('display.max_rows', None)

key_file = open("key 저장 텍스트")
lines = key_file.readlines()
access = lines[0].strip() # access 키 불러오기,  \n제거 메소드 strip().
secret = lines[1].strip() # secret 키 불러오기.
key_file.close()
upbit = pyupbit.Upbit(access, secret) 


# UNIT = 한 코인당 투자금액
#### 수정 주의 ####
UNIT = 100000 
#### 수정 주의 ####


tickers = pyupbit.get_tickers(fiat="KRW")
Money = upbit.get_balance("KRW")


# 신생코인 제외 함수. (현재 미사용) 
def except_new(ticker):
    
    prices = pyupbit.get_ohlcv(ticker, interval="day")
    if len(prices) <= 10: # 등재된지 10일을 넘지 않은 신생 코인은 제외.
        return ticker  
    else:
        return 0


# UNIT 금액 터미널에 출력해주는 함수.
def print_UNIT():
    
    print('현재 UNIT은', format(int(UNIT),","), '원 입니다.')
    return UNIT


# 업비트 주문가능 금액에 맞게 반올림해주는 함수.
def smart_round(number):
    
    if number > 0:  
        if 0< number <10:
            return round(number, 2)
        elif 10<= number <100:
            return round(number, 1)
        elif 100<= number <1000:
            return int(number)
        elif 1000<= number <10000:
            return round(number, -1)
        elif 10000<= number <100000:
            return round(number, -1)
        elif 100000<= number <1000000:
            return round(number, -2)
        elif 1000000<= number <10000000:
            return round(number, -3)
        elif 10000000<= number <100000000:
            return round(number, -3)
        elif 100000000<= number <1000000000:
            return round(number, -4)
        else:
            return number
    else:
        return None


# Slack으로 메시지 보내주는 함수.
def post_message(token, channel, text):
    
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+token},
        data={"channel": channel,"text": text})
    print(response)


# 전일대비 등락율 내림차순 함수.
def target_coin(coin):  
    
    df = pyupbit.get_ohlcv(coin)
    yesterday = df.iloc[-2] # 전일데이터 load . 
    yesterday_close = yesterday['close'] # 전일종가.
    price = pyupbit.get_current_price(coin) # 현재가.
    target = (price - yesterday_close) / yesterday_close * 100 # 전일대비 등락률.
    return target


# 매수주문 함수. 
def buy(ticker, rate):
    
    BUY_FACTOR = 1 + rate/100
    now_price = pyupbit.get_current_price(ticker)
    BUY_price = smart_round(BUY_FACTOR*now_price)
    BUY_volume = UNIT/BUY_price
    if rate <= 0: 
        temp = upbit.buy_limit_order(ticker, BUY_price, BUY_volume)
        Money = upbit.get_balance("KRW")
        print("매수주문가격:", BUY_price, "수량:", BUY_volume, "남은현금:", format(int(Money),","),"원")
        time.sleep(0.2)
        return temp
    else: 
        print(ticker, ">>> buy() 함수 에러.")
        time.sleep(0.2)
        pass


# UNIT 2배 매수주문 함수. (현재 미사용)
def buy2X(ticker, rate):
    
    BUY_FACTOR = 1 + rate/100
    now_price = pyupbit.get_current_price(ticker)
    BUY_price = smart_round(BUY_FACTOR*now_price)
    BUY_volume = 2*(UNIT/BUY_price) # 2배 매수
    if rate <= 0: 
        temp = upbit.buy_limit_order(ticker, BUY_price, BUY_volume)
        Money = upbit.get_balance("KRW")
        print("[3차]매수주문가격:", BUY_price, "수량:", BUY_volume, "남은현금:", format(int(Money),","),"원")
        time.sleep(0.2)
        return temp    
    else: 
        print(ticker, ">>>>>> buy2X() 함수 에러.")
        time.sleep(0.2)
        pass


# 매도주문 함수. 평단가를 기준해서 보유량 전부를 매도
def sell(ticker, rate):
    
    balance = upbit.get_balance(ticker)
    avg_price = upbit.get_avg_buy_price(ticker)
    SELL_FACTOR = 1 + rate/100
    SELL_price = smart_round(SELL_FACTOR*avg_price)
    SELL_volume = balance
    if rate >= 0: 
        temp = upbit.sell_limit_order(ticker, SELL_price, SELL_volume)
        Money = upbit.get_balance("KRW")
        print("매도주문가격:", SELL_price, "수량:", SELL_volume, "남은현금:", format(int(Money),","),"원")
        time.sleep(0.2)
        return temp
    else: 
        print(ticker, ">>> sell() 함수 에러.")
        time.sleep(0.2)
        pass


# 특정주문목록에 대한 uuid 가져오기.
def get_data_uuid(temp): # 매수/매도 함수로부터의 반환값을 인자로 받음.
    
    if str(type(temp)) == "<class 'dict'>":
        target = pd.DataFrame([temp])
    elif str(type(temp)) == "<class 'list'>":
        target = pd.DataFrame(temp)
    if target.empty:
        print(target)
        uuid = 'Upbit_Error' # 업비트 에러시, 이 값을 return 한다. >>> get_state 함수랑 연결.
        return uuid 
    if not target.empty:
        print(target)
        uuid = target['uuid']
        uuid = uuid[0] # 시리즈안에 있는 uuid 값 리스트로 반환.
        return uuid


# 특정주문 state 가져오기. 
def get_state(uuid): 
    
    Gate = True
    if uuid == 'Upbit_Error':
        state = 'Upbit_Error' # 업비트 에러시, 이 값을 return 한다.
        return state
    else:
        while Gate == True:
            # temp = 주문내역 조회.
            temp = upbit.get_order(uuid)
            time.sleep(0.2)
            # temp 를 DataFrame 으로 변환. target = DataFrame 으로 변환된 temp.
            if str(type(temp)) == "<class 'dict'>":
                target = pd.DataFrame([temp])
            elif str(type(temp)) == "<class 'list'>":
                target = pd.DataFrame(temp)
            else:
                print(temp)
                print('get_state 함수 비정상적 작동.')
            # target 안에 있는 state 값 추출.
            if target.empty:
                print('target이 비어있음.')
                continue
            else:
                # 정상작동.
                if 'state' in target.columns:
                    state = target['state']
                    state = state[0] 
                    return state # 함수에서 return 은 함수를 종료시키므로, break 가 따로 필요없다.
                # 업비트 에러시. 'message': 'Jwt의 query를 검증하는데 실패하였습니다.' 뜨면 주문 다시 요청.
                else:
                    print(target)
                    print('state가 target 데이터프레임에 없음. upbit.get_order(uuid) 재실행.')
                    time.sleep(3)
                    continue


# 특정주문목록 DataFrame으로 가져오기. 주문함수 자체를 받음. 
def get_data(temp): #ticker 또는 uuid 입력. ticker이면 [미체결주문]이, uuid면 체결/미체결 [상관없이] 해당 주문에대한 정보를 가져온다.

    if str(type(temp)) == "<class 'dict'>":
        target = pd.DataFrame([temp])
    elif str(type(temp)) == "<class 'list'>":
        target = pd.DataFrame(temp)
    return target


# 특정주문 uuid 가져오기. 
def get_uuid(ticker): #ticker 또는 uuid 입력. ticker이면 [미체결주문]이, uuid면 체결/미체결 [상관없이] 해당 주문에대한 정보를 가져온다.
    
    temp = upbit.get_order(ticker)
    if str(type(temp)) == "<class 'dict'>":
        target = pd.DataFrame([temp])
    elif str(type(temp)) == "<class 'list'>":
        target = pd.DataFrame(temp)
    if target.empty:
        print(target)
        uuid = 'Upbit_Error' # 업비트 에러시, 이 값을 return 한다. >>> get_state 함수랑 연결.
        return uuid 
    if not target.empty:
        print(target)
        uuid = target['uuid']
        uuid = uuid[0] # 시리즈안에 있는 uuid 값 리스트로 반환.
        return uuid


# 특정주문 uuid "들" 가져오기. (반환값 Series)
def get_uuids(ticker): # ticker 또는 uuid 입력. ticker이면 [미체결주문]이, uuid면 체결/미체결 [상관없이] 해당 주문에대한 정보를 가져온다.
    
    temp = upbit.get_order(ticker)
    if str(type(temp)) == "<class 'dict'>":
        target = pd.DataFrame([temp])
    elif str(type(temp)) == "<class 'list'>":
        target = pd.DataFrame(temp)
    uuids = target['uuid']
    uuids # 즉 uuids를 시리즈로 반환. 
    return uuids


# 미체결 목록개수 반환 함수. 
def get_len(ticker): # ticker 만 입력할 것
    
    temp = upbit.get_order(ticker)
    if str(type(temp)) == "<class 'dict'>":
        target = pd.DataFrame([temp])
    elif str(type(temp)) == "<class 'list'>":
        target = pd.DataFrame(temp)
    length = len(target)
    return length






