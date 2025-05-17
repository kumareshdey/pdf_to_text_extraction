# PDF to Text Extractor

A user-friendly desktop application for extracting text from PDF files and exporting the results to text files. The tool supports basic and advanced extraction modes, with optional spellchecking, and provides a graphical interface for ease of use.

## Features

- Extracts text from PDF files using multiple backends (PyPDF2, PyMuPDF, EasyOCR).
- Supports both basic (fast) and advanced (accurate) extraction modes.
- Optional spellchecking using TextBlob.
- Simple graphical user interface (GUI) built with Tkinter.
- Progress bar and logging area for real-time feedback.
- Handles errors gracefully and provides helpful messages.
- Automatically installs Poppler if not present (for advanced PDF processing).

## Installation

1. **Clone the repository**  
   ```sh
   git clone <your-repo-url>
   cd pdf_to_text_extractor
   ```

2. **Install dependencies**  
   It is recommended to use a virtual environment.
   ```sh
   pip install -r requirements.txt
   ```

3. **(Windows only) Poppler**  
   The application will attempt to install Poppler automatically if not found.

## Usage

Run the application with:

```sh
python ui.py
```

- Select the source PDF file.
- Choose the destination folder for the extracted text.
- Select extraction options (basic/advanced, spellcheck).
- Click "Submit" to start extraction.

The extracted text will be saved as a `.txt` file in the chosen destination folder.

## File Structure

| File                       | Description                                      |
|----------------------------|--------------------------------------------------|
| `ui.py`                    | Main GUI application                             |
| `full_implementation_1.py` | Core logic for PDF text extraction               |
| `poppler_installer.py`     | Handles Poppler installation (Windows)           |
| `requirements.txt`         | Python dependencies                              |
| `ui.spec`                  | PyInstaller spec for building an executable      |

## Building an Executable

To create a standalone executable (Windows):

```sh
pip install pyinstaller
pyinstaller ui.spec
```

## Requirements

- Python 3.7+
- See [requirements.txt](requirements.txt) for full list

## License

MIT License

---

**Developed by [Your Name/Team]**