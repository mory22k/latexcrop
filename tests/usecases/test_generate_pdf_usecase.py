from unittest.mock import MagicMock

from application.usecases.generate_pdf_usecase import GeneratePdfUseCase
from application.dto.compile_request import CompileRequest
from application.dto.process_result import ProcessResult
from domain.services.latex_compile_service import LatexCompileService
from domain.models.pdf_document import PdfDocument

from logging import getLogger

logger = getLogger(__name__)


def test_generate_pdf_usecase_success(tmp_path):
    # Arrange
    dummy_pdf_path = tmp_path / "dummy.pdf"
    dummy_pdf_path.write_bytes(b"%PDF-1.4")
    dummy_pdf = PdfDocument(path=dummy_pdf_path)

    mock_service = MagicMock(spec=LatexCompileService)
    mock_service.compile.return_value = dummy_pdf

    usecase = GeneratePdfUseCase(compile_service=mock_service)
    request = CompileRequest(
        tex_content="\\documentclass{bxjsarticle}\\begin{document} Hello, world! \\end{document}",
        latexmkrc_content="$latex='xelatex %O %S';",
    )

    # Act
    result = usecase.execute(request)

    # Assert
    assert isinstance(result, ProcessResult)
    assert result.pdf_path == dummy_pdf.path
    assert "Validated TexDocument." in result.logs
    assert "Validated LatexmkrcSource." in result.logs
    assert f"Generated PDF at {dummy_pdf.path}" in result.logs
    mock_service.compile.assert_called_once()

    print(result.logs)
