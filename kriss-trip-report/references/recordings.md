# 녹음 및 전사본 처리

회의 녹음, 오디오 파일, 녹음 ZIP이 원자료로 제공되었을 때 이 문서를 사용한다.

## 기본 원칙

녹음은 보조 원자료이지만, 보고서의 사실관계는 신뢰 가능한 전사본 또는 문서형 회의자료에서 가져와야 한다. 전사되지 않은 오디오에서 기술 결론을 직접 작성하지 않는다.

## 입력 가능 자료

이 스킬은 다음 자료를 목록화하고 준비할 수 있다.

- 오디오 파일: `.m4a`, `.mp3`, `.wav`, `.aac`, `.flac`, `.ogg`
- 오디오 파일이 들어 있는 녹음 ZIP
- 전사본 파일: `.txt`, `.md`, `.srt`, `.vtt`
- 오디오와 전사본이 함께 들어 있는 ZIP

## 준비 절차

녹음 또는 녹음 ZIP이 있으면 `scripts/prepare_recordings.py`를 실행한다.

목록만 만들 때:

```powershell
python scripts\prepare_recordings.py recordings.zip --output-dir run\recordings
```

파일을 작업 폴더로 추출/복사할 때:

```powershell
python scripts\prepare_recordings.py recordings.zip --output-dir run\recordings --extract
```

출력:

- `recording-index.md`: 사람이 읽는 녹음/전사본 표와 작성 주의사항
- `recording-manifest.json`: 구조화된 녹음/전사본 manifest
- `audio/`: `--extract` 사용 시 추출/복사된 녹음
- `transcripts/`: `--extract` 사용 시 추출/복사된 전사본

## 전사본 매칭

준비 스크립트는 파일명 stem이 같거나 유사한 녹음과 전사본을 연결한다.

권장 파일명:

```text
meeting-day1-session1.m4a
meeting-day1-session1.txt
meeting-day1-session2.m4a
meeting-day1-session2.srt
```

녹음에 대응 전사본이 없으면, 전사 전까지 보고서 사실관계에 사용할 수 없다고 index에 표시된다.

## 전사 범위

전사 변환은 이 스킬 밖에서 수행한다. 오디오 전사가 필요하면 별도 전사 스킬 또는 승인된 speech-to-text 도구를 사용하고, 생성된 전사본 파일을 이 워크플로에 다시 제공한다.

외부 전사 후에는 오디오 작업 폴더와 전사본 폴더를 대상으로 `prepare_recordings.py`를 다시 실행해 manifest가 녹음과 전사본을 연결하게 한다.

```powershell
python scripts\prepare_recordings.py run\recordings\audio run\recordings\transcripts --output-dir run\recordings-linked
```

보고서 원자료로는 연결된 전사본만 사용한다.

## 전사본을 사용한 작성

전사본이 있을 때:

- 날짜, 세션 번호, 슬라이드 제목, 발화자, 명시적 아젠다 표현을 기준으로 전사본 발췌를 아젠다 항목에 매핑한다.
- 전사본은 공식 아젠다, 회의록, 발표자료를 보완하는 용도로 쓴다.
- 전사본이 문서 원자료와 충돌하면 공식 아젠다/회의록/발표자료를 우선한다. 단, 전사본이 이후 결정이나 현장 수정사항을 명확히 기록한 경우는 예외로 검토한다.
- 보고서에 긴 전사본 인용을 넣지 않는다. 한국어 개조식으로 요약한다.
- 최종 본문에 `녹취록 확인 필요` 같은 불확실성 표시를 넣지 않는다.

전사본이 없을 때:

- 녹음은 dossier/inventory에만 포함한다.
- 녹음을 보고서 본문의 사실 근거로 사용하지 않는다.
- 사용자에게 전사본을 요청하거나 별도 전사 도구/스킬을 사용한 뒤, 생성된 전사본을 연결하기 위해 `prepare_recordings.py`를 다시 실행한다.

## 최종 보고서 처리

`수집자료`에는 녹음이 실제로 제공되었거나 사용된 회의/보고서 원자료인 경우에만 요약해 넣는다. `회의 녹음자료 및 전사본`처럼 간결한 범주명으로 충분하다. 요청이 없으면 각 오디오 파일명을 나열하지 않는다.

녹음은 `출입국 입증 자료`가 아니다. 출입국 입증 자료는 항공권, 보딩패스, 출입국 사실증명 등 여행 증빙으로 제한한다.
