import json
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk


class PropositionEditor(ttk.Frame):
    """Two synchronized ways to edit the proposition list."""

    def __init__(self, parent, onChanged):
        super().__init__(parent)
        self.onChanged = onChanged
        self.propositions = []
        self.currentMode = "list"

        self._buildToolbar()
        self._buildEditors()

    def _buildToolbar(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=(0, 8))

        ttk.Label(toolbar, text="Editing mode:").pack(side="left")

        self.modeVariable = tk.StringVar(value="list")
        modeBox = ttk.Combobox(
            toolbar,
            textvariable=self.modeVariable,
            values=["list", "JSON"],
            state="readonly",
            width=10,
        )
        modeBox.pack(side="left", padx=8)
        modeBox.bind("<<ComboboxSelected>>", self._switchMode)

        ttk.Button(
            toolbar,
            text="Validate / Apply",
            command=self.applyCurrentEditor,
        ).pack(side="right")

    def _buildEditors(self):
        self.editorContainer = ttk.Frame(self)
        self.editorContainer.pack(fill="both", expand=True)

        self._buildListEditor()
        self._buildJsonEditor()

        self.listEditor.pack(fill="both", expand=True)

    def _buildListEditor(self):
        self.listEditor = ttk.Frame(self.editorContainer)

        self.listBox = tk.Listbox(
            self.listEditor,
            selectmode=tk.SINGLE,
        )
        self.listBox.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(
            self.listEditor,
            orient="vertical",
            command=self.listBox.yview,
        )
        scrollbar.pack(side="left", fill="y")
        self.listBox.config(yscrollcommand=scrollbar.set)

        buttons = ttk.Frame(self.listEditor)
        buttons.pack(side="left", fill="y", padx=(8, 0))

        ttk.Button(buttons, text="Add", command=self.addProposition).pack(fill="x", pady=2)
        ttk.Button(buttons, text="Edit", command=self.editProposition).pack(fill="x", pady=2)
        ttk.Button(buttons, text="Delete", command=self.deleteProposition).pack(fill="x", pady=2)
        ttk.Button(buttons, text="Up", command=lambda: self.moveProposition(-1)).pack(fill="x", pady=2)
        ttk.Button(buttons, text="Down", command=lambda: self.moveProposition(1)).pack(fill="x", pady=2)

    def _buildJsonEditor(self):
        self.jsonEditor = ttk.Frame(self.editorContainer)

        self.jsonText = tk.Text(
            self.jsonEditor,
            wrap="word",
            undo=True,
        )
        self.jsonText.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(
            self.jsonEditor,
            orient="vertical",
            command=self.jsonText.yview,
        )
        scrollbar.pack(side="left", fill="y")
        self.jsonText.config(yscrollcommand=scrollbar.set)

    def setPropositions(self, propositions):
        self.propositions = list(propositions)
        self._refreshList()
        self._refreshJson()

    def getPropositions(self):
        return list(self.propositions)

    def _refreshList(self):
        self.listBox.delete(0, tk.END)
        for proposition in self.propositions:
            self.listBox.insert(tk.END, proposition)

    def _refreshJson(self):
        jsonValue = json.dumps(
            self.propositions,
            ensure_ascii=False,
            indent=4,
        )
        self.jsonText.delete("1.0", tk.END)
        self.jsonText.insert("1.0", jsonValue)

    def _switchMode(self, _event=None):
        selectedMode = self.modeVariable.get()

        if selectedMode == self.currentMode:
            return

        if not self._applyEditorSilently():
            self.modeVariable.set(self.currentMode)
            return

        self.currentMode = selectedMode

        self.listEditor.pack_forget()
        self.jsonEditor.pack_forget()

        if selectedMode == "list":
            self.listEditor.pack(fill="both", expand=True)
        else:
            self.jsonEditor.pack(fill="both", expand=True)

    def _applyEditorSilently(self):
        try:
            if self.currentMode == "JSON":
                rawValue = self.jsonText.get("1.0", tk.END).strip()
                parsed = json.loads(rawValue)

                if not isinstance(parsed, list):
                    raise ValueError("The JSON root must be a list.")

                if not all(isinstance(item, str) for item in parsed):
                    raise ValueError("Every proposition must be a string.")

                self.propositions = [
                    item.strip() for item in parsed if item.strip()
                ]
                self._refreshList()
            else:
                self.propositions = list(self.listBox.get(0, tk.END))
                self._refreshJson()

            self.onChanged(self.propositions)
            return True

        except (json.JSONDecodeError, ValueError) as error:
            messagebox.showerror("Invalid JSON", str(error))
            return False

    def applyCurrentEditor(self):
        self._applyEditorSilently()

    def addProposition(self):
        value = simpledialog.askstring(
            "Add proposition",
            "Proposition:",
            parent=self,
        )

        if value and value.strip():
            self.propositions.append(value.strip())
            self._refreshList()
            self._refreshJson()
            self.onChanged(self.propositions)

    def editProposition(self):
        selection = self.listBox.curselection()
        if not selection:
            return

        index = selection[0]
        value = simpledialog.askstring(
            "Edit proposition",
            "Proposition:",
            initialvalue=self.propositions[index],
            parent=self,
        )

        if value and value.strip():
            self.propositions[index] = value.strip()
            self._refreshList()
            self._refreshJson()
            self.onChanged(self.propositions)

    def deleteProposition(self):
        selection = self.listBox.curselection()
        if not selection:
            return

        index = selection[0]
        del self.propositions[index]

        self._refreshList()
        self._refreshJson()
        self.onChanged(self.propositions)

    def moveProposition(self, direction):
        selection = self.listBox.curselection()
        if not selection:
            return

        index = selection[0]
        newIndex = index + direction

        if newIndex < 0 or newIndex >= len(self.propositions):
            return

        self.propositions[index], self.propositions[newIndex] = (
            self.propositions[newIndex],
            self.propositions[index],
        )

        self._refreshList()
        self.listBox.selection_set(newIndex)
        self._refreshJson()
        self.onChanged(self.propositions)

    def loadJsonFile(self, path):
        with open(path, "r", encoding="utf-8") as file:
            parsed = json.load(file)

        if not isinstance(parsed, list):
            raise ValueError("The JSON root must be a list.")

        if not all(isinstance(item, str) for item in parsed):
            raise ValueError("Every proposition must be a string.")

        self.setPropositions([
            item.strip() for item in parsed if item.strip()
        ])

    def saveJsonFile(self, path):
        self._applyEditorSilently()

        with open(path, "w", encoding="utf-8") as file:
            json.dump(
                self.propositions,
                file,
                ensure_ascii=False,
                indent=4,
            )
            file.write("\n")
