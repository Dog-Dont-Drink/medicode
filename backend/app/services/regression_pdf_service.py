from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from app.core.exceptions import BadRequest
from app.schemas.descriptive import LassoPlotPayload


def export_lasso_plot_pdf(plot: LassoPlotPayload) -> tuple[bytes, str]:
    if not plot.content_base64.strip():
        raise BadRequest("LASSO 图像内容为空，无法导出 PDF")

    try:
        image_bytes = base64.b64decode(plot.content_base64, validate=True)
    except (ValueError, TypeError) as exc:
        raise BadRequest("LASSO 图像内容无效，无法导出 PDF") from exc

    try:
        image_reader = ImageReader(BytesIO(image_bytes))
        image_width, image_height = image_reader.getSize()
    except Exception as exc:  # reportlab/pillow raises multiple image decoding errors
        raise BadRequest("LASSO 图像解码失败，无法导出 PDF") from exc

    page_size = landscape(A4) if image_width >= image_height else A4
    page_width, page_height = page_size
    margin = 36
    scale = min((page_width - margin * 2) / image_width, (page_height - margin * 2) / image_height)
    draw_width = image_width * scale
    draw_height = image_height * scale
    draw_x = (page_width - draw_width) / 2
    draw_y = (page_height - draw_height) / 2

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=page_size)
    pdf.setTitle(Path(plot.filename).stem or "lasso-plot")
    pdf.drawImage(image_reader, draw_x, draw_y, draw_width, draw_height, preserveAspectRatio=True, mask="auto")
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer.read(), f"{Path(plot.filename).stem or 'lasso-plot'}.pdf"
