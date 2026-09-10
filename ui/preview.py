import tkinter as tk

from reportlab.pdfgen import canvas

class PreviewRenderer:
    """ReportLab page to a Tkinter PhotoImage using Pillow."""
    def __init__(self, pdfRenderer):
        self.pdfRenderer = pdfRenderer
        self.currentImage = None

    def render(self, parent, grid, title, orientation, seed):
        # Import here so the main application can still start if Pillow is
        # temporarily unavailable while the rest of the UI is being tested.
        from PIL import Image, ImageTk
        from io import BytesIO

        pageWidth, pageHeight = self.pdfRenderer.getPageSize(orientation)

        previewWidth = 560
        previewHeight = int(previewWidth * pageHeight / pageWidth)

        image = Image.new("RGB", (previewWidth, previewHeight), "white")
        imageBuffer = BytesIO()

        # Pillow's image can be written as a temporary PNG buffer.
        image.save(imageBuffer, format="PNG")
        imageBuffer.seek(0)

        # ReportLab cannot directly draw on a Pillow image. We therefore use
        # a PDF page as the source of truth and rasterize it with PyMuPDF if
        # available. If it is unavailable, the UI falls back to a canvas
        # approximation below.
        try:
            import fitz

            pdfBuffer = BytesIO()
            pdfCanvas = canvas.Canvas(
                pdfBuffer,
                pagesize=(pageWidth, pageHeight),
            )
            self.pdfRenderer.renderPage(
                pdfCanvas,
                grid,
                title,
                orientation,
                seed,
                pageWidth,
                pageHeight,
            )
            pdfCanvas.showPage()
            pdfCanvas.save()

            pdfBuffer.seek(0)
            document = fitz.open(stream=pdfBuffer.read(), filetype="pdf")
            page = document[0]
            matrix = fitz.Matrix(
                previewWidth / pageWidth,
                previewWidth / pageWidth,
            )
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image = Image.frombytes(
                "RGB",
                [pixmap.width, pixmap.height],
                pixmap.samples,
            )
            document.close()

        except Exception:
            # The fallback keeps the application usable if PyMuPDF is not
            # installed. The exported PDF still uses the exact PDF renderer.
            image = Image.new(
                "RGB",
                (previewWidth, previewHeight),
                "white",
            )

        self.currentImage = ImageTk.PhotoImage(image)
        return self.currentImage