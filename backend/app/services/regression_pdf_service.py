from __future__ import annotations

import base64
from pathlib import Path

from app.core.exceptions import BadRequest
from app.schemas.descriptive import LassoPlotPayload


def export_lasso_plot_pdf(plot: LassoPlotPayload) -> tuple[bytes, str]:
    if not (plot.vector_pdf_base64 or "").strip():
        raise BadRequest("当前结果未包含矢量 PDF，请重新运行分析后再导出。")

    try:
        pdf_bytes = base64.b64decode(plot.vector_pdf_base64, validate=True)
    except (ValueError, TypeError) as exc:
        raise BadRequest("矢量 PDF 内容无效，无法导出。") from exc

    filename = plot.vector_pdf_filename or f"{Path(plot.filename).stem or 'plot'}.pdf"
    return pdf_bytes, filename
