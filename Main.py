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

# 프로그램 시작전 항상, cmd터미널에 아래 명령어 시행하기. (로그파일 기록을 위해서.)
# Python Debug Console 메시지들 저장 하는 법: (파일이 있는 폴더까지 이동후) "python 파일명.py > 로그파일이름.txt"
#                                                                       예) python Main.py > log.txt
key_file = open("key 저장 텍스트")
lines = key_file.readlines()
access = lines[0].strip() # access 키 불러오기,  \n제거 메소드 strip().
secret = lines[1].strip() # secret 키 불러오기.
key_file.close()
upbit = pyupbit.Upbit(access, secret) 
myToken = "Slack 토큰" # Slack 토큰. 


######################################## 전략 설명 ########################################
# 투자 알고리즘 >>> 1) 한 시점에서 코인의 전일대비 등략률이 -1% 이하이면 -20 ~ -30 으로 매수 주문. (새벽3시를 기준으로함. 가장 하락세가 강하다고 판단.)
#                  2) 1차매수(= L0주문) 그룹별로 퍼센트 다름. (g1 = -30, g2 = -25, g3 = -20)
#                  3) 2차매수 -25% 주문.
#                  4) 2차매수 완료 후 hold 사이클 진행.
#                  5) 매도주문은 +15% 기존과 동일함. 
#                  6) 단, 최초주문시 시장가에서 +7% 상승시 상승가에서 -20% 재매수 주문.
###########################################################################################




# ========================================================================================================
# Dec_tickers 구하기. & L_df 객체생성 & Dec_tickers_today 객체생성  @재시작시에는, 박스처리 한 부분 주석처리@
# 1. Dec_tickers 구하기. (코인별 변동률 내림차순 데이터 프레임)
coin_fr = []
tickers = pyupbit.get_tickers(fiat="KRW")
for i in tickers : 
    coin_fr.append(target_coin(i))
    coin_df = pd.DataFrame(data = list(zip(tickers, coin_fr)), columns = ['ticker', 'Fluctuation'])
    coin_decline = coin_df[coin_df.Fluctuation < -1].sort_values(by = ['Fluctuation'], ascending = False) 
    Dec_tickers = coin_decline.get('ticker')
    time.sleep(0.08)  

# 등략률 기준 그룹화.
g1 = coin_decline[(-5 < coin_decline.Fluctuation) & (coin_decline.Fluctuation <= -1)] 
g2 = coin_decline[(-9 < coin_decline.Fluctuation) & (coin_decline.Fluctuation <= -5)]
g3 = coin_decline[coin_decline.Fluctuation <= -9]

Dec_tickers.to_csv('Dec_tickers.csv', index = True) 
g1.to_csv('g1.csv', index = True)
g2.to_csv('g2.csv', index = True)
g3.to_csv('g3.csv', index = True)

# 2. L_df 객체생성. (매도,매수시 uuid 저장 데이터 프레임)
tickers = pyupbit.get_tickers(fiat="KRW")
L_list = ['L0uuid', 'L1Suuid', 'L1Buuid', 'L2Suuid', 'L2Buuid', 'L3Suuid', 
          'price', 'date', 'L0', 'L1', 'L2', 'L3', 'Hold'] 
L_df = pd.DataFrame(data = '-', index = tickers,
                columns = L_list)
L_df.iloc[:, 8:] = False
L_df['price'] = 0
L_df.to_csv('L_df.csv', index = True)

# 3. Dec_tickers_today 객체생성. (갱신시 등략률)
temp = pd.DataFrame(data = [], columns = ['ticker', 'Fluctuation'])
Dec_tickers_today = temp.get('ticker')
Dec_tickers_today.to_csv('Dec_tickers_today.csv', index = False)
# ========================================================================================================


now = datetime.datetime.now()
MonthDate = now.strftime('%m-%d')
L1Sstate = '-'
L1Bstate = '-'
L2Sstate = '-'
L2Bstate = '-'
L3Sstate = '-'
L0uuid = '-'
L1Suuid = '-'
L1Buuid = '-'
L2Suuid = '-'
L2Buuid = '-'
L3Suuid = '-'
price = 0
date = '-'
cur_price = 0
L0 = False
L1 = False
L2 = False
L3 = False
Hold = False

B_g1 = -30 # 최초주문 즉, L0주문시 buy() 함수에 들어가는 인자. 
B_g2 = -25 
B_g3 = -20 
S = 15 # sell() 함수에 들어가는 인자. 몇 % 가격으로 매도 할건지 쓰면 된다. 항상 0또는 [양수]여야 한다. ex) S = 15 >>> 위로15% 매도.
B = -25 # buy() 함수에 들어가는 인자. 몇 % 가격으로 매수 할건지 쓰면 된다. 항상 0또는 [음수]여야 한다. ex) B = -15 >>> 아래로15% 매수. #! 모두 -25로 통일!
Money = upbit.get_balance("KRW")
UNIT = print_UNIT() # 현재 UNIT 크기 출력. (UNIT은 functions 에서 지정, 한 코인당 투자금액을 의미)
DO_NOT_BUY = []  # 특정 코인 매수 금지.
DO_NOT_SELL = [] # 특정 코인 매도 금지.
TargetProfit =  10000000 # 목표수익. (목표수익 달성시 윈도우 드레싱 작동)
ValuedAssets = get_ValuedAssets() # 총 보유자산 = ValuedAssets
time.sleep(1)
tickers = pyupbit.get_tickers(fiat="KRW")
L_df = pd.read_csv('L_df.csv', index_col=0) 

# 목표수익에 도달할때까지 무한loop.
while ValuedAssets < TargetProfit: 
    L_df.to_csv('L_df.csv', index = True)
    L_df = pd.read_csv('L_df.csv', index_col=0)
    L_df = L_df
    Dec_tickers = pd.read_csv('Dec_tickers.csv')
    Dec_tickers_today = pd.read_csv('Dec_tickers_today.csv')
    D1 = Dec_tickers.get('ticker') 
    D2 = Dec_tickers_today.get('ticker')
    if ticker in (D1.values or D2.values):
        L0 = True
        L_df.loc[ticker, 'L0'] = L0
    g1 = pd.read_csv('g1.csv', index_col=0)
    g2 = pd.read_csv('g2.csv', index_col=0)
    g3 = pd.read_csv('g3.csv', index_col=0)
    now = datetime.datetime.now()
    DO_NOT_BUY
    print(now)
    print('DO_NOT_BUY >>>',DO_NOT_BUY)
    # 새벽 3시 갱신. (새벽 3시 기준 코인들의 등략률을 가져옴)
    if not (now.hour == 3 and 1 <= now.minute <= 10): # Dec_tickers 갱신시각 빼고 계속 진행. 
        now = datetime.datetime.now()   
        for ticker in tickers:
            try: 
                L_df = L_df
                L_df.to_csv('L_df.csv', index = True) # 프로그램 종료를 대비하여 L_df 저장. index = True 로 안하면 인덱스(코인 이름들) 저장안됨.
                L_df = pd.read_csv('L_df.csv', index_col=0) 
                # 알고리즘 실행.
                time.sleep(0.5)
                Money = upbit.get_balance("KRW")
                # 반복문이니까 호출해서 갱신해야 함.
                L_df = L_df
                L0uuid = L_df.loc[ticker, 'L0uuid']
                L1Suuid = L_df.loc[ticker, 'L1Suuid']
                L1Buuid = L_df.loc[ticker, 'L1Buuid']
                L2Suuid = L_df.loc[ticker, 'L2Suuid']
                L2Buuid = L_df.loc[ticker, 'L2Buuid']
                L3Suuid = L_df.loc[ticker, 'L3Suuid']
                L0 = L_df.loc[ticker, 'L0']
                L1 = L_df.loc[ticker, 'L1']
                L2 = L_df.loc[ticker, 'L2']
                L3 = L_df.loc[ticker, 'L3']
                Hold = L_df.loc[ticker, 'Hold']
                # 검증대상들 : DO_NOT_BUY 에 속해있지 않은 코인들.
                if ticker not in DO_NOT_BUY: 
                    L0 = L0
                    L1 = L1
                    L2 = L2
                    L3 = L3
                    Hold = Hold
                    print(ticker, '검증시작.')
                    time.sleep(0.5)
                    L0uuid = L0uuid # 새 사이클 시작시, 갱신을 위해서 L0uuid 추가.
                    # L0 주문 대상: 
                    if L0 == True:
                        print(ticker,'>>> L0 사이클 시작')
                        balance = upbit.get_balance(ticker)
                        price = pyupbit.get_current_price(ticker)
                        now = datetime.datetime.now()
                        MonthDate = now.strftime('%m-%d')
                        # L0 주문 판단.
                        Money = upbit.get_balance("KRW")
                        if Money >= 2*UNIT: # 매수주문 필터. (충분한 잔고 없을시 주문X)
                            if balance == 0: # 코인잔고balance가 0이면, 해당 코인이 없다는 뜻이므로 진행.
                                if ticker in g1.values: 
                                    target = buy(ticker, B_g1)  # L0 주문실행.
                                    print(ticker, '>>>', B_g1, '가격으로 주문함.')
                                elif ticker in g2.values:
                                    target = buy(ticker, B_g2)  # L0 주문실행.
                                    print(ticker, '>>>', B_g2, '가격으로 주문함.')
                                elif ticker in g3.values:        
                                    target = buy(ticker, B_g3)  # L0 주문실행.
                                    print(ticker, '>>>', B_g3, '가격으로 주문함.')
                                else:
                                    continue
                                L0uuid = get_data_uuid(target)
                                L_df.loc[ticker, 'L0uuid'] = L0uuid
                                L_df.loc[ticker, 'price'] = price
                                L_df.loc[ticker, 'date'] = MonthDate
                                L1 = True 
                                L_df.loc[ticker, 'L1'] = L1
                                L0 = False 
                                L_df.loc[ticker, 'L0'] = L0
                                continue
                        else:
                            continue  

                    if L1 == True:
                        print(ticker,'>>> L0 사이클 진행중')
                        L0state = get_state(L0uuid) # 실시간 데이터니까 state들에 대한 "갱신"이 필요.
                        if L0state == 'wait':
                            cur_price = pyupbit.get_current_price(ticker)
                            price = L_df.loc[ticker, 'price']
                            # L0주문당시 현재가보다 7%이상 올랐다면, 주문취소하고 -20으로 새롭게 주문한다.
                            if cur_price >= 1.07*price:
                                print(ticker, '>>> 7%이상 상승. 새롭게 L0 주문.')
                                upbit.cancel_order(L0uuid) # 기존 L0 주문 취소.
                                target = buy(ticker, -30)  # 새로운 L0 주문실행.
                                L0uuid = get_data_uuid(target)
                                L_df.loc[ticker, 'L0uuid'] = L0uuid
                                L_df.loc[ticker, 'price'] = price 
                                continue
                            else:
                                continue 
                        # L0 주문(state)이 체결되었으면, L1 매도, 매수 주문.
                        if L0state == 'done':
                            L1Suuid = L_df.loc[ticker, 'L1Suuid']
                            balance = upbit.get_balance(ticker) # balance = 코인 보유량.
                            if balance > 0: # 매도주문 필터로, balance 추가. >>> 중복 매도주문 방지.
                                print('>>> L1 사이클 시작')
                                # L1매도주문 
                                print('>>> L1매도주문')
                                target = sell(ticker, S) # >>> 항상 매도먼저 주문할 것.
                                L1Suuid = get_data_uuid(target)
                                L_df.loc[ticker, 'L1Suuid'] = L1Suuid
                                L1Sstate = get_state(L1Suuid)
                            Money = upbit.get_balance("KRW")
                            if Money >= 2*UNIT: # 매수주문 필터. (충분한 잔고 없을시 주문X)
                                # L1매수주문
                                print('>>> L1매수주문')
                                target = buy(ticker, B)
                                L1Buuid = get_data_uuid(target)
                                L_df.loc[ticker, 'L1Buuid'] = L1Buuid
                                L1Bstate = get_state(L1Buuid)
                                L2 = True 
                                L_df.loc[ticker, 'L2'] = L2
                                L1 = False 
                                L_df.loc[ticker, 'L1'] = L1
                                continue

                    if L2 == True:
                        print(ticker,'>>> L1 사이클 진행중')
                        L1Sstate = get_state(L1Suuid) # 실시간 데이터니까 state들에 대한 "갱신"이 필요.
                        L1Bstate = get_state(L1Buuid)
                        time.sleep(0.5)
                        # L1 매도주문(L1Sstate)이 체결되었으면, L1매수주문L1Buuid 취소시키고 다시, L0부터.
                        if L1Sstate == 'done':
                            print(">>> L1 매수주문 취소")
                            upbit.cancel_order(L1Buuid)
                            # 데이터 초기화.
                            L0uuid = '-'
                            L_df.loc[ticker, 'L0uuid'] = L0uuid
                            L1Suuid = '-'
                            L_df.loc[ticker, 'L1Suuid'] = L1Suuid
                            L1Buuid = '-'
                            L_df.loc[ticker, 'L1Buuid'] = L1Buuid
                            L2Suuid = '-'
                            L_df.loc[ticker, 'L2Suuid'] = L2Suuid
                            L2Buuid = '-'
                            L_df.loc[ticker, 'L2Buuid'] = L2Buuid
                            L3Suuid = '-'
                            L_df.loc[ticker, 'L3Suuid'] = L3Suuid
                            L0 = False
                            L_df.loc[ticker, 'L0'] = L0
                            L1 = False
                            L_df.loc[ticker, 'L1'] = L1
                            L2 = False
                            L_df.loc[ticker, 'L2'] = L2
                            L3 = False
                            L_df.loc[ticker, 'L3'] = L3
                            Hold = False
                            L_df.loc[ticker, 'Hold'] = Hold
                            continue
                        #* L1 매수주문(L1Bstate)이 체결되었으면, L1매도주문L1Suuid 을 취소하고, L2매도주문을 걸고 HOLD 한다.
                        elif L1Bstate == 'done': 
                            balance = upbit.get_balance(ticker) # balance = 코인 보유량.
                            if balance > 0: # 매수주문 필터. (충분한 잔고 없을시 주문X)
                                print('>>> L2 사이클 시작')
                                # L1매도주문.[취소]
                                print('>>> L1 매도주문 [취소]')
                                upbit.cancel_order(L1Suuid)
                                time.sleep(2)
                                # L2매도주문. 
                                print('>>> L2매도주문')
                                target = sell(ticker, S) 
                                L2Suuid = get_data_uuid(target)
                                L_df.loc[ticker, 'L2Suuid'] = L2Suuid
                                L2Sstate = get_state(L2Suuid)
                                # HOLD
                                DO_NOT_BUY.append(ticker)
                                print(ticker,'>>> 홀드.')
                                Hold = True
                                L_df.loc[ticker, 'Hold'] = Hold
                                L2 = False
                                L_df.loc[ticker, 'L2'] = L2
                                continue

                    if Hold == True:
                        print(ticker,'>>> 홀드 사이클 진행중')
                        L2Sstate = get_state(L2Suuid) 
                        if L2Sstate == 'done':
                            print('>>> !!! L3 탈출 !!!')
                            # 데이터 초기화 
                            L0uuid = '-'
                            L_df.loc[ticker, 'L0uuid'] = L0uuid
                            L1Suuid = '-'
                            L_df.loc[ticker, 'L1Suuid'] = L1Suuid
                            L1Buuid = '-'
                            L_df.loc[ticker, 'L1Buuid'] = L1Buuid
                            L2Suuid = '-'
                            L_df.loc[ticker, 'L2Suuid'] = L2Suuid
                            L2Buuid = '-'
                            L_df.loc[ticker, 'L2Buuid'] = L2Buuid
                            L3Suuid = '-'
                            L_df.loc[ticker, 'L3Suuid'] = L3Suuid
                            L0 = False
                            L_df.loc[ticker, 'L0'] = L0
                            L1 = False
                            L_df.loc[ticker, 'L1'] = L1
                            L2 = False
                            L_df.loc[ticker, 'L2'] = L2
                            L3 = False
                            L_df.loc[ticker, 'L3'] = L3
                            Hold = False
                            L_df.loc[ticker, 'Hold'] = Hold
                            continue
                        else:
                            print('>>> 아직 안 팔림')          
                    
                    if (L0 and L1 and L2 and Hold) == False:
                        print(ticker,'>>> 매수대상 아님.')
                    else: 
                        pass             
                else:
                    pass         
                L_df = L_df
                L_df.to_csv('L_df.csv', index = True) # 프로그램 종료를 대비하여 L_df 저장. 
            except Exception as e: # 업비트 에러뜨면 프로그램 60초간 중지 후, 재실행.
                L_df = L_df
                L_df.to_csv('L_df.csv', index = True) # 일단 그동안 데이터들 저장. (저장시 index True로 해야한다)
                Dec_tickers.to_csv('Dec_tickers.csv', index = True) # 일단 그동안 데이터들 저장.
                Dec_tickers_today.to_csv('Dec_tickers_today.csv', index = True)
                print('codeblue : ', e) 
                time.sleep(60)
                continue
        now = datetime.datetime.now()
        time.sleep(1)
        ValuedAssets = get_ValuedAssets()

    else: # L0 주문 대상 갱신. >>> Dec_tickers_today
        coin_fr = [] # coin_fr 이 for문 밖에 있어야한다. 안에 있으면 에러뜸.
        tickers = pyupbit.get_tickers(fiat="KRW")
        for i in tickers : 
            coin_fr.append(target_coin(i))
            coin_df = pd.DataFrame(data = list(zip(tickers, coin_fr)), columns = ['ticker', 'Fluctuation'])
            coin_decline = coin_df[coin_df.Fluctuation < -1].sort_values(by = ['Fluctuation'], ascending = False) 
            Dec_tickers_today = coin_decline.get('ticker')
            time.sleep(0.08)

        g1 = coin_decline[(-5 < coin_decline.Fluctuation) & (coin_decline.Fluctuation <= -1)] 
        g2 = coin_decline[(-9 < coin_decline.Fluctuation) & (coin_decline.Fluctuation <= -5)]
        g3 = coin_decline[coin_decline.Fluctuation <= -9]

        print('Dec_tickers_today: ', Dec_tickers_today)
        print('g1: ', g1)
        print('g2: ', g2)
        print('g3: ', g3)
        now = datetime.datetime.now()
        print('L0 주문 대상 갱신 완료. 현재시각: ', now)
        Dec_tickers_today.to_csv('Dec_tickers_today.csv', index = True) 
        g1.to_csv('g1.csv', index = True)
        g2.to_csv('g2.csv', index = True)
        g3.to_csv('g3.csv', index = True)

        post_message(myToken, '#making-money', 'Dec_tickers_today 갱신완료.') # Slack으로 갱신완료 알림.
        time.sleep(720)    


# 총 보유자산(ValuedAssets)이 목표수익(TargetProfit)에 도달하여, while문 탈출.
post_message(myToken, '#making-money', '목표수익 달성!') # Slack으로 목표달성 알림. 

# 목표도달시 윈도우 드레싱.
count = 0
tickers = pyupbit.get_tickers(fiat="KRW") 
for ticker in tickers:
    wait_orders = upbit.get_order(ticker)
    if wait_orders: 
        for k in range(len(wait_orders)):
            r1 = wait_orders[k]
            r2 = pd.Series(r1)
            uuid_for_cancel = r2['uuid']
            cancel_order = upbit.cancel_order(uuid_for_cancel)
            pprint.pprint(cancel_order)
            print(ticker, ": 미체결 주문을 취소했습니다.")
            count += 1
        print(count)
        print("\n")
    elif not wait_orders:
        print(".")
        pass
    time.sleep(0.1)
print("총 ",count,"개의 미체결 주문 취소했습니다.")

# 보유코인 현재가 +3% 매도
for ticker in tickers:
    balance = upbit.get_balance(ticker)
    if balance > 0:
        cur_price = pyupbit.get_current_price(ticker)
        SELL_price = smart_round(1.03*cur_price)
        upbit.sell_limit_order(ticker, SELL_price, balance)
    time.sleep(0.1)
print("모든 코인들, 현재가 +3% 매도주문 완료.")
post_message(myToken, '#making-money', '모든 코인들, 현재가 +3% 매도주문 완료.')
print('Main.py 종료')
