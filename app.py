import os
import gspread
from datetime import datetime, timedelta, timezone
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# GitHub Pages에서 오는 API 요청을 허용하기 위해 CORS 설정 적용
CORS(app) 

# --- 1. 구글 인증 및 시트 연결 ---
# 서버 환경에서는 Colab 인증 대신 '서비스 계정(Service Account)'을 사용해야 합니다.
# 구글 클라우드 콘솔에서 서비스 계정을 만들고 발급받은 maesan-night-selfstudy-701887cb22e8.json 파일을 같은 폴더에 넣으세요.
try:
    gc = gspread.service_account(filename='maesan-night-selfstudy-701887cb22e8.json')
    sh = gc.open('야간자율학습 명렬표')
    print("✅ 구글 시트 연결 성공")
except Exception as e:
    print(f"❌ 구글 시트 연결 실패. maesan-night-selfstudy-701887cb22e8.json 파일이 있는지, 권한이 있는지 확인하세요.\n에러: {e}")

# --- 2. 데이터 구조 설정 ---
student_db = {}

def load_master_data():
    global student_db
    student_db.clear()
    target_sheets = ['월~목 자습(2~6반)', '월~목 자습(요셉홀,지리실)', '금요자습', '토요자습']

    for s_name in target_sheets:
        try:
            ws = sh.worksheet(s_name)
            data = ws.get_all_values()
            for i, row in enumerate(data[1:], start=2):
                if len(row) >= 2 and row[1]: # 학번 존재 확인
                    sid = row[1].strip()
                    student_info = {
                        "name": row[2].strip() if len(row) > 2 else "이름없음",
                        "sheet": s_name,
                        "row": i
                    }

                    if sid not in student_db:
                        student_db[sid] = []

                    student_db[sid].append(student_info)
            print(f"✅ '{s_name}' 로드 완료")
        except Exception as e:
            print(f"⚠️ '{s_name}' 시트를 찾을 수 없거나 에러가 발생했습니다: {e}")

# 서버 시작 시 마스터 데이터 로드
load_master_data()

# --- 3. 편의 기능 ---
def get_now_info():
    now = datetime.now(timezone(timedelta(hours=9))) # KST 기준
    days = ['월', '화', '수', '목', '금', '토', '일']
    return {
        "time": now.strftime("%H:%M"),
        "day": days[now.weekday()],
        "w_idx": now.weekday()
    }

# --- 4. API 엔드포인트 ---
# (이제 HTML 렌더링은 프론트엔드에서 하므로 루트('/') 라우트는 제거하거나 상태 확인용으로 둡니다)
@app.route('/')
def health_check():
    return jsonify({"status": "running", "message": "Attendance API is active"})

@app.route('/api/checkin', methods=['POST'])
def checkin():
    sid = str(request.json.get('student_id', '')).strip()
    info = get_now_info()

    # 1. 요일에 따른 허용 시트 필터링
    allowed_sheets = []
    if info['day'] in ['월', '화', '수', '목']:
        allowed_sheets = ['월~목 자습(2~6반)', '월~목 자습(요셉홀,지리실)']
    elif info['day'] == '금':
        allowed_sheets = ['금요자습']
    elif info['day'] == '토':
        allowed_sheets = ['토요자습']
    else:
        return jsonify({"status": "fail", "message": "일요일은 운영하지 않습니다."})

    # 2. 교시 판정
    period, col = 0, 0
    if "00:10" <= info['time'] <= "19:30":
        period, col = 1, 4 # D열
    elif "20:40" <= info['time'] <= "21:00":
        period, col = 2, 5 # E열
    else:
        return jsonify({"status": "fail", "message": f"지금({info['time']})은 출석 시간이 아닙니다."})

    # 3. 명단 대조 및 기록
    if sid in student_db:
        students = student_db[sid]

        # 오늘 허용된 시트에 있는 학생 찾기
        st = None
        for s in students:
            if s['sheet'] in allowed_sheets:
                st = s
                break
                
        if st:
            # 실제 시트 업데이트
            ws = sh.worksheet(st['sheet'])
            ws.update_cell(st['row'], col, 1)
            # 색상 변경
            ws.format(gspread.utils.rowcol_to_a1(st['row'], col), {
                "backgroundColor": {"red": 0.8, "green": 1.0, "blue": 0.8}
            })
            return jsonify({"status": "success", "name": st['name'], "sheet": st['sheet'], "period": period})
        else:
            return jsonify({"status": "fail", "message": "오늘은 출석 대상 시트에 배정되지 않았습니다."})
    else:
        return jsonify({"status": "fail", "message": "명단에 없는 학번입니다."})

if __name__ == '__main__':
    # 개발 환경에서는 로컬 포트 5000에서 실행 (배포 시 환경변수로 포트 설정 권장)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)