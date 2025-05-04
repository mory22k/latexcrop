import subprocess
import tempfile
from pathlib import Path

from domain.models.tex_document import TexDocument
from domain.models.latexmkrc_source import LatexmkrcSource
from domain.models.pdf_document import PdfDocument


class LatexCompileService:
    """
    TeX ドキュメントと latexmkrc ソースを受け取り，PDF を生成するサービス
    """

    def compile(
        self,
        tex_doc: TexDocument,
        rc_source: LatexmkrcSource,
        pdf_name: str = "main.pdf",
    ) -> PdfDocument | None:
        """
        tex_doc.content を main.tex に書き出し，
        rc_source.content を latexmkrc に書き出して
        latexmk で PDF を生成し，PdfDocument を返す。

        returns:
            PdfDocument: 生成された PDF ドキュメントモデル
            RuntimeError: latexmk の実行に失敗した場合
        """
        # バリデーション
        tex_doc.validate()
        rc_source.validate()

        # 作業用ディレクトリを作成
        workdir = Path(tempfile.mkdtemp())

        # TeX ファイルを書き出し
        tex_path = workdir / "main.tex"
        tex_doc.write_to(tex_path)

        # latexmkrc ファイルを書き出し
        rc_path = rc_source.write_to(workdir)

        # latexmk 実行（-r: rc 指定）
        try:
            subprocess.run(
                ["latexmk", "--halt-on-error", "-r", str(rc_path), tex_path.name],
                cwd=workdir,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            subprocess.run(
                ["latexmk", "-c", tex_path.name],
                cwd=workdir,
                check=True,
            )
            subprocess.run(
                ["rm", "-f", str(rc_path)],
            )
            subprocess.run(
                ["rm", "-f", str(tex_path)],
            )
            raise e

        # 出力 PDF のパスを返却
        pdf_path = workdir / pdf_name
        return PdfDocument(path=pdf_path)
