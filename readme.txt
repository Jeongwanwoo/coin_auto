1. Topic 
가상화폐 변동성을 이용한 자동매매 및 윈도우 드레싱 알고리즘

2. Data 
업비트 API 활용

3. Start 
Main.py, functions.py, get_ValuedAssets.py 본인 API키 입력 -> 
functions.py 파일에서 한 코인당 투자금액인 UNIT 설정 ->
Main.py 파일에서 윈도우 드레싱 목표금액 설정 ->
Main.py 파일에서 Slack 으로 메시지를 받기위한 Slack 토큰 입력 ->
Main.py 에서 실행 

4. Result 
목표금액에 달성할 때 까지 117개의 코인들을 감시하면 매도, 매수를 진행한다.  