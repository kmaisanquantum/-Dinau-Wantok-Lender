# Alesco Payslip Parsing Pipeline

Implementation: `backend/app/services/payslip_parser.py`

## Why this design

Agents onboard borrowers in the field, often photographing a paper
payslip on a low-end Android phone with poor lighting. The pipeline
has to be tolerant of bad scans while never silently trusting a
misread number — a wrong Net Pay figure feeds directly into the
Alesco 50% deduction-ceiling check, which is a regulatory limit, not
a business preference.

## Stages

1. **Input** — JPG/PNG photo or PDF export of a standard PNG Alesco
   public-service payslip.
2. **Pre-process** — EXIF-based rotation correction, grayscale
   conversion, autocontrast. PDFs are rasterized at 300dpi per page
   with `pdf2image` before the same pipeline applies.
3. **OCR** — `pytesseract` with PSM 6 (uniform text block), which
   matches the typical single-column payslip layout better than
   Tesseract's default page-segmentation mode.
4. **Field extraction** — regex anchors search the OCR text for
   `GROSS PAY`, `NET PAY`, `TOTAL DEDUCTIONS`, and an employee/file
   number, plus a per-line deduction-table pattern (code, description,
   amount) rather than relying on fixed pixel coordinates, since crop
   and scan quality vary a lot between agents' phones.
5. **Reconciliation check** — Gross Pay minus the summed deduction
   lines must equal Net Pay within a 1 Kina tolerance. If it doesn't,
   the extract is marked `needs_manual_review` instead of being
   trusted automatically — OCR misreads a digit far more often than a
   payslip's own arithmetic is wrong.
6. **Ceiling check** — `check_deduction_ceiling()` computes what the
   borrower's *total* deduction percentage of gross pay would become
   if a proposed new loan repayment were added, and compares it
   against `settings.alesco_max_total_deduction_pct` (default 50%,
   configurable because the ceiling is set by government circular and
   has changed before). Loans that would breach the ceiling should be
   refused or resized by the loan-issuance flow — this function only
   answers the compliance question, it never authorizes a loan itself.
7. **Output** — a `PayslipExtract` mapped onto the borrower's
   `net_pay_at_disbursement` / `total_deduction_pct_at_disbursement`
   columns at the point a loan is created, so every loan carries a
   compliance snapshot rather than relying on a value that could grow
   stale.

## Operational notes

- Employee name is **not** auto-extracted from the payslip; it's
  confirmed manually against the borrower's ID at onboarding, to avoid
  silently trusting an OCR misread of a name field into the borrower
  record.
- `raw_text` is retained on the extract object during processing for
  debugging/manual review, but should not be persisted to the database
  — only the structured fields belong in `borrowers`/`loans`.
- Tesseract + poppler are installed in the backend Docker image (see
  `backend/Dockerfile`); no external OCR API dependency, keeping the
  pipeline usable even if outbound internet from the VPS is
  unreliable.
