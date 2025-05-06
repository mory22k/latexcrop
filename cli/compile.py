import sys
import argparse
from pathlib import Path

from application.dto.pipeline_request import PipelineRequest
from application.usecases.process_pdf_pipeline_usecase import ProcessPdfPipelineUseCase
from application.usecases.generate_pdf_usecase import GeneratePdfUseCase
from application.usecases.trim_pdf_usecase import TrimPdfUseCase
from application.usecases.embed_tex_usecase import EmbedTexUseCase
from application.usecases.make_transparent_usecase import MakeTransparentUseCase
from domain.services.latex_compile_service import LatexCompileService
from domain.services.pdf_crop_service import PdfCropService
from domain.services.pdf_embed_service import PdfEmbedService
from domain.services.pdf_transparency_service import PdfTransparencyService


def main():
    p = argparse.ArgumentParser(description="Compile LaTeX to PDF and process it.")
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("result/output.pdf"),
        help="出力PDFのパス",
    )
    args = p.parse_args()
    cli_dir = Path(__file__).resolve().parent
    tex_dir = cli_dir / "tex"

    # 入力ファイルの読み込み
    latexmkrc_content = (tex_dir / "latexmkrc").read_text(encoding="utf-8")
    preamble = (tex_dir / "preamble").read_text(encoding="utf-8")
    body = (tex_dir / "texbody").read_text(encoding="utf-8")

    tex_content = preamble + "\n\\begin{document}\n" + body + "\n\\end{document}\n"

    # サービスとユースケースの初期化
    compile_svc = LatexCompileService()
    crop_svc = PdfCropService()
    embed_svc = PdfEmbedService()
    transp_svc = PdfTransparencyService()

    pipeline_uc = ProcessPdfPipelineUseCase(
        generate_uc=GeneratePdfUseCase(compile_svc),
        trim_uc=TrimPdfUseCase(crop_svc),
        embed_uc=EmbedTexUseCase(embed_svc),
        transparency_uc=MakeTransparentUseCase(transp_svc),
    )

    # 実行
    result = pipeline_uc.execute(
        PipelineRequest(
            tex_content=tex_content,
            latexmkrc_content=latexmkrc_content,
            margins=(0, 0, 0, 0),
        )
    )

    # 成功時のみ出力ファイルを移動
    if result.is_success:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        Path(result.pdf_path).rename(cli_dir / args.output)
        print(f"Generated: {args.output}")
    else:
        print("Error:")
        for ln in result.logs:
            print("  ", ln)
        sys.exit(1)


if __name__ == "__main__":
    main()
