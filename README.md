# 📦 Zip2Read

> A utility tool for extracting source code from ZIP archives and generating structured Markdown dumps.

> Modern GUI, interactive navigation, and flexible extension filtering.

---

## ✨ Features
- 🎯 **Smart filtering** — automatically skips binary files (`.png`, `.mp4`, `.exe`, `.blend`, `.pdf`, etc.)
- 🌐 **Language statistics** — table with code breakdown, number of files, and percentage share
- 🗺️ **Interactive file maps** — separate trees for code and binaries with clickable HTML anchors
- 🎨 **Stylish GUI** — sidebar navigation, drag&drop, hidden progress bar, custom QSS styles
- ⚙️ **Flexible presets** — manage extensions via JSON configs (created automatically)
- 🛡️ **Fault tolerance** — smooth skipping of broken/undecoded files without Process interrupts
- 💾 **Convenient output** — autosave to `~/Documents/Zip2Read/`

---

## 📦 Installation and Run

### Requirements
- Python 3.10+
- OS: Windows / macOS / Linux

---

## Usage
1. **Select archive**: Drag `.zip` into the window area or click "Select archive"
2. **Configure preset**: Select an extension configuration from the drop-down list
3. **Extract**: Click "Extract to Markdown" → the progress will be displayed automatically
4. **Open result**: The file will appear in `Documents/Zip2Read/` and open in any MD editor (VS Code, Obsidian, Typora, GitHub)

---

## 📄 Configuring extension presets
When you first launch the project, a `presets/` folder with `default.json` is automatically created in the project root.

You can add your own configurations to this folder – they will be instantly added to the interface.

**Example `presets/web.json`:**
```json
{
"extensions": [".html", ".css", ".js", ".ts", ".json", ".xml", ".svg"]
}
```
> 💡 Extensions are specified **with a period**. The list is checked for lowercase.

---

## 📝 Output Format: Markdown
```markdown
---
archive_name: project.zip
extraction_date: 2026-05-01 14:32:10
total_files: 142
code_percentage: 68.31%
code_files: 97
binary_files: 41
other_files: 4
---

# 📊 Archive Analysis
- **Code**: 97 files (68.31%)
...

# 🌐 Language Statistics
| Language | Files | Percentage of Code |
|---|---|---|
| python | 42 | 43.3% |
...

# 🗺️ Code Map
- [📄 `src/main.py`](#src-main-py)
...

# 🗺️ Binary/Other File Map
- [🗃️ `assets/icon.png`](#assets-icon-png)
...

# 📦 File Contents
### <a id="src-main-py"></a> 📄 `src/main.py`
```python
import sys
...
```
