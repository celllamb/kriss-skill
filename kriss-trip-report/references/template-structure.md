# Template Structure

The bundled template is `assets/kriss-overseas-trip-report-template.hwpx`.

It is a single-section HWPX document with paragraph-style content, not a table. The original title is `국외출장보고서 표준 양식`.

## Required Sections

```text
I. 출장개요
  ○ 목적
  ○ 기간
  ○ 대상국가 및 방문기관
  ○ 출장자 인적사항
      - 성명, 소속, 연락처 등
  ○ 면담자 인적사항
      - 성명, 국가, 소속, 연락처, 면담내용, 면담일시 등

II. 출장내용
  ○ 주요 활동 내용 (일정별 또는 활동내역별로 작성)

III. 시사점 및 특이사항
  ○ 시사점
  ○ 건의사항
  ○ 특이사항
     ※ 선물수령 관련
       - 선물수령 여부 : □ 예. □ 아니오.
       - 선물신고 여부 : □ 예. □ 아니오.

IV. 기타자료
  ○ 수집자료
      - 제목, 저자, 발행처, 발행년도 등
  ○ 출입국 입증 자료
    - 항공권 또는 보딩패스 사본
    - 출입국 사실증명서
```

## Writing Conventions

- Keep the purpose short and official.
- Use evidence-based dates for the period.
- For `대상국가 및 방문기관`, write one comprehensive location/institution line. Do not list daily rooms or sub-venues unless the user explicitly asks.
- Use agenda or itinerary order for activity summaries.
- Do not put working notes or source-gap phrases in the final body. Avoid `확인 필요`, `자료상`, `입력자료`, `첨부자료`, `제공된 자료`, `녹취록 확인`, and `회의록 확인`.
- When a required fact cannot be derived, ask the user before finalizing or leave the specific item blank if the template permits it.
- Follow the privacy rules in `privacy.md`; do not keep the template's privacy-warning sentence in the final report.
- Treat italic/helper text in the standard template as writing instructions, not final report content.
- Remove helper lines such as `성명, 소속, 연락처 등`, `성명, 국가, 소속, 연락처, 면담내용, 면담일시 등`, `제목, 저자, 발행처, 발행년도 등`, and `개인정보(주민등록번호 등) 반드시 삭제 요망` from the final report.
- Keep the gift receipt/declaration checkbox lines unchanged unless the user explicitly provides final checked values:
  - `선물수령 여부 : □ 예. □ 아니오.`
  - `선물신고 여부 : □ 예. □ 아니오.`
- Under each `○` item, write actual content as `      - ...` sub-bullets.
- Under `○ 주요 활동 내용`, agenda numbers such as `1. ...` may follow directly, but indent them beneath the `○` item.
- For meeting reports, cover updates, discussions/agreements, and follow-up plans with label-less `      - ...` sub-bullets. Do not write literal labels such as `업데이트 사항:`, `논의 사항 및 합의 사항:`, or `추후 계획:` in the final activity bullets.
- Write `주요 활동 내용` in Korean bullet style (`개조식`). For substantive agenda items, use enough bullets to reach about one HWPX page per agenda when source material supports it.
- Use concise Korean nominal/bullet-style endings in final report bullets. Prefer endings such as `필요함`, `확인`, `논의`, `제시`, `검토 필요`, and `반영 필요`; avoid prose endings such as `필요하다`, `확인하였다`, `논의되었다`, `제시되었다`, and `검토할 필요가 있다`.
- If adding an agenda slide, meeting photo, or figure, insert no more than one representative image per agenda and keep it near the related agenda bullets. Choose the single slide/photo/figure that best represents the agenda's topic, result, KRISS contribution, decision, or timeline. Do not include multiple slides under one agenda; omit the image when no representative slide exists.
- Write `시사점` and `특이사항` in readable Korean bullet style (`개조식`). Avoid long paragraph-like bullets; split complex points into short bullets or indented sub-bullets.
- In `특이사항`, use numbered issue-group headings (`1. ...`, `2. ...`) and reserve hyphen bullets for details under each issue group. This keeps issue-group headings visually distinct from their subordinate detail bullets.
- Do not list travel evidence documents in `수집자료`; reserve that list for meeting/report source materials.
- Insert evidence images used for `출입국 입증 자료` after masking 주민등록번호, 여권번호, and 외국인등록번호. If an airline ticket or boarding pass exists, include it together with the immigration fact certificate unless the user asks otherwise. Evidence images should show the full document page, not a cropped excerpt, and each evidence category should start on its own page when generating HWPX.
- When generating HWPX, embed images as PNG files in `BinData` following `references/hwpx-hancom-compat-notes.md`.
