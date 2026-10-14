# KRISS PPT Skill — 1.1.0

HTML을 유일한 source of truth로 삼아 최종 DOM geometry와 computed style을 편집 가능한 native PPTX로 변환합니다. PPTX 단계의 재디자인, 글꼴 대체, 임의 위치·폭 보정, 의미 있는 콘텐츠의 이미지 평탄화를 허용하지 않습니다.

**정식 배포판(1.1.0)**입니다. 관리자가 외부 검증 완료를 확인한 `1.1.0-rc3+ophthagen.1` 기능을 정식 버전으로 승격하였습니다. 단, 전체 KRISS 레퍼런스 패턴의 native 변환 또는 모든 PowerPoint 실행 환경을 일괄 인증했다는 의미는 아닙니다. 디자인 승인과 변환기 인증을 구분합니다. S11·S12의 세로쓰기 등 알려진 미지원 표현은 원본을 보존한 채 명시적으로 차단합니다. 패턴 이름에 Approved가 있어도 export 인증을 뜻하지 않습니다. `references/pattern-support.json` 및 `references/release-status.md`에서 실제 검증 범위를 확인하십시오. 개별 발표자료도 모든 gate를 통과해야 완료로 취급합니다.

## 설치와 사전 점검

아래 검증용 설치 조합에는 Python 3.13을 사용합니다. 이번 실행에서 확인한 버전은 Python 3.13.5/Linux입니다. 소스의 최소 문법 수준은 Python 3.10이지만, 다른 Python 버전의 의존성 조합은 검증하지 않았습니다. Windows/macOS 및 Microsoft PowerPoint 실제 앱은 검증하지 않았습니다.

먼저 `kriss-ppt/` 디렉터리로 이동합니다. 압축 해제 직후 다음 무결성 검사를 실행하십시오. 이 검사는 외부 Python 패키지가 필요하지 않습니다. 저장소의 용량 제한에 맞춰 무손실 압축한 `references/reference.html.gz`로부터 원본 `reference.html`을 자동 복원하고 SHA-256을 검증합니다. 복원된 HTML은 원본과 바이트 단위로 동일합니다.

```bash
PYTHONDONTWRITEBYTECODE=1 python scripts/verify_installation.py --strict
```

일반 사용 후에는 `--strict` 없이 실행하면 `.venv`, `__pycache__` 등 실행 환경 파일을 제외하고 설치 파일을 확인합니다. 설치 manifest는 전자서명이 아니며, 파일과 manifest를 함께 바꾸는 공격을 인증하는 수단이 아닙니다.

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt -c constraints-tested.txt
python -m playwright install chromium
```

Linux에서 필요한 시스템 라이브러리까지 설치하려면 관리 정책에 따라 `python -m playwright install --with-deps chromium`을 사용합니다. 전체 QA에는 LibreOffice(`libreoffice` 또는 `soffice`), Poppler(`pdftoppm`), Fontconfig(`fc-match`)가 PATH에 있어야 합니다. Python API만으로 생성하는 경로에는 Node.js가 필요하지 않지만 `.mjs` 보조 도구에는 필요합니다.

시스템 Chromium을 사용하려면 `CHROMIUM_PATH` 환경 변수 또는 `--chromium /path/to/chromium`을 지정합니다. 스킬은 환경 변수 → 시스템 Chromium → Playwright 관리 브라우저 순으로 탐색합니다. 브라우저 버전은 evidence에 기록됩니다.

```bash
python scripts/check_environment.py --font "Noto Sans KR" --font "JetBrains Mono" --json environment.json
```

실제로 선택한 레퍼런스가 요구하는 모든 글꼴을 별도 설치해야 합니다. 위 두 family 외의 글꼴도 입력에 따라 추가합니다. 글꼴 파일은 배포하지 않으며 final HTML에도 내장하지 않습니다. family 확인은 개별 글리프 fallback이 없다는 증명이 아닙니다. `constraints-tested.txt`는 관측한 직접 의존성 조합이며 완전한 lockfile이 아닙니다. 네트워크 신규 설치의 재현성은 이번 환경에서 확인하지 못했습니다.

## 원본 이미지와 variation

표준 variation도 `reference.html`의 원본 배경 JPEG를 그대로 사용합니다. 제목 장식과 하단 띠를 CSS로 다시 그리지 않습니다. 이전 H02–H06의 배경 제거 규칙과 V10의 전면 대체 배경은 HTML 작성 단계에서 수정했습니다. V10의 어두운 강조는 본문 패널 안에만 적용합니다. 자세한 규칙은 `references/original-artwork-contract.md`를 참조하십시오.

알려진 구형 HTML을 명시적으로 복구하려면 `python scripts/sync_reference_chrome.py old.html --output restored.html`을 실행하고 HTML을 검토한 뒤 빌드합니다. 빌드는 입력의 잘못된 배경을 자동으로 바꾸지 않고 차단합니다.

## 실행

```bash
python scripts/validate_html.py presentation.html
python scripts/build_release.py presentation.html presentation.pptx
```

입력 HTML은 보존하고, 같은 위치에 `presentation.final.html`, 지정 위치에 PPTX와 `.evidence/`를 만듭니다. 배포할 HTML은 `.final.html`입니다. 허용된 로컬 이미지·CSS·일반 스크립트는 원래 바이트를 내장하여 상대경로의 해석 차이를 없앱니다. 이미지를 다시 raster화하지 않으며, 로컬 자원을 읽기 위해 same-origin 정책을 해제하지 않습니다. 입력 JavaScript를 실행하므로 신뢰할 수 있는 HTML에만 사용하십시오. 컨테이너 실행용 Chromium 인자에는 `--no-sandbox`가 포함되므로, 격리되지 않은 호스트에서 미신뢰 입력을 실행하지 마십시오. 로컬 파일의 입력 디렉터리 이탈, 누락 파일, 로컬 글꼴 내장, 미해결 `srcset`/모듈 경로는 차단됩니다. 외부 자원은 고정되지 않을 수 있으므로 재열기 검사를 통과해야 하며, 재현 가능한 빌드에는 로컬 자원을 권장합니다.

외부 네트워크를 차단한 검증은 `KRISS_OFFLINE=1`로 실행합니다. 입력이 외부 stylesheet·image 등을 필요로 하면 정상 통과를 기대하지 마십시오.

## 판정과 증거

`STATIC → HTML → NATIVE → PARITY → (선택적 REGRESSION)`을 모두 통과한 빌드만 `RELEASED`/exit 0입니다. `BLOCKED`는 검증 실패, `BUILD_ERROR`는 빌드 미완료이며 둘 다 exit 1입니다. 이 상태의 PPTX는 진단용입니다. 반복 빌드가 초기에 실패하면 과거 PPTX 파일은 남을 수 있으나, 이전 성공 manifest는 즉시 무효화됩니다. 파일 존재나 생성 시각만으로 배포 여부를 판단하지 마십시오.

객체 목록은 exporter 필터 이전의 DOM에서 독립적으로 수집합니다. 의미 있는 객체는 native 대응 객체가 있어야 하며, 작아서 전체 화면 픽셀 차이가 적어도 누락을 허용하지 않습니다. SVG 기본 도형 외의 미지원 구조, 미해결 overflow, 중복 ID, 비어 있는 speaker notes, 리소스 로딩 오류는 차단됩니다.

일반 HTML 활성화와 export는 같은 layout settle API를 사용합니다. 최종 HTML을 별도 페이지에서 다시 열어 일반적인 `.active` 전환으로 geometry·computed style·렌더를 비교합니다. screenshot SHA 일치 여부는 별도 기록하며, 승인에는 기존 global/local 수치 기준을 그대로 사용합니다. 단순 anti-aliasing 차이를 이유로 layout을 이동하거나 비교 허용치를 높이지 않습니다.

Evidence에는 입력·final HTML·모델·PPTX·이미지 자원 hash, 도구 버전, 객체 대응, native 검사, HTML 재열기, LibreOffice 렌더 비교가 포함됩니다. 이것은 재현성/변조 감지를 위한 연결 정보이지 공격자가 모든 파일과 hash를 재작성하는 상황에 대한 전자서명은 아닙니다.

## 구조와 버전관리

`SKILL.md`, `references/`, `scripts/`, 의존성·라이선스 문서와 무결성 manifest만 설치 배포본에 포함합니다. 대용량 canonical HTML은 Git 전송상 `reference.html.gz`로 보관하며, 설치 검증 시 무손실 복원됩니다. 저장소에도 이 설치본만 반영합니다. `.agent`, 개발용 테스트·CI, 시험 입력, 발표자료, 비교 이미지, 실행 결과, 패치 ZIP, 과거 작업 기록과 글꼴 파일은 제외합니다. 실제 사용 중 실행하는 HTML/native/parity 검사 및 설치 무결성 검사는 스킬 기능이므로 유지합니다. 개발 시험·검증 증거는 설치본 밖에서 관리하며 설치에 필요하지 않습니다.

`VERSION`이 실행 버전의 유일한 기준입니다. exporter, build의 실패 기록 및 환경 점검은 이 파일을 읽습니다. 파일 변경 시 `PACKAGE-MANIFEST.json`도 갱신해야 하며, 버전·manifest 불일치를 무시하지 않습니다.

대상 저장소: `celllamb/kriss-skill`. 설치 디렉터리는 `kriss-ppt/`로 추가하며 다른 스킬이나 저장소 루트 문서를 덮어쓰지 않습니다.

## 정식 릴리스에 포함된 hyperlink 기능

This installation includes native external text hyperlink capture, complete
source-text/link coverage and native URL validation. Canonical and approved
reference click navigation now ignores links and interactive controls. Layout,
image assets and parity thresholds are unchanged. Relative/internal links,
nontext hyperlinks and generated link content remain explicitly unsupported.
See `references/hyperlink-contract.md`.

This stable distribution includes the earlier rc3-based fixes. Historical
per-pattern reports retain their original scope; the production build must still
pass all required QA gates.


## Source-bound speaker notes

Plain-text `data-notes` is captured from the settled DOM before export filtering.
The native notes body must match exactly, including Unicode, paragraphs, blank
lines and whitespace. The delivered HTML reread must reproduce the same notes.
Missing, changed or unreadable notes block approval even when slide pixels match.
See `references/speaker-notes-contract.md`. Rebuild older evidence without this
contract rather than treating a missing notes record as a pass. The release includes the earlier hyperlink fixes; every completed deck
still requires its own HTML/native/parity validation.
