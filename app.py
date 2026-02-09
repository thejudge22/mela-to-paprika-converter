#!/usr/bin/env python3
"""
Mela to Paprika Recipe Converter - Web UI

A simple web interface for converting .melarecipe files to .paprikarecipes format.
"""

import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, send_file, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from convert import convert_mela_to_paprika, read_mela_file, mela_to_paprika

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

# Maximum upload size: 500MB (increased from 50MB to handle many recipe files with images)
# Set via environment variable or default to 500MB
MAX_UPLOAD_MB = int(os.environ.get('MAX_UPLOAD_MB', 500))
app.config['MAX_CONTENT_LENGTH'] = MAX_UPLOAD_MB * 1024 * 1024

# Configuration
UPLOAD_FOLDER = Path(tempfile.gettempdir()) / 'mela_to_paprika_uploads'
UPLOAD_FOLDER.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {'melarecipe'}


def allowed_file(filename):
    """Check if file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')


@app.route('/convert', methods=['POST'])
def convert():
    """Handle file upload and conversion."""
    
    # Check if files were uploaded
    if 'files' not in request.files:
        flash('No files selected', 'error')
        return redirect(url_for('index'))
    
    files = request.files.getlist('files')
    
    # Filter out empty files
    files = [f for f in files if f.filename]
    
    if not files:
        flash('No files selected', 'error')
        return redirect(url_for('index'))
    
    # Validate all files have correct extension
    invalid_files = [f.filename for f in files if not allowed_file(f.filename)]
    if invalid_files:
        flash(f'Invalid file type(s): {", ".join(invalid_files)}. Only .melarecipe files are allowed.', 'error')
        return redirect(url_for('index'))
    
    # Create a unique session folder for this conversion
    session_id = str(uuid.uuid4())
    session_folder = UPLOAD_FOLDER / session_id
    session_folder.mkdir(exist_ok=True)
    
    try:
        # Save uploaded files
        saved_files = []
        for file in files:
            filename = secure_filename(file.filename)
            filepath = session_folder / filename
            file.save(filepath)
            saved_files.append(filepath)
        
        # Perform conversion
        output_path = convert_mela_to_paprika(session_folder, session_folder)
        
        if output_path is None:
            flash('Conversion failed. Please check that your .melarecipe files are valid.', 'error')
            return redirect(url_for('index'))
        
        # Move the output file to a predictable name for download
        download_name = f"Paprika_Recipes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.paprikarecipes"
        download_path = session_folder / download_name
        output_path.rename(download_path)
        
        # Store the download path in session (using a simple dict for demo)
        download_sessions[session_id] = {
            'path': str(download_path),
            'filename': download_name,
            'created': datetime.now().isoformat()
        }
        
        # Redirect to success page with download link
        return redirect(url_for('success', session_id=session_id, filename=download_name))
        
    except Exception as e:
        flash(f'Error during conversion: {str(e)}', 'error')
        return redirect(url_for('index'))
    
    finally:
        # Clean up input files (but keep output for download)
        for filepath in saved_files:
            try:
                filepath.unlink()
            except:
                pass


# Simple in-memory storage for download sessions (use Redis/database in production)
download_sessions = {}


@app.route('/success')
def success():
    """Show success page with download link."""
    session_id = request.args.get('session_id')
    filename = request.args.get('filename')
    
    if not session_id or session_id not in download_sessions:
        flash('Download session expired or invalid', 'error')
        return redirect(url_for('index'))
    
    return render_template('success.html', filename=filename, session_id=session_id)


@app.route('/download/<session_id>')
def download(session_id):
    """Serve the converted file for download."""
    
    if session_id not in download_sessions:
        flash('Download session expired or invalid', 'error')
        return redirect(url_for('index'))
    
    session_info = download_sessions[session_id]
    filepath = Path(session_info['path'])
    filename = session_info['filename']
    
    if not filepath.exists():
        flash('File no longer available', 'error')
        return redirect(url_for('index'))
    
    return send_file(
        filepath,
        as_attachment=True,
        download_name=filename,
        mimetype='application/zip'
    )


@app.route('/api/convert', methods=['POST'])
def api_convert():
    """API endpoint for conversion (returns JSON)."""
    
    if 'files' not in request.files:
        return jsonify({'success': False, 'error': 'No files provided'}), 400
    
    files = request.files.getlist('files')
    files = [f for f in files if f.filename]
    
    if not files:
        return jsonify({'success': False, 'error': 'No files provided'}), 400
    
    # Validate files
    for file in files:
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': f'Invalid file: {file.filename}'}), 400
    
    # Create session folder
    session_id = str(uuid.uuid4())
    session_folder = UPLOAD_FOLDER / session_id
    session_folder.mkdir(exist_ok=True)
    
    try:
        # Save and convert
        saved_files = []
        for file in files:
            filename = secure_filename(file.filename)
            filepath = session_folder / filename
            file.save(filepath)
            saved_files.append(filepath)
        
        output_path = convert_mela_to_paprika(session_folder, session_folder)
        
        if output_path is None:
            return jsonify({'success': False, 'error': 'Conversion failed'}), 500
        
        download_name = f"Paprika_Recipes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.paprikarecipes"
        download_path = session_folder / download_name
        output_path.rename(download_path)
        
        download_sessions[session_id] = {
            'path': str(download_path),
            'filename': download_name,
            'created': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'filename': download_name,
            'download_url': url_for('download', session_id=session_id, _external=True)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
    finally:
        for filepath in saved_files:
            try:
                filepath.unlink()
            except:
                pass


@app.route('/api/preview', methods=['POST'])
def api_preview():
    """API endpoint to preview a recipe without converting."""
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    if not file.filename:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'Invalid file type'}), 400
    
    try:
        # Read the file directly without saving
        content = file.read().decode('utf-8')
        mela_data = json.loads(content)
        
        # Convert to Paprika format for preview
        paprika_data = mela_to_paprika(mela_data)
        
        # Remove photo_data for preview (too large)
        preview_data = {k: v for k, v in paprika_data.items() if k != 'photo_data'}
        
        return jsonify({
            'success': True,
            'original': {
                'title': mela_data.get('title', 'Untitled'),
                'ingredients_count': len(mela_data.get('ingredients', '').split('\n')) if mela_data.get('ingredients') else 0,
            },
            'converted': preview_data
        })
        
    except json.JSONDecodeError as e:
        return jsonify({'success': False, 'error': f'Invalid JSON: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.errorhandler(413)
def too_large(e):
    """Handle 413 Payload Too Large errors."""
    max_size_mb = app.config['MAX_CONTENT_LENGTH'] // (1024 * 1024)
    if request.is_json or request.path.startswith('/api/'):
        return jsonify({
            'success': False, 
            'error': f'File(s) too large. Maximum total upload size is {max_size_mb}MB. Try uploading fewer files at once.'
        }), 413
    flash(f'Files too large. Maximum total upload size is {max_size_mb}MB. Try uploading fewer files at once or increase MAX_UPLOAD_MB.', 'error')
    return redirect(url_for('index'))


@app.route('/config')
def get_config():
    """Get app configuration for frontend."""
    return jsonify({
        'max_upload_mb': app.config['MAX_CONTENT_LENGTH'] // (1024 * 1024),
        'allowed_extensions': list(ALLOWED_EXTENSIONS)
    })


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'})


if __name__ == '__main__':
    # Create templates directory
    templates_dir = Path(__file__).parent / 'templates'
    templates_dir.mkdir(exist_ok=True)
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)
