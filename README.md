# Skill Collection

Agent에서 사용할 수 있는 skill 모음입니다. 이 저장소의 README는 스킬을 처음 사용하는 사람이 각 스킬의 목적을 이해하고, 필요한 스킬을 골라 바로 사용할 수 있도록 돕는 안내서입니다.

Agent들은 여러가지 있겠지만 OpenAI의 코딩 에이전트인 Codex를 기본으로 해서 설명합니다. Codex가 아니라 Claude웹, Claude Code, Antigravity나 Openclaw등 다른 곳에서도 사용할 수 있습니다. 

대부분의 사용자가 MS Windows 환경에서 일하고 CLI나 PowerShell에 익숙하지 않을 수 있다고 가정합니다. 따라서 일반 사용자는 아래에 있는 명령어를 직접 실행할 필요가 없습니다. 파일이나 폴더를 Codex에 제공한 뒤, 예시 문장처럼 작업을 요청하면 됩니다.

`kriss-`로 시작하는 스킬은 KRISS 업무에 맞춘 전용 스킬입니다. 그 외 스킬은 특정 기관에 한정되지 않는 범용 스킬입니다.
범용 스킬은 그 자체로도 사용할 수 있고, KRISS 전용 스킬을 사용할 때도 직간접적으로 도움이 될 수 있습니다. 예를 들어 `kriss-trip-report`로 HWPX 보고서를 만들 때 `edit-hwpx-docs`가 검증이나 간단한 HWPX 수정에 도움이 될 수 있으므로, 특별한 이유가 없다면 범용 스킬도 함께 내려받아 두는 것을 권장합니다.
앞으로 KRISS 업무와 관련된 스킬이 추가되면 `kriss-...` 형식의 이름을 사용할 예정입니다.

## Skill이란?

Skill은 Codex가 특정 작업을 더 안정적으로 수행하도록 돕는 작업 지침 묶음입니다. 보통 다음 파일들로 구성됩니다.

| 구성 | 설명 |
| --- | --- |
| `SKILL.md` | 스킬의 목적, 사용 조건, 작업 순서, 주의사항 |
| `references/` | 작업 전에 참고해야 하는 배경 문서나 규칙 |
| `scripts/` | 반복 작업을 자동화하는 보조 도구 |
| `assets/` | 템플릿, 예시 파일 등 스킬이 사용하는 자료 |
| `agents/openai.yaml` | Codex UI에서 보일 스킬 이름과 기본 호출 문구 |

사용자는 보통 `SKILL.md`나 `scripts/`를 직접 열어볼 필요가 없습니다. Codex에게 `Use $스킬이름 ...` 형식으로 요청하면 Codex가 해당 스킬의 지침을 읽고 필요한 작업을 진행합니다.

## 어떤 스킬을 써야 하나요?

| 스킬 | 구분 | 이런 때 사용하세요 |
| --- | --- | --- |
| `edit-hwpx-docs` | 범용 | 한컴 HWPX 문서에서 텍스트를 뽑거나, 간단한 문구를 바꾸거나, HWP2018에서 민감한 문단 레이아웃 참조까지 포함해 문서 패키지 구조를 검증해야 할 때 |
| `kriss-trip-report` | KRISS 전용 | KRISS 국외출장보고서를 회의 자료, 발표자료, 일정표, 탑승권, 출입국 증빙, 사진, 전사본 등을 바탕으로 작성하거나, 작성된 보고서를 원자료와 대조 감사하고 HWPX 최종본을 검증해야 할 때 |
| `official-docs-setup` | 범용 | 설치 명령, 실행 명령, SDK 설정, 서버 실행 방법 등을 작성하기 전에 공식 문서를 먼저 확인하게 하고 싶을 때 |

## 설치 방법

### Windows 사용자

먼저 이 저장소의 파일을 내 PC에 준비한 뒤, 압축파일 형태로 codex에게 스킬추가를 요청하거나 필요한 스킬 폴더를 Codex의 `skills` 폴더로 복사합니다.

#### 1. 저장소를 내 PC에 받기

GitHub Desktop으로 받는 방법:

GitHub Desktop은 명령어를 몰라도 저장소를 내려받고 업데이트를 관리할 수 있는 프로그램입니다. 스킬을 계속 업데이트해서 쓸 예정이라면 ZIP 다운로드보다 GitHub Desktop이 더 편할 수 있습니다.

1. [GitHub Desktop 다운로드 페이지](https://desktop.github.com/download/)에서 Windows용 GitHub Desktop을 설치합니다.
2. GitHub Desktop을 실행하고 GitHub 계정으로 로그인합니다.
3. 웹브라우저에서 이 저장소 페이지를 엽니다.
4. 초록색 `Code` 버튼을 누른 뒤 `Open with GitHub Desktop`을 선택합니다.
5. 저장 위치를 고르고 `Clone`을 누릅니다.
6. 내려받은 폴더 안에 `edit-hwpx-docs`, `kriss-trip-report`, `official-docs-setup` 폴더가 있는지 확인합니다.

나중에 저장소가 업데이트되면 GitHub Desktop에서 이 저장소를 열고 최신 변경사항을 가져오면 됩니다. 자세한 절차는 GitHub 공식 문서의 [GitHub Desktop으로 저장소 복제하기](https://docs.github.com/en/desktop/adding-and-cloning-repositories/cloning-a-repository-from-github-to-github-desktop?platform=windows)를 참고하세요.

GitHub 웹사이트에서 ZIP으로 받는 방법:

이 방법은 가장 단순하지만, 나중에 저장소가 업데이트되면 ZIP을 다시 내려받아야 합니다.

1. 저장소 페이지를 엽니다.
2. 초록색 `Code` 버튼을 누릅니다.
3. `Download ZIP`을 선택합니다. (이 상태에서 받은 압축파일을 바로 codex에게 스킬 설치를 요청해도 됩니다.)
4. 내려받은 ZIP 파일을 마우스 오른쪽 버튼으로 클릭한 뒤 `압축 풀기`를 선택합니다.
5. 압축을 푼 폴더 안에 `edit-hwpx-docs`, `kriss-trip-report`, `official-docs-setup` 폴더가 있는지 확인합니다.

이미 누군가에게 폴더를 전달받은 경우:

1. 전달받은 폴더를 엽니다.
2. 그 안에 `edit-hwpx-docs`, `kriss-trip-report`, `official-docs-setup` 같은 스킬 폴더가 있는지 확인합니다.
3. ZIP 파일로 전달받았다면 먼저 압축을 풉니다.

#### 2. Codex skills 폴더 열기

1. Windows 파일 탐색기를 엽니다.
2. 주소창에 `%USERPROFILE%`를 입력해 내 사용자 폴더로 이동합니다.
3. `.codex` 폴더를 엽니다. 없으면 새 폴더를 만들고 이름을 `.codex`로 지정합니다.
4. `.codex` 폴더 안에서 `skills` 폴더를 엽니다. 없으면 새로 만듭니다.

#### 3. 필요한 스킬 폴더 복사하기

1. 압축을 푼 저장소 폴더로 돌아갑니다.
2. 필요한 스킬 폴더를 선택합니다.
3. 선택한 폴더를 `%USERPROFILE%\.codex\skills` 폴더 안으로 복사합니다.

최종 위치는 보통 `C:\Users\사용자이름\.codex\skills\스킬이름` 형태가 됩니다.

일부 스킬만 설치하려면 필요한 폴더만 복사하면 됩니다.

예를 들어 HWPX 문서 편집만 필요하면 `edit-hwpx-docs` 폴더만 복사하면 됩니다. KRISS 국외출장보고서 작성이 필요하면 `kriss-trip-report` 폴더를 복사합니다.

설치가 어렵다면 Codex에게 다음처럼 요청해도 됩니다.

```text
이 저장소의 edit-hwpx-docs 스킬을 내 Codex skills 폴더에 설치해줘.
```

### 고급 사용자 또는 관리자

Git과 PowerShell에 익숙하다면 아래 명령을 사용할 수 있습니다.

```powershell
git clone https://github.com/celllamb/kriss-skill.git
cd kriss-skill
```

```powershell
$skills = "$env:USERPROFILE\.codex\skills"
New-Item -ItemType Directory -Force -Path $skills
Copy-Item -Recurse -Force .\edit-hwpx-docs, .\kriss-trip-report, .\official-docs-setup $skills
```

```powershell
Copy-Item -Recurse -Force .\edit-hwpx-docs "$env:USERPROFILE\.codex\skills"
```

## 기본 사용법

기본적인 사용법은 특정 스킬을 명시할 필요 없이 요청하는 것입니다. 
최신의 모델들은 대부분은 Tool Calling 혹은 Function Calling이라는 기능이 있어서 사용자의 요청에 따라서 특정 스킬을 써야할 때를 판단해서 알아서 사용합니다.

```text
CCQM 폴더에 있는 파일에 기반해서 출장 보고서를 작성해줘.
```

모델의 판단에 의해서 자동으로 스킬을 사용하게 하는 것이기 때문에 때때로 스킬을 사용하지 않는 경우도 있을 수 있는데 이 경우 스킬을 명시해서 요청하면 됩니다.

```text
kriss-trip-report 스킬을 사용해서 제공한 출장 자료를 바탕으로 출장 보고서를 작성해줘.
```

좀 더 직접적으로는 `Use $스킬이름` 뒤에 원하는 작업을 요청하는 방법도 있습니다.

```text
Use $edit-hwpx-docs. 이 HWPX 파일의 본문을 추출하고 요약해줘.
Use $kriss-trip-report. 이 출장 자료 폴더를 바탕으로 국외출장보고서 초안을 만들어줘.
Use $official-docs-setup. 이 프로젝트 실행 방법을 공식 문서 기준으로 정리해줘.
```

## 스킬별 안내

### edit-hwpx-docs

한컴 HWPX 파일을 다루는 범용 스킬입니다. HWPX는 내부적으로 여러 XML 파일이 들어 있는 ZIP 패키지이기 때문에, 일반 텍스트 파일처럼 직접 편집하면 문서가 깨질 수 있습니다. 이 스킬은 HWPX 구조를 유지하면서 안전하게 읽고, 검증하고, 간단히 수정하는 데 초점을 둡니다. 최신 버전은 텍스트 치환 뒤 남을 수 있는 `charCnt`와 `hp:lineseg textpos` 같은 HWP2018 민감 레이아웃 참조도 검사하고 일부 자동 복구합니다.

주요 작업:

- HWPX 파일이 정상적인 패키지인지 검증
- 문서 본문 텍스트 추출
- 템플릿 안의 간단한 문구나 placeholder 치환
- 문서 끝에 문단 추가
- 문구를 줄인 뒤 남은 문단 길이/줄 배치 참조 오류 검사
- HWPX를 unpack한 뒤 XML을 수정하고 다시 pack

사용자 요청 예시:

```text
Use $edit-hwpx-docs. 이 HWPX 파일이 정상인지 확인해줘.
Use $edit-hwpx-docs. 이 HWPX 파일의 본문을 Word처럼 읽을 수 있는 텍스트로 뽑아줘.
Use $edit-hwpx-docs. 템플릿 안의 {{NAME}}을 "Kim"으로 바꾼 새 파일을 만들어줘.
```

아래 스크립트는 Codex나 고급 사용자가 자동화할 때 쓰는 예시입니다. 일반 사용자가 직접 실행할 필요는 없습니다.

```powershell
python .\edit-hwpx-docs\scripts\hwpx_tool.py validate .\document.hwpx
python .\edit-hwpx-docs\scripts\hwpx_tool.py extract .\document.hwpx --output .\document.txt
python .\edit-hwpx-docs\scripts\hwpx_tool.py replace .\template.hwpx .\output.hwpx --old "{{NAME}}" --new "Kim"
python .\edit-hwpx-docs\scripts\hwpx_tool.py append .\template.hwpx .\output.hwpx --text-file .\addition.txt
```

`validate`는 ZIP/XML 구조뿐 아니라 실제 문단 길이를 넘어서는 `hp:lineseg textpos` 값도 확인합니다. 이런 오류는 XML이 정상이어도 HWP2018에서 손상/변조 경고로 이어질 수 있습니다.

표, 이미지, 스타일, 머리말, 각주처럼 문서 구조가 복잡한 부분을 고쳐야 한다면 Codex에게 먼저 `references/hwpx-format.md`를 읽고 진행하라고 요청하는 것이 좋습니다. Hancom Office가 설치되어 있고 최종 전달본을 만드는 경우에는 실제 한컴 엔진으로 열기 가능성까지 확인하는 것이 안전합니다.

### kriss-trip-report

KRISS 국외출장보고서 작성과 원자료 대조 검토를 돕는 전용 스킬입니다. 관련 분야를 잘 모르는 사용자도 출장 자료 폴더를 제공하면 Codex가 자료 목록을 만들고, 보고서 유형을 판단하고, KRISS 양식에 맞춘 초안을 작성하도록 설계되어 있습니다.
현재 (CCQM과 같은) 회의, 학회, 파견연구의 3가지 유형으로 분류하며 2026년 CCQM 회의 자료로 회의 유형 출장보고서 테스트해서 확인했습니다. 
다른 유형도 작동하도록 설계되어 있지만 아직 실제 자료로 충분히 검증하지 못했습니다.

회의형 보고서처럼 study number, 기관별 발표자료, coordinator 자료, action item이 많이 섞이는 경우에는 별도 컨텍스트의 감사 에이전트가 보고서를 원자료와 다시 대조하도록 설계되어 있습니다. 감사 에이전트는 명백한 오류와 사용자 확인이 필요한 항목을 분리해 보고하고, 그 결과에 따라 보고서를 다시 수정합니다. 이 감사 프롬프트는 Codex뿐 아니라 Claude, Claude Code, Antigravity 같은 다른 에이전트에서도 새 대화에 복사해 사용할 수 있습니다.

최신 버전은 원자료-아젠다 매칭표와 source trace matrix를 더 중요하게 사용합니다. 실질적 발표자료나 기술 원자료는 공식 아젠다, 프로그램, action, 회의록, 증빙 범주, 사용자 확인 맥락 중 어디에 쓰이는지 먼저 연결하고, 최종 보고서 본문에는 `근거`, `자료상`, `발표자료 없음` 같은 작성 과정 문구를 남기지 않도록 합니다. 이미지가 들어간 HWPX는 한컴 HWP2018에서 실제로 열리는지까지 확인하는 절차가 강화되었습니다.

사용할 수 있는 자료 예시:

- 회의 안건, 회의록, 발표자료, 기관 소개자료
- 학회 프로그램, 초록, 포스터, 세션 노트
- 파견 연구 계획, 실험 노트, 일일 업무 기록
- 항공권, 탑승권, 출입국 사실증명
- 회의 사진, 출장 사진
- 녹음 파일과 전사본

중요한 점:

- 녹음 파일은 전사본이 있을 때만 보고서 근거로 사용합니다.
- 주민등록번호, 여권번호, 외국인등록번호 같은 개인정보는 스킬에서 마스킹하게 되어있지만 최종 문서에서 마스킹되어 있는지 확인해야 합니다.
- 탑승권과 출입국 증빙은 회의 자료가 아니라 출입국 증빙 자료로 분류합니다.
- 모르는 내용은 추측하지 않고, 자료에서 확인하거나 사용자에게 물어봐야 합니다.

사용자 요청 예시:

```text
Use $kriss-trip-report. 이 출장 자료 폴더를 검토해서 어떤 자료가 있는지 목록부터 만들어줘.
Use $kriss-trip-report. 발표자료와 회의 아젠다를 대조해서 원자료-아젠다 매칭표를 먼저 만들어줘.
Use $kriss-trip-report. 이 자료들로 KRISS 국외출장보고서 초안을 작성해줘.
Use $kriss-trip-report. 작성된 보고서를 원자료와 대조해서 study number와 내용이 맞는지 감사해줘.
Use $kriss-trip-report. 첨부한 탑승권과 출입국 증빙에서 개인정보가 보이는지 먼저 확인해줘.
```

아래 스크립트는 Codex나 고급 사용자가 자료 정리와 HWPX 생성을 자동화할 때 쓰는 예시입니다. 일반 사용자가 직접 실행할 필요는 없습니다.

```powershell
python .\kriss-trip-report\scripts\build_dossier.py .\source-materials --output-md .\work\dossier.md --output-json .\work\dossier.json
python .\kriss-trip-report\scripts\prepare_recordings.py .\recordings .\transcripts --output-dir .\work\recordings --output-md .\work\recordings.md --output-json .\work\recordings.json --extract
python .\kriss-trip-report\scripts\draft_hwpx_from_markdown.py .\work\draft.md .\work\report.hwpx --template .\kriss-trip-report\assets\kriss-overseas-trip-report-template.hwpx
python .\kriss-trip-report\scripts\validate_hwpx_images.py .\work\report.hwpx
```

PDF 발표자료나 증빙자료의 일부 페이지만 이미지로 넣어야 할 때 Codex가 사용할 수 있는 명령 예시:

```powershell
python .\kriss-trip-report\scripts\render_pdf_pages.py .\slides.pdf --pages 1,3,5-7 --output-dir .\work\images --prefix slides --dpi 200
```

최종 HWPX에 이미지가 들어간 경우 `validate_hwpx_images.py`를 실행해 이미지 참조와 HWP2018 민감 문단 레이아웃 참조가 깨지지 않았는지 확인합니다. 한컴오피스를 사용할 수 있다면 파일을 열고 다시 저장한 뒤 round-trip 비교도 수행하는 것이 좋습니다.

```powershell
python .\kriss-trip-report\scripts\compare_hwpx_packages.py .\before.hwpx .\after.hwpx
```

Windows에 Hancom Office 2018이 설치되어 있으면 비대화식 round-trip 검증을 사용할 수 있습니다. 처음 한 번 보안 모듈을 등록한 뒤, 생성본을 한컴 엔진으로 열고 별도 HWPX로 저장해 다시 열리는지 확인합니다.

```powershell
powershell -ExecutionPolicy Bypass -File .\kriss-trip-report\scripts\install_hwp_security_module.ps1 -Force
powershell -ExecutionPolicy Bypass -File .\kriss-trip-report\scripts\hwp2018_roundtrip.ps1 .\work\report.hwpx .\work\report.hwp2018-roundtrip.hwpx -Force
python .\kriss-trip-report\scripts\compare_hwpx_packages.py .\work\report.hwpx .\work\report.hwp2018-roundtrip.hwpx
```

`install_hwp_security_module.ps1`는 `assets/hwp-security-module` 안의 Hancom file-path checker module을 현재 사용자 레지스트리에 등록합니다. 이 절차는 자동화 중 뜨는 파일 접근 보안창을 피하기 위한 것이며, `SetMessageBoxMode`만으로는 충분하지 않습니다.

### official-docs-setup

설치, 실행, 설정 방법을 작성할 때 공식 문서를 먼저 확인하도록 하는 범용 스킬입니다. 소프트웨어 설치 명령은 버전, 운영체제, 패키지 관리자, GPU/CUDA 지원 여부에 따라 자주 바뀌므로 기억에 의존한 답변을 줄이는 데 유용합니다.

사용하면 좋은 상황:

- SDK, CLI, 서버, 프레임워크 설치 방법을 작성할 때
- Dockerfile, 실행 스크립트, 환경 변수 설정을 만들 때
- 모델 실행 명령이나 inference 서버 시작 방법을 정리할 때
- 공식 문서 기준으로 기존 README의 설치 안내를 검토할 때

사용자 요청 예시:

```text
Use $official-docs-setup. 이 프로그램 설치 방법을 공식 문서 기준으로 정리해줘.
Use $official-docs-setup. Windows 사용자가 따라할 수 있게 실행 방법을 써줘.
Use $official-docs-setup. 기존 README의 설치 명령이 최신 공식 문서와 맞는지 확인해줘.
```

Codex 외 다른 도구에 같은 원칙을 옮겨야 한다면 `official-docs-setup/references/portable-prompts.md`의 프롬프트 조각을 사용할 수 있습니다.

## 검증 방법

스킬이나 스크립트를 수정하는 사람은 가능한 범위에서 검증 명령을 실행합니다. 일반 사용자는 이 단계를 직접 수행하지 않아도 됩니다. Codex에게 “결과 파일을 검증해줘”라고 요청하면 됩니다.

```powershell
python .\edit-hwpx-docs\scripts\validate_skill.py .\edit-hwpx-docs
python .\edit-hwpx-docs\scripts\hwpx_tool.py validate .\some-output.hwpx
python .\kriss-trip-report\scripts\validate_hwpx_images.py .\some-report.hwpx
```

`edit-hwpx-docs`의 기본 도구는 Python 표준 라이브러리만 사용합니다. `hwpx_tool.py validate`와 `validate_hwpx_images.py`는 XML 파싱뿐 아니라 HWP2018에서 문제가 될 수 있는 `charCnt`, `hp:lineseg textpos` 불일치도 확인합니다.

`kriss-trip-report`는 PDF와 이미지 처리를 위해 `pypdf`, `Pillow`, `PyMuPDF` 같은 패키지가 필요할 수 있으며, Codex Desktop 번들 패키지를 먼저 찾고 없으면 자동 설치를 시도합니다. Hancom Office가 설치된 Windows 환경에서는 위의 HWP2018 round-trip 검증까지 수행하면 이미지 포함 최종본의 위험을 더 줄일 수 있습니다.

자동 설치를 막고 필요한 설치 명령만 확인하려면 다음 환경 변수를 설정합니다.

```powershell
$env:KRISS_TRIP_REPORT_NO_AUTO_INSTALL = "1"
```

## 개인정보와 민감자료 주의

출장 증빙, 탑승권, 출입국 사실증명, 회의 녹취, 전사본에는 개인정보와 민감한 업무 정보가 포함될 수 있습니다. 원본 자료와 생성 산출물은 공유 전에 검토하고, 보호 식별자가 포함된 파일은 저장소에 커밋하지 마세요.
