import json
import random
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from generator import BingoGenerator
from pdf_export import BingoPdfRenderer
from ui.editor import PropositionEditor
from ui.preview import PreviewRenderer


class HumanBingoApp:
    """Main Tkinter application."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Human Bingo Generator")
        self.root.geometry("1480x760")
        self.root.minsize(950, 650)

        self.pdfRenderer = BingoPdfRenderer()
        self.previewRenderer = PreviewRenderer(self.pdfRenderer)

        self.generatedGrids = []
        self.currentGridIndex = 0
        self.loadedJsonPath = None

        self.titleVariable = tk.StringVar(value="Human Bingo")
        self.subTitleVariable = tk.StringVar(value="Trouve quelqu'un qui ...")
        self.gridSizeVariable = tk.IntVar(value=5)
        self.batchSizeVariable = tk.IntVar(value=10)
        self.seedVariable = tk.IntVar(value=random.randint(100000, 999999))
        self.orientationVariable = tk.StringVar(value="portrait")
        self.gridCounterVariable = tk.StringVar(value="No grids generated yet")

        self._buildInterface()
        self._loadStarterData()

    def run(self):
        self.root.mainloop()

    def _buildInterface(self):
        self._buildMenu()

        outerFrame = ttk.Frame(self.root, padding=12)
        outerFrame.pack(fill="both", expand=True)

        self._buildControls(outerFrame)

        contentFrame = ttk.PanedWindow(
            outerFrame,
            orient="horizontal",
        )
        contentFrame.pack(fill="both", expand=True, pady=(12, 0))

        previewFrame = ttk.Frame(contentFrame, padding=8)
        editorFrame = ttk.Frame(contentFrame, padding=8)

        contentFrame.add(previewFrame, weight=3)
        contentFrame.add(editorFrame, weight=2)

        self._buildPreview(previewFrame)
        self._buildEditor(editorFrame)

    def _buildMenu(self):
        menuBar = tk.Menu(self.root)

        fileMenu = tk.Menu(menuBar, tearoff=False)
        fileMenu.add_command(label="Open JSON...", command=self.openJson)
        fileMenu.add_command(label="Save JSON", command=self.saveJson)
        fileMenu.add_command(label="Save JSON As...", command=self.saveJsonAs)
        fileMenu.add_separator()
        fileMenu.add_command(label="Export PDF...", command=self.exportPdf)
        fileMenu.add_command(label="Save Batch...", command=self.saveBatch)
        fileMenu.add_separator()
        fileMenu.add_command(label="Exit", command=self.root.destroy)

        menuBar.add_cascade(label="File", menu=fileMenu)
        self.root.config(menu=menuBar)

    def _buildControls(self, parent):
        controls = ttk.LabelFrame(parent, text="Generation", padding=10)
        controls.pack(fill="x")

        ttk.Label(controls, text="Title:").grid(row=0, column=0, sticky="w")
        ttk.Entry(
            controls,
            textvariable=self.titleVariable,
            width=28,
        ).grid(row=0, column=1, padx=(5, 15), sticky="ew")

        ttk.Label(controls, text="SubTitle:").grid(row=0, column=2, sticky="w")
        ttk.Entry(
            controls,
            textvariable=self.subTitleVariable,
            width=28,
        ).grid(row=0, column=3, padx=(5, 15), sticky="ew")

        ttk.Label(controls, text="Grid size:").grid(row=0, column=4, sticky="w")
        ttk.Spinbox(
            controls,
            from_=1,
            to=50,
            textvariable=self.gridSizeVariable,
            width=6,
        ).grid(row=0, column=5, padx=(5, 15))

        ttk.Label(controls, text="Number of grids:").grid(row=0, column=6, sticky="w")
        ttk.Spinbox(
            controls,
            from_=1,
            to=1000,
            textvariable=self.batchSizeVariable,
            width=7,
        ).grid(row=0, column=7, padx=(5, 15))

        ttk.Label(controls, text="Seed:").grid(row=0, column=8, sticky="w")
        ttk.Entry(
            controls,
            textvariable=self.seedVariable,
            width=10,
        ).grid(row=0, column=9, padx=(5, 5))

        ttk.Button(
            controls,
            text="Randomize",
            command=self.randomizeSeed,
        ).grid(row=0, column=10, padx=(0, 15))

        ttk.Label(controls, text="Orientation:").grid(row=0, column=11, sticky="w")

        ttk.Radiobutton(
            controls,
            text="Portrait",
            variable=self.orientationVariable,
            value="portrait",
        ).grid(row=0, column=12, padx=3)

        ttk.Radiobutton(
            controls,
            text="Landscape",
            variable=self.orientationVariable,
            value="landscape",
        ).grid(row=0, column=13, padx=3)

        ttk.Button(
            controls,
            text="Generate",
            command=self.generate,
        ).grid(row=0, column=14, padx=(15, 3))

        self.saveBatchButton = ttk.Button(
            controls,
            text="Save Batch",
            command=self.saveBatch,
            state="disabled",
        )
        self.saveBatchButton.grid(row=0, column=15, padx=3)

        self.exportPdfButton = ttk.Button(
            controls,
            text="Export PDF",
            command=self.exportPdf,
            state="disabled",
        )
        self.exportPdfButton.grid(row=0, column=16, padx=3)

        controls.columnconfigure(1, weight=1)

    def _buildPreview(self, parent):
        ttk.Label(
            parent,
            textvariable=self.gridCounterVariable,
        ).pack(anchor="w")

        navigation = ttk.Frame(parent)
        navigation.pack(fill="x", pady=8)

        ttk.Button(
            navigation,
            text="← Previous",
            command=self.showPreviousGrid,
        ).pack(side="left")

        ttk.Button(
            navigation,
            text="Next →",
            command=self.showNextGrid,
        ).pack(side="left", padx=5)

        self.previewCanvas = tk.Canvas(
            parent,
            background="#D9D9D9",
            highlightthickness=0,
        )
        self.previewCanvas.pack(fill="both", expand=True)

        self.previewCanvas.bind(
            "<Configure>",
            lambda _event: self.refreshPreview(),
        )

    def _buildEditor(self, parent):
        ttk.Label(
            parent,
            text="Propositions",
            font=("TkDefaultFont", 12, "bold"),
        ).pack(anchor="w", pady=(0, 8))

        self.editor = PropositionEditor(
            parent,
            onChanged=self.onPropositionsChanged,
        )
        self.editor.pack(fill="both", expand=True)

    def _loadStarterData(self):
        starterPath = Path(__file__).parent.parent / "data" / "propositions.json"

        try:
            self.editor.loadJsonFile(starterPath)
        except Exception as error:
            messagebox.showwarning(
                "Could not load starter data",
                str(error),
            )

    def onPropositionsChanged(self, _propositions):
        # Generation is explicit. Editing the list does not silently replace
        # grids that the user has already generated.
        pass

    def randomizeSeed(self):
        self.seedVariable.set(random.randint(100000, 999999))

    def generate(self):
        try:
            gridSize = int(self.gridSizeVariable.get())
            batchSize = int(self.batchSizeVariable.get())
            seed = int(self.seedVariable.get())

            if seed < 0:
                raise ValueError("Seed must be a positive integer.")

            propositions = self.editor.getPropositions()

            generator = BingoGenerator(propositions)
            self.generatedGrids = generator.generateBatch(
                gridSize,
                batchSize,
                seed,
            )

            self.currentGridIndex = 0

            self.saveBatchButton.config(state="normal")
            self.exportPdfButton.config(state="normal")

            self._updateGridCounter()
            self.refreshPreview()

        except ValueError as error:
            messagebox.showerror("Cannot generate grids", str(error))

    def _updateGridCounter(self):
        if not self.generatedGrids:
            self.gridCounterVariable.set("No grids generated yet")
            return

        self.gridCounterVariable.set(
            f"Grid {self.currentGridIndex + 1} / {len(self.generatedGrids)}"
        )

    def showPreviousGrid(self):
        if not self.generatedGrids:
            return

        self.currentGridIndex = (
            self.currentGridIndex - 1
        ) % len(self.generatedGrids)

        self._updateGridCounter()
        self.refreshPreview()

    def showNextGrid(self):
        if not self.generatedGrids:
            return

        self.currentGridIndex = (
            self.currentGridIndex + 1
        ) % len(self.generatedGrids)

        self._updateGridCounter()
        self.refreshPreview()

    def refreshPreview(self):
        if not self.generatedGrids:
            return

        self.previewCanvas.delete("all")

        grid = self.generatedGrids[self.currentGridIndex]
        title = self.titleVariable.get().strip() or "Human Bingo"
        subTitle = self.subTitleVariable.get().strip() or "Find someone who ..."
        orientation = self.orientationVariable.get()
        seed = self.seedVariable.get()

        try:
            image = self.previewRenderer.render(
                self.previewCanvas,
                grid,
                title,
                subTitle,
                orientation,
                seed,
            )

            canvasWidth = self.previewCanvas.winfo_width()
            canvasHeight = self.previewCanvas.winfo_height()

            self.previewCanvas.create_image(
                canvasWidth // 2,
                canvasHeight // 2,
                image=image,
                anchor="center",
            )

        except Exception as error:
            self.previewCanvas.create_text(
                20,
                20,
                anchor="nw",
                text=(
                    "Preview unavailable.\n\n"
                    f"{error}\n\n"
                    "The PDF export remains available."
                ),
            )

    def openJson(self):
        path = filedialog.askopenfilename(
            title="Open propositions JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )

        if not path:
            return

        try:
            self.editor.loadJsonFile(path)
            self.loadedJsonPath = Path(path)
            self.root.title(
                f"Human Bingo Generator — {self.loadedJsonPath.name}"
            )

        except Exception as error:
            messagebox.showerror("Could not open JSON", str(error))

    def saveJson(self):
        if self.loadedJsonPath is None:
            self.saveJsonAs()
            return

        try:
            self.editor.saveJsonFile(self.loadedJsonPath)
            messagebox.showinfo(
                "Saved",
                f"Saved propositions to {self.loadedJsonPath.name}.",
            )
        except Exception as error:
            messagebox.showerror("Could not save JSON", str(error))

    def saveJsonAs(self):
        path = filedialog.asksaveasfilename(
            title="Save propositions JSON",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
        )

        if not path:
            return

        try:
            self.editor.saveJsonFile(path)
            self.loadedJsonPath = Path(path)
            self.root.title(
                f"Human Bingo Generator — {self.loadedJsonPath.name}"
            )
        except Exception as error:
            messagebox.showerror("Could not save JSON", str(error))

    def saveBatch(self):
        if not self.generatedGrids:
            return

        seed = self.seedVariable.get()

        path = filedialog.asksaveasfilename(
            title="Save generated batch",
            initialfile=f"{seed}.json",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
        )

        if not path:
            return

        batchData = {
            "seed": seed,
            "title": self.titleVariable.get(),
            "gridSize": int(self.gridSizeVariable.get()),
            "orientation": self.orientationVariable.get(),
            "grids": self.generatedGrids,
        }

        try:
            with open(path, "w", encoding="utf-8") as file:
                json.dump(
                    batchData,
                    file,
                    ensure_ascii=False,
                    indent=4,
                )
                file.write("\n")

            messagebox.showinfo(
                "Batch saved",
                f"Saved {len(self.generatedGrids)} grids.",
            )

        except Exception as error:
            messagebox.showerror("Could not save batch", str(error))

    def exportPdf(self):
        if not self.generatedGrids:
            return

        seed = self.seedVariable.get()

        path = filedialog.asksaveasfilename(
            title="Export Human Bingo PDF",
            initialfile=f"human_bingo_{seed}.pdf",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
        )

        if not path:
            return

        try:
            self.pdfRenderer.exportBatch(
                self.generatedGrids,
                self.titleVariable.get().strip() or "Human Bingo",
                self.subTitleVariable.get().strip() or "Trouve quelqu'un qui ...",
                self.orientationVariable.get(),
                seed,
                path,
            )

            messagebox.showinfo(
                "PDF exported",
                f"Exported {len(self.generatedGrids)} pages.",
            )

        except Exception as error:
            messagebox.showerror("Could not export PDF", str(error))
