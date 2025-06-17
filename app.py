#!/usr/bin/env -S bash -c 'source ~/menv/bin/activate && exec "$0" "$@"'
"""
AI Image Generation Pipeline - Web Command Center
A Flask-based web interface for controlling the AI image generation pipeline.
"""

import os
import subprocess
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'ai-pipeline-secret-key-change-this'

# Configuration
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Helper Functions
def run_command(command, cwd=None):
    """Execute a command and return the result"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            cwd=cwd or os.getcwd(),
            timeout=300  # 5 minute timeout
        )
        return {
            'success': result.returncode == 0,
            'output': result.stdout,
            'error': result.stderr,
            'returncode': result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'output': '',
            'error': 'Command timed out after 5 minutes',
            'returncode': -1
        }
    except Exception as e:
        return {
            'success': False,
            'output': '',
            'error': str(e),
            'returncode': -1
        }

def get_system_status():
    """Get current system status"""
    status = {}
    
    # Check if required files exist
    required_files = ['generate.py', 'watermark.py', 'prompt_builder.py', 'gon.sh']
    status['files'] = {}
    for file in required_files:
        status['files'][file] = os.path.exists(file)
    
    # Check environment variables
    status['env'] = {
        'REPLICATE_API_TOKEN': bool(os.getenv('REPLICATE_API_TOKEN'))
    }
    
    # Count generated images in images directory - updated to use proper images/ path patterns
    from pathlib import Path
    images_dir = Path('images')
    if images_dir.exists():
        png_files = len(list(images_dir.glob('*.png')))
        jpg_files = len(list(images_dir.glob('*.jpg'))) + len(list(images_dir.glob('*.jpeg')))
        total_files = png_files + jpg_files
    else:
        total_files = 0
    status['generated_images'] = total_files
    
    return status

# Routes
@app.route('/')
def dashboard():
    """Main dashboard"""
    status = get_system_status()
    return render_template('dashboard.html', status=status)

@app.route('/generate')
def generate_page():
    """Image generation page"""
    return render_template('generate.html')

@app.route('/api/generate', methods=['POST'])
def api_generate():
    """Generate a single image"""
    data = request.get_json()
    
    location = data.get('location', '')
    item = data.get('item', '')
    mantra = data.get('mantra', '')
    aspect_ratio = data.get('aspect_ratio', '4:5')
    palette = data.get('palette', 'A')
    platform = data.get('platform', 'ig')
    
    if not all([location, item, mantra]):
        return jsonify({'success': False, 'error': 'Missing required fields'})
    
    # Build prompt
    prompt_cmd = f'python3 prompt_builder.py "{location}" "{item}" "{mantra}" "{aspect_ratio}" "{palette}"'
    prompt_result = run_command(prompt_cmd)
    
    if not prompt_result['success']:
        return jsonify({'success': False, 'error': 'Failed to build prompt', 'details': prompt_result['error']})
    
    # Extract prompt from output
    prompt_lines = prompt_result['output'].split('\n')
    prompt = None
    for line in prompt_lines:
        if line.startswith('Prompt:'):
            prompt = line.replace('Prompt: ', '')
            break
    
    if not prompt:
        return jsonify({'success': False, 'error': 'Could not extract prompt'})
    
    # Generate filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'custom_{timestamp}_{palette}_{platform}.png'
    
    # Generate image
    generate_cmd = f'python3 generate.py "{prompt}" "{filename}" "{aspect_ratio}"'
    generate_result = run_command(generate_cmd)
    
    if not generate_result['success']:
        return jsonify({'success': False, 'error': 'Failed to generate image', 'details': generate_result['error']})
    
    # Apply watermark
    platform_name = {'ig': 'instagram', 'tt': 'tiktok', 'tw': 'twitter'}.get(platform, 'instagram')
    watermark_cmd = f'python3 watermark.py "{filename}" "Fortuna_Bound_Watermark.png" "{platform_name}" --logo'
    watermark_result = run_command(watermark_cmd)
    
    return jsonify({
        'success': True, 
        'filename': filename,
        'watermarked': watermark_result['success'],
        'prompt': prompt
    })

@app.route('/api/run-pipeline', methods=['POST'])
def api_run_pipeline():
    """Run the full generation pipeline"""
    result = run_command('./gon.sh')
    return jsonify(result)

@app.route('/api/status')
def api_status():
    """Get system status"""
    return jsonify(get_system_status())

@app.route('/api/verify-setup')
def api_verify_setup():
    """Verify system setup"""
    result = run_command('python3 verify_setup.py')
    return jsonify(result)

@app.route('/api/palette-extract', methods=['POST'])
def api_palette_extract():
    """Extract colors from uploaded image"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})
    
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Extract palette
        result = run_command(f'python3 palette_extractor.py "{filepath}" 5')
        
        # Clean up uploaded file
        os.remove(filepath)
        
        return jsonify(result)

@app.route('/logs')
def logs_page():
    """View logs page"""
    return render_template('logs.html')

@app.route('/api/logs')
def api_logs():
    """Get recent logs"""
    log_files = ['regenerate.log', 'palette_rotation.log']
    logs = {}
    
    for log_file in log_files:
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    logs[log_file] = f.read().split('\n')[-100:]  # Last 100 lines
            except Exception as e:
                logs[log_file] = [f'Error reading log: {e}']
        else:
            logs[log_file] = ['Log file not found']
    
    return jsonify(logs)

@app.route('/api/organize-images', methods=['POST'])
def api_organize_images():
    """Organize and filter images"""
    result = run_command('python3 image_organizer.py')
    return jsonify(result)

@app.route('/api/rank-images', methods=['POST'])
def api_rank_images():
    """Rank images by quality"""
    result = run_command('python3 image_ranker.py')
    return jsonify(result)

@app.route('/api/generate-videos', methods=['POST'])
def api_generate_videos():
    """Generate videos from selected images"""
    data = request.get_json() or {}
    max_videos = data.get('max_videos', 10)
    
    # Check if RUNWAY_API_KEY is set
    if not os.getenv('RUNWAY_API_KEY'):
        return jsonify({
            'success': False, 
            'error': 'RUNWAY_API_KEY environment variable not set'
        })
    
    cmd = f'python3 intelligent_video_generator.py'
    result = run_command(cmd)
    return jsonify(result)

@app.route('/api/image-stats')
def api_image_stats():
    """Get image organization statistics"""
    try:
        from pathlib import Path
        
        images_dir = Path('images')
        stats = {
            # Updated to use proper images/ directory patterns
            'base_pngs': len(list(images_dir.glob('*.png'))) if images_dir.exists() else 0,
            'pending': 0,
            'approved': 0,
            'rejected': 0,
            'selected_for_video': 0,
            'total_videos': 0
        }
        
        if images_dir.exists():
            # Updated patterns for subdirectories within images/
            stats['pending'] = len(list((images_dir / 'pending').glob('*.png'))) if (images_dir / 'pending').exists() else 0
            stats['approved'] = len(list((images_dir / 'approved').glob('*.png'))) if (images_dir / 'approved').exists() else 0
            stats['rejected'] = len(list((images_dir / 'rejected').glob('*.png'))) if (images_dir / 'rejected').exists() else 0
            stats['selected_for_video'] = len(list((images_dir / 'selected_for_video').glob('*.png'))) if (images_dir / 'selected_for_video').exists() else 0
        
        video_outputs_dir = Path('video_outputs')
        if video_outputs_dir.exists():
            stats['total_videos'] = len(list(video_outputs_dir.glob('*.mp4')))
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    print("Starting AI Image Generation Pipeline Command Center...")
    print("Access the web interface at: http://localhost:8080")
    app.run(debug=True, host='0.0.0.0', port=8080)

