#!/usr/bin/env python3
# save as: backup_receiver.py

import os
import json
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_file, abort
import logging

# Configuration
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
ALLOWED_EXTENSIONS = {'.db', '.json', '.txt'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create upload directory
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

def allowed_file(filename):
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS

def get_file_info(file_path):
    """Get detailed file information"""
    try:
        stat = file_path.stat()
        return {
            'filename': file_path.name,
            'size': stat.st_size,
            'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'extension': file_path.suffix.lower()
        }
    except Exception as e:
        logger.error(f"Error getting file info for {file_path}: {e}")
        return None

@app.route('/upload', methods=['POST'])
def upload_backup():
    try:
        if not request.files:
            return jsonify({'error': 'No files provided'}), 400

        uploaded_files = []
        
        for file_key, file in request.files.items():
            if file.filename == '':
                continue
                
            if not allowed_file(file.filename):
                logger.warning(f"Rejected file with invalid extension: {file.filename}")
                continue
            
            # Create timestamp prefix for uniqueness
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = f"{timestamp}_{file.filename}"
            file_path = Path(UPLOAD_DIR) / safe_filename
            
            # Save file
            file.save(str(file_path))
            uploaded_files.append({
                'original_name': file.filename,
                'saved_as': safe_filename,
                'size': file_path.stat().st_size,
                'type': file_key
            })
            
            logger.info(f"Uploaded: {file.filename} -> {safe_filename}")
        
        # Log upload event
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'client_ip': request.remote_addr,
            'files': uploaded_files,
            'user_agent': request.headers.get('User-Agent', 'Unknown')
        }
        
        # Save upload log
        log_file = Path(UPLOAD_DIR) / "upload_log.json"
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        return jsonify({
            'success': True,
            'message': f'Successfully uploaded {len(uploaded_files)} files',
            'files': uploaded_files
        })
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>', methods=['GET'])
def download_backup(filename):
    """Download a specific backup file"""
    try:
        # Security: Only allow files in upload directory and validate filename
        if not filename or '..' in filename or '/' in filename or '\\' in filename:
            logger.warning(f"Invalid filename requested: {filename}")
            abort(400, description="Invalid filename")
        
        file_path = Path(UPLOAD_DIR) / filename
        
        if not file_path.exists():
            logger.warning(f"File not found: {filename}")
            abort(404, description="File not found")
        
        if not file_path.is_file():
            logger.warning(f"Not a file: {filename}")
            abort(404, description="Not a file")
        
        # Verify file extension
        if not allowed_file(filename):
            logger.warning(f"File type not allowed: {filename}")
            abort(403, description="File type not allowed")
        
        logger.info(f"Downloading file: {filename} for client {request.remote_addr}")
        
        # Log download event
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': 'download',
            'client_ip': request.remote_addr,
            'filename': filename,
            'file_size': file_path.stat().st_size,
            'user_agent': request.headers.get('User-Agent', 'Unknown')
        }
        
        # Save download log
        log_file = Path(UPLOAD_DIR) / "download_log.json"
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        return send_file(
            str(file_path),
            as_attachment=True,
            download_name=filename,
            mimetype='application/octet-stream'
        )
        
    except Exception as e:
        logger.error(f"Download failed for {filename}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/list', methods=['GET'])
def list_backups():
    """List all available backup files with detailed information"""
    try:
        files = []
        upload_path = Path(UPLOAD_DIR)
        
        if not upload_path.exists():
            return jsonify({
                'success': True,
                'files': [],
                'message': 'Upload directory does not exist'
            })
        
        # Get all files with allowed extensions
        for file_path in upload_path.iterdir():
            if file_path.is_file() and allowed_file(file_path.name):
                file_info = get_file_info(file_path)
                if file_info:
                    files.append(file_info)
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: x['modified'], reverse=True)
        
        logger.info(f"Listed {len(files)} backup files for client {request.remote_addr}")
        
        return jsonify({
            'success': True,
            'files': files,
            'total_count': len(files),
            'upload_dir': str(upload_path),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"List backups failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/info/<filename>', methods=['GET'])
def file_info(filename):
    """Get detailed information about a specific file"""
    try:
        # Security validation
        if not filename or '..' in filename or '/' in filename or '\\' in filename:
            abort(400, description="Invalid filename")
        
        file_path = Path(UPLOAD_DIR) / filename
        
        if not file_path.exists() or not file_path.is_file():
            abort(404, description="File not found")
        
        if not allowed_file(filename):
            abort(403, description="File type not allowed")
        
        file_info = get_file_info(file_path)
        if not file_info:
            return jsonify({'error': 'Could not get file information'}), 500
        
        # Add download URL
        file_info['download_url'] = f"/download/{filename}"
        
        return jsonify({
            'success': True,
            'file': file_info
        })
        
    except Exception as e:
        logger.error(f"File info failed for {filename}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/status', methods=['GET'])
def status():
    """Health check endpoint with server statistics"""
    try:
        upload_path = Path(UPLOAD_DIR)
        file_count = 0
        total_size = 0
        
        if upload_path.exists():
            for file_path in upload_path.iterdir():
                if file_path.is_file() and allowed_file(file_path.name):
                    file_count += 1
                    total_size += file_path.stat().st_size
        
        return jsonify({
            'status': 'running',
            'upload_dir': UPLOAD_DIR,
            'timestamp': datetime.now().isoformat(),
            'statistics': {
                'total_files': file_count,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            },
            'endpoints': {
                'upload': '/upload (POST)',
                'download': '/download/<filename> (GET)',
                'list': '/list (GET)',
                'info': '/info/<filename> (GET)',
                'status': '/status (GET)'
            }
        })
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/delete/<filename>', methods=['DELETE'])
def delete_backup(filename):
    """Delete a specific backup file (optional endpoint)"""
    try:
        # Security validation
        if not filename or '..' in filename or '/' in filename or '\\' in filename:
            abort(400, description="Invalid filename")
        
        file_path = Path(UPLOAD_DIR) / filename
        
        if not file_path.exists():
            abort(404, description="File not found")
        
        if not file_path.is_file():
            abort(404, description="Not a file")
        
        if not allowed_file(filename):
            abort(403, description="File type not allowed")
        
        # Delete the file
        file_size = file_path.stat().st_size
        file_path.unlink()
        
        logger.info(f"Deleted file: {filename} (size: {file_size}) for client {request.remote_addr}")
        
        # Log deletion event
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': 'delete',
            'client_ip': request.remote_addr,
            'filename': filename,
            'file_size': file_size,
            'user_agent': request.headers.get('User-Agent', 'Unknown')
        }
        
        # Save deletion log
        log_file = Path(UPLOAD_DIR) / "deletion_log.json"
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        return jsonify({
            'success': True,
            'message': f'Successfully deleted {filename}',
            'deleted_file': {
                'filename': filename,
                'size': file_size
            }
        })
        
    except Exception as e:
        logger.error(f"Delete failed for {filename}: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(413)
def file_too_large(e):
    return jsonify({'error': 'File too large'}), 413

@app.errorhandler(400)
def bad_request(e):
    return jsonify({'error': str(e.description)}), 400

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': str(e.description)}), 404

@app.errorhandler(403)
def forbidden(e):
    return jsonify({'error': str(e.description)}), 403

if __name__ == '__main__':
    print(f"🚀 Chame Backup Receiver starting...")
    print(f"📁 Upload directory: {UPLOAD_DIR}")
    print(f"🌐 Endpoints available:")
    print(f"   📤 Upload:   http://0.0.0.0:5050/upload (POST)")
    print(f"   📥 Download: http://0.0.0.0:5050/download/<filename> (GET)")
    print(f"   📋 List:     http://0.0.0.0:5050/list (GET)")
    print(f"   ℹ️  Info:     http://0.0.0.0:5050/info/<filename> (GET)")
    print(f"   ❤️  Status:   http://0.0.0.0:5050/status (GET)")
    print(f"   🗑️  Delete:   http://0.0.0.0:5050/delete/<filename> (DELETE)")
    print(f"🎯 Server ready at http://0.0.0.0:5050")
    
    # Run server
    app.run(host='0.0.0.0', port=5050, debug=False)
