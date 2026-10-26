# KRISS PPT Skill — 1.2.0-rc3 (runtime-only package)

HTML을 유일한 source of truth로 삼아 최종 DOM geometry와 computed style을 편집 가능한 native PPTX로 변환합니다. PPTX 단계의 재디자인, 글꼴 대체, 임의 위치·폭 보정, 의미 있는 콘텐츠의 이미지 평탄화를 허용하지 않습니다.

**배포 후보(RC)입니다. 전체 KRISS 레퍼런스의 native 변환이 인증된 정식 릴리스가 아닙니다.** 디자인 승인과 변환기 인증을 구분합니다. S11·S12의 세로쓰기 등 알려진 미지원 표현은 원본을 보존한 채 명시적으로 차단합니다. 패턴 이름에 Approved가 있어도 export 인증을 뜻하지 않습니다. `references/pattern-support.json` 및 `references/release-status.md`에서 실제 검증 범위를 확인하십시오. 개별 발표자료도 모든 gate를 통과해야 완료로 취급합니다.

## 설치와 사전 점검

아래 검증용 설치 조합에는 Python 3.13을 사용합니다. 이번 실행에서 확인한 버전은 Python 3.13.5/Linux입니다. 소스의 최소 문법 수준은 Python 3.10이지만, 다른 Python 버전의 의존성 조합은 검증하지 않았습니다. Windows/macOS 및 Microsoft PowerPoint 실제 앱은 검증하지 않았습니다.

먼저 `kriss-ppt/` 디렉터리로 이동합니다. GitHub 체크아웃에서는 전송 제한을 피하기 위해 원본 마스터 PPTX가 4개 무손실 XZ 조각으로, 소스 HTML variation이 XZ로 보관되어 있습니다. 아래 검사 과정에서 표준 라이브러리만으로 원래의 `kriss-wide-master.pptx` 및 HTML을 **바이트 단위로 동일하게 복원**하며 SHA-256을 검증합니다. 기존 `reference.html`도 4개의 분할 gzip 전송 파일에서 무손실 복원합니다. 원본 데이터·슬라이드 마스터는 변형되지 않습니다. ZIP 압축 해제 직후에도 동일한 명령을 사용하십시오. 이 검사는 외부 Python 패키지가 필요하지 않습니다.

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

Linux에서 필요한 시스템 라이브러리까지 설치하려면 관리 정책에 따라 `python -m playwright install --with-deps chromium`을 사용합니다. 전체 QA에는 LibreOffice(`libreoffice` 또는 `soffice`), Poppler(`pdftoppm`), Fontconfig(`fc-match`)가 PATH에 있어야 합니다. 표준 설치·검증·PPTX 변환 과정에는 Node.js가 필요하지 않습니다.

시스템 Chromium을 사용하려면 `CHROMIUM_PATH` 환경 변수 또는 `--chromium /path/to/chromium`을 지정합니다. 스킬은 환경 변수 → 시스템 Chromium → Playwright 관리 브라우저 순으로 탐색합니다. 브라우저 버전은 evidence에 기록됩니다.

```bash
python scripts/check_environment.py --font "나눔바른고딕" --font "JetBrains Mono" --json environment.json
```

실제로 선택한 레퍼런스가 요구하는 모든 글꼴을 별도 설치해야 합니다. 위 두 family 외의 글꼴도 입력에 따라 추가합니다. 글꼴 파일은 배포하지 않으며 final HTML에도 내장하지 않습니다. family 확인은 개별 글리프 fallback이 없다는 증명이 아닙니다. `constraints-tested.txt`는 관측한 직접 의존성 조합이며 완전한 lockfile이 아닙니다. 네트워크 신규 설치의 재현성은 이번 환경에서 확인하지 못했습니다.

## 원본 PPTX 마스터·레이아웃 상속 (rc3)

`references/kriss-wide-master.pptx`는 사용자가 제공한 원본 KRISS wide 형식(1개 master, 14개 layout)입니다. `reference.html`은 기존과 같이 표지·제목·배경·로고를 **모두 표시**합니다. PPTX 변환 시에만 표지/표준/구분 슬라이드의 정확히 일치하는 배경을 PPTX의 마스터/레이아웃에서 상속하고 슬라이드에 중복 이미지로 만들지 않습니다. 같은 원본 레이아웃의 그림과 바이트·위치가 일치하는 로고만 슬라이드 그림 변환을 생략합니다. 일치하지 않는 원본 자산은 조용히 재배치하거나 중복시키지 않고 차단 또는 별도 native 객체로 처리합니다.

공식 원본의 텍스트 서식: 나눔바른고딕, 표준 제목 28pt, 표지 제목 40pt, 본문 1~5수준 28/24/20/18/18pt. `python scripts/master_typography.py`로 직접 재확인합니다. 원본 서식에서 공간이 허용되지 않는 표·출처·그림 레이블은 본문 스타일을 무조건 강제하지 않고 원본 DOM의 명시적인 서식과 가독성을 검토합니다. 글꼴 파일은 배포하지 않습니다.

상세 사용 제한과 상속·객체 대응 검증은 `references/native-master-contract.md`를 참조하십시오.

## 원본 이미지와 variation

표준 variation도 `reference.html`의 원본 배경 JPEG를 그대로 사용합니다. 제목 장식과 하단 띠를 CSS로 다시 그리지 않습니다. 이전 H02–H06의 배경 제거 규칙과 V10의 전면 대체 배경은 HTML 작성 단계에서 수정했습니다. V10의 어두운 강조는 본문 패널 안에만 적용합니다. 자세한 규칙은 `references/original-artwork-contract.md`를 참조하십시오.

구형 HTML에 비표준 배경이나 제목 장식이 있으면 `references/reference.html`과 비교하여 원본 HTML에서 직접 수정한 뒤 빌드합니다. 빌드는 입력의 잘못된 배경을 자동으로 바꾸지 않고 차단합니다.

## 실행

```bash
python scripts/validate_html.py presentation.html
python scripts/build_release.py presentation.html presentation.pptx
```

입력 HTML은 보존하고, 같은 위치에 `presentation.final.html`, 지정 위치에 PPTX와 `.evidence/`를 만듭니다. 배포할 HTML은 `.final.html`입니다. 허용된 로컬 이미지·CSS·일반 스크립트는 원래 바이트를 내장하여 상대경로의 해석 차이를 없앱니다. 원본 이미지의 보존을 우선하고, 로컬 자원을 읽기 위해 same-origin 정책을 해제하지 않습니다. 입력 JavaScript를 실행하므로 신뢰할 수 있는 HTML에만 사용하십시오. 컨테이너 실행용 Chromium 인자에는 `--no-sandbox`가 포함되므로, 격리되지 않은 호스트에서 미신뢰 입력을 실행하지 마십시오. 로컬 파일의 입력 디렉터리 이탈, 누락 파일, 로컬 글꼴 내장, 미해결 `srcset`/모듈 경로는 차단됩니다. 외부 자원은 고정되지 않을 수 있으므로 재열기 검사를 통과해야 하며, 재현 가능한 빌드에는 로컬 자원을 권장합니다.

외부 네트워크를 차단한 검증은 `KRISS_OFFLINE=1`로 실행합니다. 입력이 외부 stylesheet·image 등을 필요로 하면 정상 통과를 기대하지 마십시오.

## 판정과 증거

`STATIC → HTML → NATIVE → PARITY → (선택적 REGRESSION)`을 모두 통과한 빌드만 `RELEASED`/exit 0입니다. `BLOCKED`는 검증 실패, `BUILD_ERROR`는 빌드 미완료이며 둘 다 exit 1입니다. 이 상태의 PPTX는 진단용입니다. 반복 빌드가 초기에 실패하면 과거 PPTX 파일은 남을 수 있으나, 이전 성공 manifest는 즉시 무효화됩니다. 파일 존재나 생성 시각만으로 배포 여부를 판단하지 마십시오.

객체 목록은 exporter 필터 이전의 DOM에서 독립적으로 수집합니다. 의미 있는 객체는 native 대응 객체가 있어야 하며, 작아서 전체 화면 픽셀 차이가 적어도 누락을 허용하지 않습니다. SVG 기본 도형 외의 미지원 구조, 미해결 overflow, 중복 ID, 비어 있는 speaker notes, 리소스 로딩 오류는 차단됩니다.

일반 HTML 활성화와 export는 같은 layout settle API를 사용합니다. 최종 HTML을 별도 페이지에서 다시 열어 일반적인 `.active` 전환으로 geometry·computed style·렌더를 비교합니다. screenshot SHA 일치 여부는 별도 기록하며, 승인에는 기존 global/local 수치 기준을 그대로 사용합니다. 단순 anti-aliasing 차이를 이유로 layout을 이동하거나 비교 허용치를 높이지 않습니다.

Evidence에는 입력·final HTML·모델·PPTX·이미지 자원 hash, 도구 버전, 객체 대응, native 검사, HTML 재열기, LibreOffice 렌더 비교가 포함됩니다. 이것은 재현성/변조 감지를 위한 연결 정보이지 공격자가 모든 파일과 hash를 재작성하는 상황에 대한 전자서명은 아닙니다.

## 구조와 버전관리

`SKILL.md`, 필수 `references/`·`scripts/`, 의존성·라이선스·출처 문서, 설치 안내 및 무결성 manifest만 포함합니다. `.gitignore`는 저장소에 실행 산출물이 포함되지 않도록 유지합니다. `.agent`, 개발용 테스트·CI, 시험 입력, 발표자료, 비교 이미지, 실행 결과, 패치 ZIP, 과거 작업 기록과 글꼴 파일은 제외합니다. 실제 사용 중 실행하는 HTML/native/parity 검사 및 설치 무결성 검사는 스킬 기능이므로 유지합니다. 개발 시험·검증 증거는 설치본 밖에서 관리하며 설치에 필요하지 않습니다.

`VERSION`이 실행 버전의 유일한 기준입니다. exporter, build의 실패 기록 및 환경 점검은 이 파일을 읽습니다. 파일 변경 시 `PACKAGE-MANIFEST.json`도 갱신해야 하며, 버전·manifest 불일치를 무시하지 않습니다.

대상 저장소: `celllamb/kriss-skill`. 스킬 디렉터리만 업데이트하며 다른 스킬은 변경하지 않습니다. 설치 디렉터리는 `kriss-ppt/`로 추가하며 다른 스킬이나 저장소 루트 문서를 덮어쓰지 않습니다.

## rc3 기반 외부 링크 보존

This installation includes native external text hyperlink capture, complete
source-text/link coverage and native URL validation. Canonical and approved
reference click navigation now ignores links and interactive controls. Layout,
image assets and parity thresholds are unchanged. Relative/internal links,
nontext hyperlinks and generated link content remain explicitly unsupported.
See `references/hyperlink-contract.md`.

This is an rc3-based build, not a new stable release or a claim that all original
patterns have been visually recertified. Earlier rc3 test and pattern results
retain their original scope.


## Source-bound speaker notes

Plain-text `data-notes` is captured from the settled DOM before export filtering.
The native notes body must match exactly, including Unicode, paragraphs, blank
lines and whitespace. The delivered HTML reread must reproduce the same notes.
Missing, changed or unreadable notes block approval even when slide pixels match.
See `references/speaker-notes-contract.md`. Rebuild older evidence without this
contract rather than treating a missing notes record as a pass. This local update
includes the earlier hyperlink fixes; it does not re-certify all patterns.
