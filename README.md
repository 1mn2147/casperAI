# CasperAI - Voice AI Command Center

CasperAI는 동아리 관리에 특화된 음성 인식 기반 AI 소프트웨어입니다. 음성 명령을 통해 구글 캘린더에 일정을 관리하고, 회의 내용을 자동으로 요약하여 회의록을 작성해 줍니다.

## ✨ 주요 기능

* **음성 명령 인식 (STT)**: `Whisper-large-v3-turbo` 모델을 로컬 환경(GTX 950)에서 구동하여 빠르고 정확하게 사용자의 음성을 텍스트로 변환합니다.
* **자연어 처리 및 요약 (LLM)**: GitHub Copilot 지원 모델(OpenAI API 호환)을 활용해 사용자의 명령 의도를 파악하고, 긴 회의 내용을 핵심 안건과 실행 목표(Action Items)로 요약합니다.
* **구글 캘린더 연동**: 파악된 일정 명령을 바탕으로 사용자의 구글 캘린더에 자동으로 일정을 등록하고 조회합니다.
* **음성 피드백 (TTS)**: `gTTS`를 활용하여 처리 결과나 시스템의 대답을 음성으로 들려줍니다.
* **대시보드 UI**: Stitch MCP를 통해 생성된 모던한 웹 UI를 제공하여 일정과 회의록을 한눈에 관리할 수 있습니다.

## 🛠 기술 스택

* **Backend**: Python 3.10
* **AI Models**: 
  * STT: `openai-whisper` (large-v3-turbo)
  * TTS: `gTTS`
  * LLM: `openai` SDK (GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro 등 호환)
* **APIs**: Google Calendar API
* **Infrastructure**: Docker, Docker Compose, NVIDIA Container Toolkit (CUDA 11.8)
* **OS Target**: Arch Linux

## 📂 프로젝트 구조

```text
casperAI/
├── backend/
│   ├── requirements.txt      # 파이썬 의존성 패키지
│   ├── stt_tts.py            # Whisper STT 및 gTTS 파이프라인
│   ├── llm.py                # 명령 분석 및 회의록 요약 로직
│   └── calendar_api.py       # 구글 캘린더 연동 로직
├── frontend/
│   └── src/
│       └── screens/          # 다운로드된 웹 UI HTML 파일들
├── Dockerfile                # GPU 지원 백엔드/프론트엔드 컨테이너 빌드 파일
├── docker-compose.yml        # 서비스 오케스트레이션
└── README.md                 # 프로젝트 설명서
```

## 🚀 설치 및 실행 방법

### 1. 사전 요구 사항 (Prerequisites)
* **GPU**: NVIDIA GPU (GTX 950 이상 권장, NVIDIA Driver 및 Docker GPU Runtime 설치 필요)
* **API Key**: GitHub Copilot 지원 모델 또는 OpenAI 호환 API Key
* **Google Cloud**: 구글 캘린더 API가 활성화된 `credentials.json` 파일

### 2. 환경 설정
1. 구글 클라우드 콘솔에서 발급받은 데스크톱 앱용 `credentials.json` 파일을 `backend/` 디렉터리 안에 위치시킵니다.
2. API 키를 환경 변수로 설정합니다.
   ```bash
   export API_KEY="your_api_key_here"
   ```
3. 로컬 HTTP OAuth 개발 플로우를 위해 아래 환경 변수를 설정합니다.
   ```bash
   export OAUTHLIB_INSECURE_TRANSPORT=1
   ```

### 3. Docker로 실행하기 (권장)
NVIDIA 컨테이너 툴킷이 설치된 Arch Linux 환경에서 아래 명령어를 실행합니다.

```bash
cd casperAI
docker-compose up --build
```
*(참고: 초기 구동 시 `whisper-large-v3-turbo` 모델 파일이 다운로드 되므로 시간이 다소 소요될 수 있습니다.)*

### 4. Google Calendar 연결 방법
`/calendar` 페이지에서 수동 OAuth 연결 플로우를 사용합니다.

1. 브라우저에서 `/calendar` 페이지로 이동합니다.
2. `Connect` 버튼을 눌러 Google 인증 URL을 생성합니다.
3. 새 탭에서 열린 Google 로그인 페이지에서 인증을 완료합니다.
4. 마지막에 이동한 주소창의 전체 URL(`http://localhost/?code=...`)을 복사합니다.
5. 다시 `/calendar` 페이지로 돌아와 URL을 붙여넣고 `Finish Connection`을 누릅니다.
6. 연결이 완료되면 같은 페이지에서 일정 조회와 `Create New Event` 기능을 사용할 수 있습니다.

주의:
- `backend/credentials.json`이 없으면 연결이 시작되지 않습니다.
- `OAUTHLIB_INSECURE_TRANSPORT=1`은 로컬 개발용 설정입니다. 운영 환경에서는 HTTPS 기반 OAuth로 바꿔야 합니다.

### 5. 로컬 환경에서 직접 실행하기 (Docker 미사용 시)
```bash
cd casperAI/backend
python -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
# GTX 950(Maxwell 아키텍처) 등 구형 GPU를 위한 PyTorch(CUDA 11.8) 설치
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118

# 로컬 HTTP OAuth 개발 허용
export OAUTHLIB_INSECURE_TRANSPORT=1

# 모듈 테스트 (테스트 스크립트 작성 후)
python your_test_script.py
```
