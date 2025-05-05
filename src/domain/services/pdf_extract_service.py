import pikepdf
from domain.models.pdf_document import PdfDocument
from domain.models.embedded_file import EmbeddedFile

class PdfExtractService:
    """
    Service to extract all embedded .tex files from a PDF.
    """

    def extract(self, pdf_doc: PdfDocument) -> list[EmbeddedFile]:
        """
        Args:
            pdf_doc: 検証済みの PdfDocument
        Returns:
            埋め込まれた .tex ファイルを EmbeddedFile リストで返却
        """
        pdf_doc.validate()
        pdf = pikepdf.Pdf.open(pdf_doc.path)
        extracted: list[EmbeddedFile] = []
        for name, filespec in pdf.attachments.items():
            if name.lower().endswith(".tex"):
                attached = filespec.get_file()
                data = attached.read_bytes()
                extracted.append(EmbeddedFile(name=name, data=data))
        pdf.close()
        return extracted
