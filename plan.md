### 목표: 캘린더 관리와 회의록 관리를 해주는 동아리 관리 특화형 AI 활용 소프트웨어 개발

기능
- STT 기술을 활용한 회의록 정리 기능
- 구글 캘린더와의 연동으로 일정 관리 기능
- STT, TTS를 활용한 대화를 통한 명령 지시 및 대답
- stt는 whisper로 직접 사용하고 llm은 gemini API 키 사용
- Whisper-large-v3-turbo 사용

환경
- arch linux 위에 도커로 올릴 예정
- i5 4세대/ gtx 950

웹 UI는 stitch mcp를 참고해 제작할 것. 다음은 stitch의 프롬프트이다.
## Stitch Instructions

Get the images and code for the following Stitch project's screens:

## Project
Title: Voice AI Command Center
ID: 9747960646839204508

## Screens:
1. Calendar Management (Lightened)
    ID: d4931d0bf5cf4d298b483e069796dc46

2. Meeting Minutes (Lightened)
    ID: 5025c8dfb7e34c09bc460f039a5b6823

3. Voice AI Command Center (Lightened)
    ID: d66200910607404c9e0aa78e39ee5157

4. Dashboard Overview (Lightened)
    ID: f8b34422d11e42dba6d070d3e10c894e

Use a utility like `curl -L` to download the hosted URLs.