// ⭐ 백엔드를 배포한 후, 배포된 파이썬 서버 주소로 변경해야 합니다.
// 로컬 테스트 시에는 'http://127.0.0.1:5000' 유지
const API_BASE_URL = 'http://127.0.0.1:5000'; 

function showMode(modeId) {
    document.querySelectorAll('.container > div').forEach(div => div.classList.add('hidden'));
    document.getElementById(modeId).classList.remove('hidden');
}

function goHome() { 
    location.reload(); 
}

async function checkST() {
    const sn = document.getElementById('studentNum').value;
    if(!sn) return alert("학번을 입력해주세요.");

    try {
        const res = await fetch(`${API_BASE_URL}/api/checkin`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ student_id: sn })
        });
        const data = await res.json();

        if(data.status === 'success') {
            document.getElementById('res-name').innerText = data.name + " 학생";
            document.getElementById('res-detail').innerText = `${data.sheet}\n${data.period}교시 출석 완료`;
            showMode('sucsses');
        } else {
            alert(data.message);
        }
    } catch (error) {
        console.error("Error:", error);
        alert("서버와 통신할 수 없습니다.");
    }
}

// 교사 인증 및 리스트 로드
function checkAuth() {
    const pw = document.getElementById('pwInput').value;
    if(pw === "1234") {
        showMode('teacher-mode');
        // loadList(); // 이 기능은 파이썬 쪽에 구현이 필요합니다.
    } else { 
        alert("비밀번호가 틀렸습니다."); 
    }
}

function Di_L() { showMode('Di_list'); }
function Dd_L() { showMode('Dd_list'); }
function copyToClipboard() { showMode('teacher-add_list'); }