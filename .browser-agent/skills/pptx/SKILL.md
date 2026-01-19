---
name: pptx
description: Create, edit, and analyze PowerPoint presentations. Use when working with .pptx files for text extraction, slide creation, or presentation editing.
---

# PPTX Creation, Editing, and Analysis

## Overview

A .pptx file is a ZIP archive containing XML files. Different tools and workflows are available for different tasks.

## Reading and Analyzing Content

### Text Extraction
```bash
python -m markitdown path-to-file.pptx
```

### Raw XML Access
For comments, speaker notes, slide layouts, animations, design elements:

```bash
python ooxml/scripts/unpack.py <office_file> <output_dir>
```

#### Key File Structures
- `ppt/presentation.xml` - Main presentation metadata
- `ppt/slides/slide{N}.xml` - Individual slide contents
- `ppt/notesSlides/notesSlide{N}.xml` - Speaker notes
- `ppt/comments/` - Comments
- `ppt/slideLayouts/` - Layout templates
- `ppt/slideMasters/` - Master templates
- `ppt/theme/` - Theme and styling
- `ppt/media/` - Images and media

## Creating New Presentations

Use html2pptx workflow for creating from scratch.

### Design Principles

1. **Consider subject matter** - What tone/mood does it suggest?
2. **Check for branding** - Consider brand colors
3. **Match palette to content** - Select appropriate colors
4. **State your approach** - Explain design choices before coding

### Requirements
- Use web-safe fonts: Arial, Helvetica, Times New Roman, Georgia, Verdana, Tahoma
- Create clear visual hierarchy
- Ensure readability with strong contrast
- Be consistent across slides

### Layout Tips
- **Two-column layout (preferred)**: Header spanning full width, then text + chart columns
- **Full-slide layout**: Let featured content take entire slide
- **NEVER vertically stack** charts below text

### Workflow
1. Create HTML file for each slide (720pt × 405pt for 16:9)
2. Use `html2pptx.js` library to convert
3. Add charts/tables using PptxGenJS API
4. Generate thumbnails and validate visually

## Editing Existing Presentations

Use OOXML format editing:

1. Unpack: `python ooxml/scripts/unpack.py <file.pptx> <dir>`
2. Edit XML files (primarily `ppt/slides/slide{N}.xml`)
3. Validate: `python ooxml/scripts/validate.py <dir> --original <file>`
4. Pack: `python ooxml/scripts/pack.py <dir> <output.pptx>`

## Using Templates

1. **Extract template text and thumbnails**:
   ```bash
   python -m markitdown template.pptx > template-content.md
   python scripts/thumbnail.py template.pptx
   ```

2. **Analyze template** - Create inventory of slide layouts

3. **Create presentation outline** - Map content to templates

4. **Rearrange slides**:
   ```bash
   python scripts/rearrange.py template.pptx working.pptx 0,34,34,50,52
   ```

5. **Extract text inventory**:
   ```bash
   python scripts/inventory.py working.pptx text-inventory.json
   ```

6. **Generate replacement text** - Create `replacement-text.json`

7. **Apply replacements**:
   ```bash
   python scripts/replace.py working.pptx replacement-text.json output.pptx
   ```

## Creating Thumbnail Grids

```bash
python scripts/thumbnail.py template.pptx [output_prefix]
```

Options:
- `--cols 4` - Adjust columns (3-6)
- Default: 5 columns, max 30 slides per grid

## Converting to Images

```bash
soffice --headless --convert-to pdf template.pptx
pdftoppm -jpeg -r 150 template.pdf slide
```

## Dependencies

- **markitdown**: `pip install "markitdown[pptx]"`
- **pptxgenjs**: `npm install -g pptxgenjs`
- **playwright**: `npm install -g playwright`
- **sharp**: `npm install -g sharp`
- **LibreOffice**: `sudo apt-get install libreoffice`
- **Poppler**: `sudo apt-get install poppler-utils`
