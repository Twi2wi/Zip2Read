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

### Quick Start
```bash
# 1. Clone or unzip the repository
git clone https://github.com/yourusername/Zip2Read.git
cd Zip2Read

# 2. Create and activate the virtual environment
python -m venv .venv
.venv\Scripts\activate # Windows
# source .venv/bin/activate # macOS / Linux

# 3. Install dependencies
pip install PyQt6

# 4. Run the application
python main.py
```

---

## 🚀 Usage
1. **Select archive**: Drag `.zip` into the window area or click "Select archive"
2. **Configure preset**: Select an extension configuration from the drop-down list
3. **Extract**: Click "Extract to Markdown" → the progress will be displayed automatically
4. **Open result**: The file will appear in `Documents/Zip2Read/` and open in any MD editor (VS Code, Obsidian, Typora, GitHub)

---

## 🏗️ Project architecture
```text
Zip2Read/
├── main.py # Entry point, global styles
├── styles.py # QSS theme (palette, widgets, animations)
├── Zip2Read.spec # PyInstaller configuration
├── core/ # Business logic
│ ├── config_manager.py # Loading/creating JSON presets
│ └── extractor.py # ZIP parsing, filtering, MD generation
├── ui/ # Interface
│ ├── main_window.py # Framework, sidebar, page routing
│ ├── worker_thread.py # Background QThread (without GUI freezes)
│ └── pages/
│ ├── extract_page.py # Extraction tab
│ └── info_page.py # About tab
└── utils/
└── version.py # Version and metadata management
```

---

## 🛠️ EXE build (Windows/macOS/Linux)
```bash
pip install pyinstaller
pyinstaller Zip2Read.spec
```
✅ The finished bundle will appear in the `dist/Zip2Read/` folder.
📦 The `onedir` mode ensures stable PyQt6 launch without library archiving issues.

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
```

---

## 🤝 License
Distributed under the [MIT](LICENSE).

Use freely, modify, share. The author is not responsible for use in production environments.

---

## 💖 Support
Found a bug? Want to add a dark theme, batch processing, or MD previews?

Open an issue or write in Discussion—we'll put the feature together in a single commit. 🛠️✨

> *"Code should be as easy to read as a good book. Zip2Read helps turn an archive into a page."*
