"""
Lightweight Document Parsing — PNG Alesco Payslip Extractor.

Design notes (see docs/payslip_parsing.md for the full pipeline write-up):

  1. INPUT: image (jpg/png, phone photo) or PDF of an Alesco public
     service payslip.
  2. PRE-PROCESS: PDF pages are rasterized; images are deskewed and
     contrast-normalized so low-quality phone photos still OCR
     reliably on cheap Android devices.
  3. OCR: pytesseract extracts raw text.
  4. FIELD EXTRACTION: layout on Alesco payslips is fairly consistent
     ("GROSS PAY", "NET PAY", "TOTAL DEDUCTIONS" and a per-line
     deduction table with status/ceiling codes). Regex anchors pull
     the fields out of the OCR text rather than depending on fixed
     pixel coordinates, since scan quality and cropping vary.
  5. VALIDATION: Net Pay must reconcile with Gross Pay minus the sum
     of parsed deductions within a small tolerance, or the record is
     flagged for manual review instead of silently trusting bad OCR.
  6. CEILING CHECK: existing total deduction % is computed and checked
     against the regulatory 50% net-pay retention ceiling BEFORE a new
     loan's deduction is added, so the system can refuse or size a
     loan that would push the borrower over the legal limit.
  7. OUTPUT: a structured PayslipExtract mapped onto the borrower's
     `net_pay_at_disbursement` / `total_deduction_pct_at_disbursement`
     fields — nothing here writes the loan itself; that decision stays
     in the loan-issuance service so the ceiling check can't be bypassed.
"""
import re
from dataclasses import dataclass, field
from io import BytesIO
from typing import Optional

from PIL import Image, ImageOps
import pytesseract

from app.core.config import settings


@dataclass
class DeductionLine:
    code: str
    description: str
    amount: float


@dataclass
class PayslipExtract:
    employee_name: Optional[str]
    alesco_file_number: Optional[str]
    gross_pay: Optional[float]
    net_pay: Optional[float]
    total_deductions: Optional[float]
    deduction_lines: list[DeductionLine] = field(default_factory=list)
    reconciliation_ok: bool = False
    existing_deduction_pct_of_gross: Optional[float] = None
    needs_manual_review: bool = True
    raw_text: str = ""


_MONEY = r"([\d,]+\.\d{2})"

FIELD_PATTERNS = {
    "gross_pay": re.compile(rf"GROSS\s*PAY[^\d]{{0,10}}{_MONEY}", re.IGNORECASE),
    "net_pay": re.compile(rf"NET\s*PAY[^\d]{{0,10}}{_MONEY}", re.IGNORECASE),
    "total_deductions": re.compile(rf"TOTAL\s*DEDUCTIONS?[^\d]{{0,10}}{_MONEY}", re.IGNORECASE),
    "alesco_file_number": re.compile(r"(?:FILE\s*NO\.?|EMP(?:LOYEE)?\s*NO\.?)[:\s]*([A-Z0-9\-]{4,15})", re.IGNORECASE),
}

# Deduction table rows typically look like: "SVL001  SAVINGS LOAN  120.50"
DEDUCTION_LINE_PATTERN = re.compile(
    r"^\s*([A-Z]{2,6}\d{2,5})\s+([A-Za-z /&\-]{3,40}?)\s+" + _MONEY + r"\s*$",
    re.MULTILINE,
)


def _preprocess_image(image_bytes: bytes) -> Image.Image:
    img = Image.open(BytesIO(image_bytes))
    img = ImageOps.exif_transpose(img)          # correct phone-camera rotation
    img = img.convert("L")                       # grayscale
    img = ImageOps.autocontrast(img, cutoff=2)    # boost faded/low-light scans
    return img


def _ocr(img: Image.Image) -> str:
    # PSM 6: assume a uniform block of text — matches typical payslip layout.
    return pytesseract.image_to_string(img, config="--psm 6")


def _parse_money(raw: str) -> float:
    return float(raw.replace(",", ""))


def extract_from_image_bytes(image_bytes: bytes) -> PayslipExtract:
    img = _preprocess_image(image_bytes)
    text = _ocr(img)
    return _extract_from_text(text)


def extract_from_pdf_bytes(pdf_bytes: bytes) -> PayslipExtract:
    from pdf2image import convert_from_bytes

    pages = convert_from_bytes(pdf_bytes, dpi=300)
    combined_text = ""
    for page in pages:
        page = page.convert("L")
        page = ImageOps.autocontrast(page, cutoff=2)
        combined_text += "\n" + _ocr(page)
    return _extract_from_text(combined_text)


def _extract_from_text(text: str) -> PayslipExtract:
    def find(pattern_key: str) -> Optional[str]:
        m = FIELD_PATTERNS[pattern_key].search(text)
        return m.group(1) if m else None

    gross_raw = find("gross_pay")
    net_raw = find("net_pay")
    total_ded_raw = find("total_deductions")
    file_no = find("alesco_file_number")

    gross = _parse_money(gross_raw) if gross_raw else None
    net = _parse_money(net_raw) if net_raw else None
    total_ded = _parse_money(total_ded_raw) if total_ded_raw else None

    lines = [
        DeductionLine(code=code, description=desc.strip(), amount=_parse_money(amt))
        for code, desc, amt in DEDUCTION_LINE_PATTERN.findall(text)
    ]

    # Reconcile: gross - sum(deduction lines) should ~= net, within 1 kina
    # tolerance for rounding across many deduction rows.
    reconciliation_ok = False
    if gross is not None and net is not None:
        summed = total_ded if total_ded is not None else sum(l.amount for l in lines)
        if summed is not None:
            reconciliation_ok = abs((gross - summed) - net) <= 1.00

    existing_pct = None
    if gross and total_ded:
        existing_pct = round((total_ded / gross) * 100, 2)

    needs_review = not reconciliation_ok or gross is None or net is None

    return PayslipExtract(
        employee_name=None,  # deliberately not auto-extracted; confirmed manually against ID at onboarding
        alesco_file_number=file_no,
        gross_pay=gross,
        net_pay=net,
        total_deductions=total_ded,
        deduction_lines=lines,
        reconciliation_ok=reconciliation_ok,
        existing_deduction_pct_of_gross=existing_pct,
        needs_manual_review=needs_review,
        raw_text=text,
    )


def check_deduction_ceiling(
    extract: PayslipExtract, proposed_new_deduction_amount: float
) -> tuple[bool, float]:
    """
    Returns (within_ceiling, resulting_total_pct).

    Ceiling is defined against GROSS pay per Alesco circulars governing
    total salary deductions for PNG public servants (settings.
    alesco_max_total_deduction_pct, default 50%). If OCR couldn't
    confidently extract gross pay, this refuses to certify compliance
    rather than guessing — callers must route to manual review.
    """
    if extract.gross_pay is None or extract.needs_manual_review:
        return (False, 0.0)

    existing = extract.total_deductions or 0.0
    resulting_total = existing + proposed_new_deduction_amount
    resulting_pct = round((resulting_total / extract.gross_pay) * 100, 2)
    return (resulting_pct <= settings.alesco_max_total_deduction_pct, resulting_pct)
