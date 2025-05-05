from application.dto.compile_request import CompileRequest
from application.dto.process_result import ProcessResult
from domain.models.tex_document import TexDocument
from domain.models.latexmkrc_source import LatexmkrcSource
from domain.services.latex_compile_service import LatexCompileService


class GeneratePdfUseCase:
    """
    Use Case that executes CompileRequest.
    """

    def __init__(self, compile_service: LatexCompileService):
        self.compile_service = compile_service

    def execute(self, request: CompileRequest) -> ProcessResult:
        logs: list[str] = []
        # 入力モデル生成と検証
        tex_doc = TexDocument(content=request.tex_content)
        tex_doc.validate()
        logs.append("Validated TexDocument.")

        rc_source = LatexmkrcSource(content=request.latexmkrc_content)
        rc_source.validate()
        logs.append("Validated LatexmkrcSource.")

        # PDF を生成
        result = self.compile_service.compile(tex_doc, rc_source)
        pdf_doc = result
        logs.append(f"Generated PDF at {pdf_doc.path}")

        return ProcessResult(pdf_path=pdf_doc.path, logs=logs)
