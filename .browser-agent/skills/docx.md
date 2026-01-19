---
name: docx
description: Create, edit, and analyze Word documents. Use when working with .docx files for text extraction, document creation, or editing with tracked changes.
---

# DOCX Creation, Editing, and Analysis

## Overview

A .docx file is a ZIP archive containing XML files. Different tools and workflows are available for different tasks.

## Workflow Decision Tree

### Reading/Analyzing Content
Use text extraction or raw XML access

### Creating New Document
Use docx-js library (JavaScript/TypeScript)

### Editing Existing Document
- **Your own document + simple changes**: Basic OOXML editing
- **Someone else's document**: Redlining workflow (recommended)
- **Legal, academic, business, government docs**: Redlining workflow (required)

## Reading and Analyzing Content

### Text Extraction
```bash
pandoc --track-changes=all path-to-file.docx -o output.md
```

Options: `--track-changes=accept/reject/all`

### Raw XML Access
For comments, complex formatting, document structure, embedded media:

```bash
python ooxml/scripts/unpack.py <office_file> <output_directory>
```

#### Key File Structures
- `word/document.xml` - Main document contents
- `word/comments.xml` - Comments
- `word/media/` - Embedded images and media
- Tracked changes: `<w:ins>` (insertions) and `<w:del>` (deletions)

## Creating New Documents

Use **docx-js** library:

```javascript
import { Document, Packer, Paragraph, TextRun } from "docx";

const doc = new Document({
  sections: [{
    properties: {},
    children: [
      new Paragraph({
        children: [
          new TextRun("Hello World"),
          new TextRun({
            text: "Bold text",
            bold: true,
          }),
        ],
      }),
    ],
  }],
});

const buffer = await Packer.toBuffer(doc);
```

## Editing Existing Documents

### Basic Workflow
1. Unpack: `python ooxml/scripts/unpack.py <file.docx> <output_dir>`
2. Edit XML files using Document library (Python)
3. Pack: `python ooxml/scripts/pack.py <input_dir> <file.docx>`

### Redlining Workflow (Tracked Changes)

**Principle: Minimal, Precise Edits**
Only mark text that actually changes. Break replacements into: [unchanged] + [deletion] + [insertion] + [unchanged].

```python
# BAD - Replaces entire sentence
'<w:del>..entire sentence..</w:del><w:ins>..new sentence..</w:ins>'

# GOOD - Only marks what changed
'<w:r>The term is </w:r><w:del>30</w:del><w:ins>60</w:ins><w:r> days.</w:r>'
```

#### Steps
1. **Get markdown representation**:
   ```bash
   pandoc --track-changes=all file.docx -o current.md
   ```

2. **Identify and group changes** - Organize into batches of 3-10

3. **Unpack and read documentation**:
   ```bash
   python ooxml/scripts/unpack.py <file.docx> <dir>
   ```

4. **Implement changes** - Use `get_node` to find nodes, make edits, save

5. **Pack the document**:
   ```bash
   python ooxml/scripts/pack.py unpacked reviewed-document.docx
   ```

6. **Final verification**:
   ```bash
   pandoc --track-changes=all reviewed-document.docx -o verification.md
   grep "original phrase" verification.md  # Should NOT find it
   grep "replacement phrase" verification.md  # Should find it
   ```

## Converting to Images

```bash
soffice --headless --convert-to pdf document.docx
pdftoppm -jpeg -r 150 document.pdf page
```

Options:
- `-r 150`: Resolution (150 DPI)
- `-f N`: First page
- `-l N`: Last page

## Dependencies

- **pandoc**: `sudo apt-get install pandoc`
- **docx**: `npm install -g docx`
- **LibreOffice**: `sudo apt-get install libreoffice`
- **Poppler**: `sudo apt-get install poppler-utils`
- **defusedxml**: `pip install defusedxml`
