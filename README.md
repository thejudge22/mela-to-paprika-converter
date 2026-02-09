# Mela to Paprika Recipe Converter

A simple web-based tool to convert recipe files from [Mela Recipe Manager](https://mela.recipes) to [Paprika Recipe Manager](https://www.paprikaapp.com) format.

## Features

- 🌐 **Web-based UI** - Simple drag-and-drop interface
- 🌙 **Dark mode** - Toggle between light and dark themes
- 📁 **Batch conversion** - Convert multiple recipes at once
- 📦 **Large batch support** - Configurable upload limits (default 500MB)
- 🖼️ **Image support** - Preserves recipe photos
- 📋 **Complete data** - Transfers ingredients, instructions, times, categories, and more
- 🔒 **Privacy-first** - All processing happens locally, no data leaves your machine
- ⚡ **Command line** - CLI tool for scripting and automation

## Quick Start

### Option 1: Run the Web UI

1. **Clone the repository:**
   ```bash
   git clone https://github.com/thejudge22/mela-to-paprika-converter.git
   cd mela-to-paprika-converter
   ```

2. **Install dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Start the web server:**
   ```bash
   ./run.sh
   ```
   Or directly with Python:
   ```bash
   python3 app.py
   ```

4. **Open your browser** and go to `http://localhost:5000`

5. **Drag and drop** your `.melarecipe` files and click Convert!

### Configuration

You can configure the app using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_UPLOAD_MB` | 500 | Maximum total upload size in megabytes |
| `SECRET_KEY` | dev-key-change-in-production | Flask secret key (change in production) |
| `FLASK_PORT` | 5000 | Port to run the Flask server on |

**Example with increased limit:**
```bash
MAX_UPLOAD_MB=1000 python3 app.py
```

### Option 2: Command Line Usage

Convert a single file:
```bash
python3 convert.py path/to/recipe.melarecipe
```

Convert all files in a directory:
```bash
python3 convert.py path/to/mela/recipes/
```

The converted `.paprikarecipes` file will be created in the current directory.

## File Format Mapping

| Mela Field | Paprika Field | Notes |
|------------|---------------|-------|
| `title` | `name` | Recipe title |
| `text` | (description) | Short description |
| `ingredients` | `ingredients` | Newline-separated list |
| `instructions` | `directions` | Newline-separated steps |
| `prepTime` | `prep_time` | Preparation time |
| `cookTime` | `cook_time` | Cooking time |
| `totalTime` | `total_time` | Total time |
| `yield` | `servings` | Number of servings |
| `notes` | `notes` | Recipe notes |
| `nutrition` | `nutritional_info` | Nutrition information |
| `categories` | `categories` | Array of category names |
| `link` | `source_url` | Original source URL |
| `images` | `photo_data` | Base64-encoded image |

## Output Format

The converter creates `.paprikarecipes` files, which are ZIP archives containing:
- One `.paprikarecipe` file per recipe (gzipped JSON)
- All recipe data including images

## Importing into Paprika

1. **Download** the converted `.paprikarecipes` file from the web UI
2. **Transfer** it to your iOS/Android device via email, cloud storage, or AirDrop
3. **Open** the file and select "Open in Paprika", or use Paprika's Import feature
4. Your recipes will be imported with all their details, including images

## Web UI Features

### Drag & Drop Upload
- Drop one or multiple `.melarecipe` files onto the upload area
- See file sizes and total batch size before converting
- Progress indicator shows upload/conversion status

### Dark Mode
- Toggle between light and dark themes using the ☀️/🌙 button in the header
- Your preference is saved automatically

### Error Handling
- Clear error messages if files are too large or invalid
- 500MB default limit (configurable)
- Friendly 413 error page with suggestions

## API Endpoints

The web UI also exposes JSON API endpoints:

### POST `/api/convert`
Convert files and return download URL.
```bash
curl -X POST -F "files=@recipe.melarecipe" http://localhost:5000/api/convert
```

### POST `/api/preview`
Preview a recipe conversion without downloading.
```bash
curl -X POST -F "file=@recipe.melarecipe" http://localhost:5000/api/preview
```

### GET `/config`
Get current configuration (upload limits, etc.).
```bash
curl http://localhost:5000/config
```

## Project Structure

```
.
├── app.py              # Flask web application
├── convert.py          # Core conversion logic (CLI)
├── requirements.txt    # Python dependencies
├── run.sh              # Convenience startup script
├── README.md           # Documentation
├── .gitignore          # Git ignore file
└── templates/          # HTML templates
    ├── base.html       # Base template with dark mode
    ├── index.html      # Upload page
    └── success.html    # Download page
```

## Requirements

- Python 3.8+
- Flask 2.0+ (for web UI)

## Troubleshooting

### "Request Entity Too Large" (413 Error)

The default upload limit is 500MB. If you need more:

1. **Use the environment variable:**
   ```bash
   MAX_UPLOAD_MB=1000 python3 app.py
   ```

2. **Or upload in smaller batches** - Select fewer files at once

### Conversion Failed

- Ensure files are valid `.melarecipe` JSON files
- Check that files aren't corrupted
- Try converting a single file first to isolate the issue

### Images Not Appearing in Paprika

- Mela stores images as base64 data which should transfer correctly
- Large images may take longer to process
- Verify the original Mela file has image data

## Credits

- Inspired by [recipe-to-paprika](https://github.com/neurotictoaster/recipe-to-paprika)
- Built for [Mela](https://mela.recipes) and [Paprika](https://www.paprikaapp.com) recipe managers

---

**Enjoy your converted recipes! 🍳**
