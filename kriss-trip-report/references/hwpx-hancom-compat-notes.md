# HWPX Hancom 호환성 노트

이 문서는 공개 HWPX/OWPML 자료만으로 명확하지 않았거나, 자연스러운 XML 해석과 실제 Hancom HWP 동작이 달랐던 사항을 기록한다. 이미지가 포함된 HWPX 보고서를 만들거나 수정할 때, 특히 desktop Hancom HWP에서 안정적으로 열려야 할 때 사용한다.

## 범위

아래 내용은 이미지가 많은 KRISS 국외출장보고서와 증빙/발표 그림을 수리하면서 확인한 사항이다. 근거는 다음과 같다.

- HWPX ZIP/XML 직접 검사
- Desktop Hancom HWP COM 자동화(`HWPFrame.HwpObject`)
- HWP 자체 `InsertPicture`가 만든 sample 파일
- HWP 열기/저장 round-trip 비교
- HWP PDF export 후 page image/contact sheet 검사

아래 항목은 공식 포맷 문서를 대체하는 설명이 아니라, Hancom Office 호환성 규칙으로 취급한다.

## 기준으로 사용한 공식 문서

- Hancom은 HWP/HWPML/OWPML 포맷 자료를 공개하며, OWPML이 열린 HWP 문서 형식이고 이전 호환 버전에서는 `.hwpx`, HWP 2018 이후에는 `.owpml`을 지원한다고 설명한다: https://www.hancom.com/support/downloadCenter/hwpOwpml
- Hancom Help의 그림 삽입 문서는 embedded/linked picture workflow, in-line 배치, 크기 조정, fit-to-cell 등을 설명한다: https://help.hancom.com/hoffice100/en-US/Hwp/insert/figure/figure.htm
- Hancom Help의 object size/position 문서는 fixed/relative 값, in-line, square, top-and-bottom 같은 wrapping/placement option을 설명한다: https://help.hancom.com/hoffice/multi/en_us/hwp/insert/objectattribute/objectattribute%28general%29.htm
- Hancom Developer는 `HwpCtrl.InsertPicture`를 공개하지만, desktop HWP가 삽입 후 쓰는 HWPX XML 구조를 충분히 설명하지는 않는다: https://developer.hancom.com/en-us/webhwp/devguide/hwpctrl/methods/insertpicture

## 주요 호환성 발견사항

### 1. HWP 호환 picture XML은 단순 spec형 XML과 다르다

실패한 보고서들은 package 항목과 이미지 파일 자체는 유효했지만, 일부 그림이 회색/검은 placeholder로 보이거나 HWP 열기 동작이 불안정했다. 해결은 단순히 “유효한 XML”이 아니라, HWP가 `InsertPicture`로 만든 그림 객체와 비슷한 `hp:pic` 구조를 쓰는 것이었다.

단순 embedded picture에서 HWP가 만든 패턴:

```xml
<hp:pic textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" numberingType="PICTURE">
  <hp:offset x="0" y="0"/>
  <hp:orgSz width="{target_display_hwp_unit}" height="{target_display_hwp_unit}"/>
  <hp:curSz width="0" height="0"/>
  <hp:flip horizontal="0" vertical="0"/>
  <hp:rotationInfo angle="0" centerX="{target_w/2}" centerY="{target_h/2}" rotateimage="1"/>
  <hp:renderingInfo>
    <hc:transMatrix e1="1" e2="0" e3="0" e4="0" e5="1" e6="0"/>
    <hc:scaMatrix e1="1" e2="0" e3="0" e4="0" e5="1" e6="0"/>
    <hc:rotMatrix e1="1" e2="0" e3="0" e4="0" e5="1" e6="0"/>
  </hp:renderingInfo>
  <hp:imgRect>
    <hc:pt0 x="0" y="0"/>
    <hc:pt1 x="{target_w}" y="0"/>
    <hc:pt2 x="{target_w}" y="{target_h}"/>
    <hc:pt3 x="0" y="{target_h}"/>
  </hp:imgRect>
  <hp:imgClip left="0" right="{source_image_unit_w}" top="0" bottom="{source_image_unit_h}"/>
  <hp:inMargin left="0" right="0" top="0" bottom="0"/>
  <hp:imgDim dimwidth="{source_image_unit_w}" dimheight="{source_image_unit_h}"/>
  <hc:img binaryItemIDRef="imageN" bright="0" contrast="0" effect="REAL_PIC" alpha="0"/>
  <hp:effects/>
  <hp:sz width="{target_w}" widthRelTo="ABSOLUTE" height="{target_h}" heightRelTo="ABSOLUTE" protect="0"/>
  <hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1" allowOverlap="0"
          holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN"
          vertAlign="TOP" horzAlign="LEFT" vertOffset="0" horzOffset="0"/>
  <hp:outMargin left="0" right="0" top="0" bottom="0"/>
</hp:pic>
```

실무 규칙:

- `orgSz`와 `sz`가 보이는 표시 크기를 가지더라도 `curSz width="0" height="0"`를 사용한다.
- `rotateimage="1"`을 사용한다.
- `transMatrix`, `scaMatrix`, `rotMatrix`는 identity matrix로 둔다.
- 같은 `hp:run` 안에서 `hp:pic` 뒤에 비어 있는 sibling `hp:t`를 추가한다. HWP가 만든 그림 run에는 이 구조가 포함된다.
- 복사한 문단의 오래된 `hp:linesegarray` layout cache는 제거하고 HWP가 다시 계산하게 한다.

### 2. 표시 단위와 원본 이미지 단위는 다르다

원본 픽셀 크기를 보이는 HWP 그림 크기로 쓰지 않는다.

관찰된 표시 크기 변환:

```text
target_hwp_unit = round(target_mm / 25.4 * 7200)
```

Desktop HWP `InsertPicture` 예:

- 2000 x 1125 PNG를 width/height 인자 `150, 84`로 넣으면 `orgSz width="42520" height="23811"`이 생성되었다.
- `150 / 25.4 * 7200 = 42519.7`이므로, desktop HWP는 inch당 7200 HWP 표시 단위를 쓰는 것으로 보인다.

중요한 실패 양상:

- `36000`이 HWP 단위처럼 보인다고 `InsertPicture` width로 넘기면 매우 큰 그림이 된다. 이미지가 page 밖으로 나가 PDF export 후 blank/cropped처럼 보일 수 있다.

원본 이미지 crop/extent 단위:

- `imgClip`과 `imgDim`은 표시 HWP 단위가 아니라 원본 이미지 좌표 단위이다.
- HWP 출력은 대략 `pixel * 75`에 비례했지만, metadata와 rounding에 따라 정확한 값은 달라질 수 있다.
- `imgClip`과 `imgDim`은 서로 일관되게 유지한다. 이 값을 `orgSz`/`sz`와 같게 강제하지 않는다.

### 3. 이미지 payload 형식은 spec보다 HWP renderer 동작이 중요하다

HWP Help는 PNG, JPG, BMP 등 여러 그림 형식을 지원한다고 하지만, 생성 HWPX package에서는 HWP 자체 출력과 유사하게 만드는 방식이 가장 안정적이었다.

- 삽입 슬라이드/증빙 이미지는 RGB PNG로 `BinData/` 아래 저장한다.
- `Contents/content.hpf`에 대응 manifest 항목을 추가한다. 예: `id="image1" href="BinData/image1.png" media-type="image/png" isEmbeded="1"`
- `BinData/` 이미지 ZIP entry는 무압축(`ZIP_STORED`)으로 저장한다.
- 매우 큰 이미지는 삽입 전 제한한다. 이 스킬에서는 `MAX_EMBEDDED_PIXEL_EDGE = 2200`이 가독성과 안정성에 충분했다.

실패했거나 위험한 접근:

- spec상 그럴듯한 치수를 가진 수작업 JPEG picture 객체는 열리더라도 HWP PDF export에서 회색/검은 placeholder가 생겼다.
- BMP 변환은 출력만 커졌고 rendering 문제를 해결하지 못했다.
- progressive JPEG와 이중 압축된 image entry는 피한다.

### 4. 유효한 HWPX만으로는 부족하며 HWP render/export 검증이 필요하다

문제가 있던 보고서도 기본 ZIP/XML 및 이미지 decode 검증은 통과했다. 실패는 desktop HWP가 layout하거나 export할 때 드러났다.

이미지 포함 보고서 최소 검증:

1. 일반 HWPX 검증 실행
2. 이미지 참조 검증 실행
   - 모든 `hc:img binaryItemIDRef`에 manifest 항목이 있는지
   - 모든 manifest image가 `BinData/`에 있는지
   - 모든 이미지가 decode되는지
   - media type과 extension이 맞는지
   - `hp:pic` 크기가 plausible한지
3. Desktop HWP에서 파일 열기
4. 생성 원본을 덮어쓰지 말고 별도 HWPX로 저장
5. 원본과 HWP 저장본 package 비교
6. HWP에서 PDF export
7. PDF를 page image로 렌더링하고 contact sheet 확인

HWP가 파일을 열 수 있어도 개별 그림 control이 placeholder로 export될 수 있으므로 contact sheet 검사가 중요하다.

비대화식 HWP2018 round-trip 검증에는 다음을 사용한다.

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_hwp_security_module.ps1 -Force
powershell -ExecutionPolicy Bypass -File scripts\hwp2018_roundtrip.ps1 generated.hwpx hwp_roundtrip.hwpx -Force
```

설치 스크립트는 공식 Hancom file-path checker module을 `HKEY_CURRENT_USER\Software\HNC\HwpAutomation\Modules`에 등록한다. round-trip helper는 HWP COM object를 사용하고, `RegisterModule("FilePathCheckDLL", "FilePathCheckerModuleExample")`이 반드시 `True`를 반환해야 한다. 그 뒤 `SetMessageBoxMode(0x00020000)`를 임시로 설정하고, 별도 output path에 저장하며, explicit HWPX 열기와 auto-format 열기를 모두 확인한 뒤 기존 message-box mode로 복원한다. message box 억제를 overwrite 처리의 대체물로 쓰지 않도록 fresh output path를 선호한다.

중요: `SetMessageBoxMode`는 일반 HWP 자동화 message box를 억제하지만, 파일 접근 보안 승인창을 단독으로 억제하지 못한다. `RegisterModule`이 `False`이면 보안모듈 registry entry를 먼저 고쳐야 한다.

### 5. HWP round-trip 변경은 예상되지만 image payload 변경은 안 된다

Desktop HWP는 저장할 때 생성 package 일부를 다시 쓴다. 이것만으로 생성 파일이 잘못되었다고 볼 수는 없다.

수리된 보고서에서 HWP가 변경한 항목:

- `Contents/content.hpf`
- `Contents/header.xml`
- `Contents/section0.xml`
- `Preview/PrvImage.png`
- `Preview/PrvText.txt`
- `META-INF/container.rdf`, `META-INF/container.xml`, `version.xml` 같은 container/version metadata

중요한 통과 조건:

```text
image_payloads_unchanged = true
only_hancom_normalized_entries = true
```

다음이면 HWP round-trip을 허용한다.

- package entry 추가/삭제가 없음
- 모든 `BinData/` image hash가 변하지 않음
- HWP가 정규화한 XML/preview/metadata만 달라짐

다음이면 거부하거나 수정한다.

- `BinData/` 이미지가 제거, 잘못 rename, 재인코딩됨
- `hc:img` 참조가 사라짐
- HWP가 반복 crash/restart 후에야 열림
- PDF export에서 여전히 검은/회색 placeholder나 심한 cropping이 보임

### 6. HWP가 별도 저장본을 고쳐도 생성 원본은 그대로일 수 있다

이 사례에서는 생성 HWPX를 열어도 원본 파일이 disk에서 자동 수정되지는 않았다. 원본 hash와 timestamp는 유지되었고, HWP 변경은 명시적으로 저장한 round-trip copy에만 나타났다.

그래도 항상 그렇다고 가정하지 않는다. 앞으로는 다음을 기록한다.

- 생성 직후 generated file hash 기록
- HWP에서 열기
- generated file hash와 timestamp 재확인
- HWP version을 별도 path로 저장
- 두 package 비교

### 7. 현재 스킬 구현 규칙

새 HWP version이 다른 동작을 입증하기 전까지 `kriss-trip-report`는 다음 생성 규칙을 유지한다.

- 수작업 JPEG/BMP variant가 아니라 PNG `BinData/imageN.png` payload를 사용한다.
- `BinData/` ZIP entry는 무압축으로 둔다.
- HWP 호환 `hp:pic` 필드를 사용한다.
  - `orgSz`/`imgRect`/`sz`: 표시 HWP 단위
  - `curSz = 0`
  - `imgClip`/`imgDim`: 원본 이미지 단위
  - identity rendering matrices
- 일반 보고서 column 이미지는 target display width 약 150 mm를 사용한다.
- 개인정보 마스킹 후에만 full-page 증빙 이미지를 사용한다.
- 최종 전달 전 validate, HWP round-trip, compare, PDF export, contact-sheet inspect를 수행한다.

## 이 스킬에서 사용하는 명령

생성:

```powershell
python scripts\draft_hwpx_from_markdown.py input.md output.hwpx
```

package/XML 검증:

```powershell
python C:\Users\stape\.codex\skills\edit-hwpx-docs\scripts\hwpx_tool.py validate output.hwpx
```

이미지 참조 검증:

```powershell
python scripts\validate_hwpx_images.py output.hwpx
```

생성본과 HWP 저장본 비교:

```powershell
python scripts\compare_hwpx_packages.py generated.hwpx hwp_roundtrip.hwpx
```

HWP export PDF 페이지 렌더링:

```powershell
python scripts\render_pdf_pages.py hwp_export.pdf --pages 1-17 --output-dir pages --prefix report --dpi 140
```

## 최종 경험칙

공식 HWPX/OWPML 구조는 필요조건이지만 desktop HWP 호환성의 충분조건은 아니다. 이미지가 많은 생성 보고서에서는 HWP 자체 `InsertPicture` 출력 형태를 신뢰하고, HWP round-trip과 PDF rendering으로 확인한다.
