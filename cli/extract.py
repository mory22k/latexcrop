import argparse
from pathlib import Path

from application.dto.extract_request import ExtractRequest
from application.dto.extract_result import ExtractResult
from application.usecases.extract_tex_usecase import ExtractTexUseCase
from domain.services.pdf_extract_service import PdfExtractService
import sys


def main():
    p = argparse.ArgumentParser(description="Extract TeX from PDF.")
    p.add_argument(
        "pdf",
        type=Path,
        nargs="?",
        default=Path("result/output.pdf"),
        help="Path to the PDF file to extract TeX from (default: result/output.pdf)",
    )
    args = p.parse_args()
    cli_dir = Path(__file__).resolve().parent

    # ユースケース初期化
    extract_svc = PdfExtractService()
    extract_uc = ExtractTexUseCase(extract_svc)

    # 実行
    # PDF パスを決定
    pdf_path: Path = cli_dir / args.pdf
    pdf_path_lookup: Path = pdf_path.resolve().parent
    if not pdf_path.exists():
        pdf_candidates = list(pdf_path_lookup.glob("*.pdf"))
        if not pdf_candidates:
            print(f"No PDF files found in {pdf_path_lookup}")
            sys.exit(1)
        pdf_path = pdf_candidates[0]

    print(f"Using PDF: {pdf_path.name!r}")
    req: ExtractRequest = ExtractRequest(pdf_path=pdf_path)
    res: ExtractResult = extract_uc.execute(req)

    # 出力ファイル作成
    tex_dir = cli_dir / "tex"
    tex_dir.mkdir(exist_ok=True)
    # preamble_out = tex_dir / "preamble"
    body_out = tex_dir / "texbody"

    # preamble_out.write_text(res.preamble, encoding="utf-8")
    body_out.write_text(res.body, encoding="utf-8")

    print("Extracted to:")
    # print("  ", preamble_out)
    print("  ", body_out)


if __name__ == "__main__":
    main()
