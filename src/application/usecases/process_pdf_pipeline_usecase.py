from application.dto.pipeline_request import PipelineRequest
from application.dto.process_result import ProcessResult
from application.dto.compile_request import CompileRequest
from application.dto.crop_request import CropRequest
from application.dto.embed_request import EmbedRequest
from application.dto.transparency_request import TransparencyRequest
from application.usecases.generate_pdf_usecase import GeneratePdfUseCase
from application.usecases.trim_pdf_usecase import TrimPdfUseCase
from application.usecases.embed_tex_usecase import EmbedTexUseCase
from application.usecases.make_transparent_usecase import MakeTransparentUseCase


class ProcessPdfPipelineUseCase:
    def __init__(
        self,
        generate_uc: GeneratePdfUseCase,
        trim_uc: TrimPdfUseCase,
        embed_uc: EmbedTexUseCase,
        transparency_uc: MakeTransparentUseCase,
    ):
        self.generate_uc = generate_uc
        self.trim_uc = trim_uc
        self.embed_uc = embed_uc
        self.transparency_uc = transparency_uc

    def execute(self, req: PipelineRequest) -> ProcessResult:
        logs: list[str] = []

        # 1. コンパイル
        comp_req = CompileRequest(
            tex_content=req.tex_content,
            latexmkrc_content=req.latexmkrc_content
        )
        comp_res = self.generate_uc.execute(comp_req)
        logs.extend(comp_res.logs)
        if not comp_res.is_success:
            print("Compilation failed.")
            return ProcessResult(
                pdf_path="",
                logs=logs,
                is_success=False
            )

        # 2. トリミング
        crop_req = CropRequest(
            pdf_path=comp_res.pdf_path,
            margins=req.margins
        )
        crop_res = self.trim_uc.execute(crop_req)
        logs.extend(crop_res.logs)

        # 3. TeX 埋め込み
        embed_req = EmbedRequest(
            pdf_path=crop_res.pdf_path,
            embedded_files=list(req.embedded_files)
        )
        embed_res = self.embed_uc.execute(embed_req)
        logs.extend(embed_res.logs)

        # 4. 白背景透過
        transp_req = TransparencyRequest(
            pdf_path=embed_res.pdf_path
        )
        transp_res = self.transparency_uc.execute(transp_req)
        logs.extend(transp_res.logs)

        return ProcessResult(
            pdf_path=transp_res.pdf_path,
            logs=logs
        )
