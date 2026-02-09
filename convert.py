#!/usr/bin/env python3
"""
Mela to Paprika Recipe Converter

Converts .melarecipe files to .paprikarecipes format.
"""

import gzip
import json
import os
import re
import shutil
import uuid
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any


def clean_text(text: str | None) -> str:
    """Clean and normalize text."""
    if not text:
        return ""
    return text.strip()


def parse_time(time_str: str | None) -> str:
    """Parse time string and format for Paprika."""
    if not time_str:
        return ""
    return time_str.strip()


def generate_uid() -> str:
    """Generate a unique identifier for Paprika."""
    return str(uuid.uuid4()).upper()


def mela_to_paprika(mela_data: dict) -> dict:
    """
    Convert a Mela recipe dictionary to Paprika format.
    
    Mela fields:
    - link, totalTime, notes, nutrition, cookTime, ingredients
    - favorite, instructions, categories, prepTime, images
    - title, text, yield (from spec, though may vary in actual files)
    
    Paprika fields:
    - uid, name, ingredients, directions, servings, prep_time, cook_time
    - total_time, notes, nutritional_info, categories, rating, difficulty
    - source, source_url, created, image_url, photo_hash, photo, photo_data
    """
    
    # Get recipe name - Mela uses 'title' but some exported files may use link-derived names
    name = clean_text(mela_data.get("title", ""))
    if not name:
        # Try to derive from link
        link = mela_data.get("link", "")
        if link:
            # Extract last part of URL path as name
            name = link.rstrip("/").split("/")[-1].replace("-", " ").replace("_", " ").title()
        else:
            name = "Untitled Recipe"
    
    # Get description (Mela's 'text' field is the short description)
    description = clean_text(mela_data.get("text", ""))
    
    # Build Paprika recipe structure
    paprika_recipe = {
        "uid": generate_uid(),
        "name": name,
        "ingredients": clean_text(mela_data.get("ingredients", "")),
        "directions": clean_text(mela_data.get("instructions", "")),
        "servings": clean_text(mela_data.get("yield", "")),
        "prep_time": parse_time(mela_data.get("prepTime")),
        "cook_time": parse_time(mela_data.get("cookTime")),
        "total_time": parse_time(mela_data.get("totalTime")),
        "notes": clean_text(mela_data.get("notes", "")),
        "nutritional_info": clean_text(mela_data.get("nutrition", "")),
        "categories": mela_data.get("categories", []) or [],
        "rating": 0,
        "difficulty": None,
        "source": clean_text(mela_data.get("link", "")),
        "source_url": clean_text(mela_data.get("link", "")),
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "image_url": None,
        "photo_hash": None,
        "photo": None,
    }
    
    # Handle images - Mela stores as array of base64 strings
    images = mela_data.get("images", [])
    if images and len(images) > 0:
        # Use the first image as the main photo
        paprika_recipe["photo_data"] = images[0]
    
    return paprika_recipe


def read_mela_file(filepath: Path) -> dict | None:
    """Read and parse a .melarecipe file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error parsing {filepath}: {e}")
        return None
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None


def create_paprika_file(recipe: dict, output_dir: Path) -> Path:
    """
    Create a single .paprikarecipe file (gzipped JSON).
    
    Returns the path to the created file.
    """
    # Create safe filename from recipe name
    safe_name = re.sub(r'[^\w\s-]', '', recipe["name"]).strip().replace(" ", "_")
    if not safe_name:
        safe_name = "recipe"
    
    paprika_filename = f"{safe_name}.paprikarecipe"
    output_path = output_dir / paprika_filename
    
    # Convert to JSON string
    recipe_json = json.dumps(recipe, ensure_ascii=False)
    
    # Gzip the JSON
    with gzip.open(output_path, 'wt', encoding='utf-8') as f:
        f.write(recipe_json)
    
    return output_path


def create_paprika_bundle(paprika_files: list[Path], output_dir: Path, bundle_name: str | None = None) -> Path:
    """
    Create a .paprikarecipes bundle (ZIP file containing .paprikarecipe files).
    
    Args:
        paprika_files: List of .paprikarecipe file paths
        output_dir: Directory to save the bundle
        bundle_name: Optional name for the bundle (without extension)
    
    Returns:
        Path to the created bundle file
    """
    if not bundle_name:
        if len(paprika_files) == 1:
            # Use the recipe name
            bundle_name = paprika_files[0].stem
        else:
            # Use timestamp
            bundle_name = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    bundle_filename = f"{bundle_name}.paprikarecipes"
    bundle_path = output_dir / bundle_filename
    
    # Create ZIP file
    with zipfile.ZipFile(bundle_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for paprika_file in paprika_files:
            zf.write(paprika_file, arcname=paprika_file.name)
    
    return bundle_path


def convert_mela_to_paprika(input_path: Path, output_dir: Path | None = None) -> Path | None:
    """
    Convert Mela recipe file(s) to Paprika format.
    
    Args:
        input_path: Path to a .melarecipe file or directory containing them
        output_dir: Directory for output (defaults to current directory)
    
    Returns:
        Path to the created .paprikarecipes bundle, or None if conversion failed
    """
    if output_dir is None:
        output_dir = Path.cwd()
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create temporary directory for intermediate files
    temp_dir = output_dir / ".temp"
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # Collect all melarecipe files
        mela_files = []
        if input_path.is_file():
            if input_path.suffix == ".melarecipe":
                mela_files.append(input_path)
            else:
                print(f"Error: {input_path} is not a .melarecipe file")
                return None
        elif input_path.is_dir():
            mela_files = list(input_path.glob("*.melarecipe"))
            if not mela_files:
                print(f"No .melarecipe files found in {input_path}")
                return None
        else:
            print(f"Error: {input_path} does not exist")
            return None
        
        print(f"Found {len(mela_files)} Mela recipe file(s)")
        
        # Convert each Mela file to Paprika format
        paprika_files = []
        for mela_file in mela_files:
            print(f"Converting: {mela_file.name}")
            
            mela_data = read_mela_file(mela_file)
            if mela_data is None:
                continue
            
            paprika_recipe = mela_to_paprika(mela_data)
            paprika_file = create_paprika_file(paprika_recipe, temp_dir)
            paprika_files.append(paprika_file)
            print(f"  -> Created: {paprika_file.name}")
        
        if not paprika_files:
            print("No recipes were successfully converted")
            return None
        
        # Create the final bundle
        bundle_path = create_paprika_bundle(paprika_files, output_dir)
        print(f"\n✅ Created Paprika bundle: {bundle_path.name}")
        print(f"   Location: {bundle_path.absolute()}")
        
        return bundle_path
        
    finally:
        # Clean up temporary files
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python convert.py <path_to_melarecipe_file_or_directory>")
        print("\nExamples:")
        print("  python convert.py recipe.melarecipe")
        print("  python convert.py /path/to/mela/recipes/")
        sys.exit(1)
    
    input_path = Path(sys.argv[1])
    result = convert_mela_to_paprika(input_path)
    
    if result:
        print(f"\nYou can now import '{result.name}' into Paprika!")
    else:
        print("\n❌ Conversion failed")
        sys.exit(1)
