from pathlib import Path

from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import stringWidth

class BingoPdfRenderer:
    """Draw a Human Bingo page using the same layout used by the preview."""
    margin = 42
    cornerRadius = 8
    gridLineWidth = 0.8
    nameSpaceRatio = 0.50

    def __init__(self):
        self.fontRegular, self.fontBold = self._registerFonts()

    def _registerFonts(self):
        candidates = [
            (
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            ),
            (
                "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
                "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
            ),
        ]

        for regularPath, boldPath in candidates:
            if Path(regularPath).exists() and Path(boldPath).exists():
                try:
                    pdfmetrics.registerFont(TTFont("HumanBingoRegular", regularPath))
                    pdfmetrics.registerFont(TTFont("HumanBingoBold", boldPath))
                    return "HumanBingoRegular", "HumanBingoBold"
                except Exception:
                    pass

        # Helvetica is the fallback. It may not contain every French glyph
        # on every ReportLab setup, so a Unicode font is preferred above.
        return "Helvetica", "Helvetica-Bold"

    def getPageSize(self, orientation):
        if orientation == "landscape":
            return landscape(A4)
        return A4

    def renderPage(
        self,
        targetCanvas,
        grid,
        title,
        orientation,
        seed,
        outputWidth=None,
        outputHeight=None,
    ):
        pageWidth, pageHeight = self.getPageSize(orientation)

        if outputWidth is None:
            outputWidth = pageWidth
        if outputHeight is None:
            outputHeight = pageHeight

        scaleX = outputWidth / pageWidth
        scaleY = outputHeight / pageHeight

        targetCanvas.saveState()
        targetCanvas.scale(scaleX, scaleY)

        self._drawPage(
            targetCanvas,
            grid,
            title,
            seed,
            pageWidth,
            pageHeight,
        )

        targetCanvas.restoreState()

    def _drawPage(self, targetCanvas, grid, title, seed, pageWidth, pageHeight):
        gridSize = int(len(grid) ** 0.5)
        titleY = pageHeight - self.margin
        subtitleY = titleY - 27

        targetCanvas.setFillColor(colors.black)
        targetCanvas.setFont(self.fontBold, 18)
        targetCanvas.drawString(self.margin, titleY, title)

        targetCanvas.setFont(self.fontRegular, 9)
        targetCanvas.drawString(
            self.margin,
            subtitleY,
            "Find someone who:",
        )

        gridTop = subtitleY - 18
        gridBottom = self.margin + 22
        gridLeft = self.margin
        gridRight = pageWidth - self.margin
        gridWidth = gridRight - gridLeft
        gridHeight = gridTop - gridBottom

        self._drawGrid(
            targetCanvas,
            grid,
            gridSize,
            gridLeft,
            gridBottom,
            gridWidth,
            gridHeight,
        )

        targetCanvas.setFillColor(colors.HexColor("#B0B0B0"))
        targetCanvas.setFont(self.fontRegular, 7)
        targetCanvas.drawRightString(
            pageWidth - self.margin,
            self.margin - 8,
            f"Seed: {seed}",
        )

    def _drawGrid(
        self,
        targetCanvas,
        grid,
        gridSize,
        left,
        bottom,
        width,
        height,
    ):
        cellWidth = width / gridSize
        cellHeight = height / gridSize

        # Draw the grid as a group of subtly rounded cells.
        for row in range(gridSize):
            for column in range(gridSize):
                x = left + column * cellWidth
                y = bottom + (gridSize - row - 1) * cellHeight
                self._drawCell(
                    targetCanvas,
                    grid[row * gridSize + column],
                    x,
                    y,
                    cellWidth,
                    cellHeight,
                )

    def _drawCell(self, targetCanvas, proposition, x, y, width, height):
        targetCanvas.setStrokeColor(colors.HexColor("#555555"))
        targetCanvas.setLineWidth(self.gridLineWidth)
        targetCanvas.setFillColor(colors.white)

        targetCanvas.roundRect(
            x,
            y,
            width,
            height,
            self.cornerRadius,
            stroke=1,
            fill=1,
        )

        textAreaHeight = height * self.nameSpaceRatio
        propositionCenterY = y + textAreaHeight + (height - textAreaHeight) / 2

        maxTextWidth = width - 12
        maxTextHeight = height - textAreaHeight - 10

        self._drawWrappedCenteredText(
            targetCanvas,
            proposition,
            x + width / 2,
            propositionCenterY,
            maxTextWidth,
            maxTextHeight,
        )

    def _drawWrappedCenteredText(
        self,
        targetCanvas,
        text,
        centerX,
        centerY,
        maxWidth,
        maxHeight,
    ):
        fontSize = 9
        minimumFontSize = 5.5

        while fontSize >= minimumFontSize:
            lines = self._wrapText(text, self.fontRegular, fontSize, maxWidth)
            lineHeight = fontSize * 1.25

            if len(lines) * lineHeight <= maxHeight:
                break

            fontSize -= 0.5

        totalHeight = len(lines) * lineHeight
        firstBaseline = centerY + totalHeight / 2 - lineHeight

        targetCanvas.setFillColor(colors.black)
        targetCanvas.setFont(self.fontRegular, fontSize)

        for index, line in enumerate(lines):
            baseline = firstBaseline - index * lineHeight
            targetCanvas.drawCentredString(centerX, baseline, line)

    def _wrapText(self, text, fontName, fontSize, maxWidth):
        words = text.split()
        lines = []
        currentLine = ""

        for word in words:
            testLine = word if not currentLine else f"{currentLine} {word}"

            if stringWidth(testLine, fontName, fontSize) <= maxWidth:
                currentLine = testLine
            else:
                if currentLine:
                    lines.append(currentLine)
                currentLine = word

        if currentLine:
            lines.append(currentLine)

        return lines or [""]

    def exportBatch(self, grids, title, orientation, seed, outputPath):
        pageWidth, pageHeight = self.getPageSize(orientation)
        pdfCanvas = canvas.Canvas(str(outputPath), pagesize=(pageWidth, pageHeight))

        for grid in grids:
            self.renderPage(
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