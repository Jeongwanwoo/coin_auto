# [Title] 가상화폐 변동성 이용 전략 기반 자동매매 시스템
--------

## [environment]

* Python3.9, Slack, parsec
* python library : pyupbit, requests, pandas, time, datetime

## [Run]
1. Main.py, functions.py, get_ValuedAssets.py 본인 API키 입력
<img width="80%" src="https://user-images.githubusercontent.com/85176433/120662146-db30b000-c4c3-11eb-8123-16af6ff84615.PNG"/>

* 업비트 홈페이지에서 키발급 



2. functions.py 파일에서 한 코인당 투자금액인 UNIT 설정

3. Main.py 파일에서 윈도우 드레싱 목표금액 설정

4. Main.py 파일에서 Slack 으로 메시지를 받기위한 Slack 토큰 입력(목표금액달성 및 03:00시 마다 있는 갱신 완료 알람, 필요시 이용)
<img width="80%" src="https://user-images.githubusercontent.com/85176433/120662694-509c8080-c4c4-11eb-8519-8a459b77db13.PNG"/>

* Slack홈페이지에서 토큰발급



5. Main.py 에서 실행  

## [Result]

#### 실행 화면
<img width="80%" src="https://user-images.githubusercontent.com/85176433/120659853-b9362e00-c4c1-11eb-9797-caa9602e0ae5.gif"/>

