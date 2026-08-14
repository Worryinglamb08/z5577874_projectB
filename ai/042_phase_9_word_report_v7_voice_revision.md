# AI prompting log 042 — Phase 9 Word report Version 7 voice revision

## Request

Revise `report/report_v5.docx` into a separate Version 7 Word file. The pass was
restricted to writing voice: remove third-person references to the author,
external-assessor framing, rubric-aware defence and self-congratulatory claims.
Retain the report structure, methods, results, tables, figures, conclusions and
cautious treatment of uncertainty.

## Source and output

- Source: `report/report_v5.docx`
- Output: `report/report_v7.docx`
- Version 5 SHA-256 before and after the revision:
  `de2c643f34cbb214e79679d7e417bb4e3d248036c5b0668745d4ccc14255fa85`
- Version 7 SHA-256:
  `0ba280d13904c473305be0fcf07cd257b96413f12f88af1296859ed753f58a41`

## Voice decisions

- Replaced every use of `the student` or `the student's` in the report with
  neutral academic prose or selective first person.
- Reframed claims about contribution, requirements and product merit as direct
  descriptions of the analysis, implementation or evidence.
- Replaced phrases such as `earns its place`, `meets the Part B product test`
  and `not an omitted research step` with methodological explanations.
- Used first person only where an authorial decision or interpretation matters,
  including calendar alignment, lexicon review, event interpretation, risk-free
  rate choice, holdings terminology and the AI-use disclosure.
- Preserved the negative sentiment-fusion result and the limitations attached
  to Maximum Sharpe, coverage confidence and the short 2021–2023 evaluation.
- Retained Version 5's three recommendations, including the proposal to study
  estimation stability and market regimes on new data.

## Validation

- Identical numeric-token multiset across Version 5 and Version 7.
- Identical six Word tables and all table cell values.
- Identical 13 Word captions.
- Identical nine embedded figures and figure ordering.
- Identical counts of sections, paragraphs, tables and inline shapes.
- Version 5 source hash unchanged.
- Word count changed from 4,900 to 4,923 words, a 23-word increase.
- Repository proofreader: zero doubled-word, spacing, reference or placeholder
  findings.
- Final package-wide Word XML scan: zero occurrences of third-person student
  references, rubric/marker/marks/credit language, self-praise terms or the
  specified defensive phrases.

No analytical code, result artifact, citation, portfolio definition, sample,
cost assumption, sentiment rule, table value, figure value or conclusion was
changed in this revision.
