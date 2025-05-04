from dataclasses import dataclass


@dataclass(frozen=True)
class CompileRequest:
    """
    DTO that will be passed to CompileUseCase.

    Attributes:
        tex_content (str): LaTeX ソースコード全体
        latexmkrc_content (str): latexmk 設定ファイルの内容
    """

    tex_content: str
    latexmkrc_content: str
