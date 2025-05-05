from dataclasses import dataclass

@dataclass(frozen=True)
class ExtractResult:
    r"""
    抽出した TeX の preamble 部分と body 部分を保持する DTO。
    Attributes:
        preamble: \begin{document} より前の TeX ソース
        body:     \begin{document} と \end{document} の間の TeX 本文
    """
    preamble: str
    body: str
