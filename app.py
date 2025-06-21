#!/usr/bin/env -S bash -c 'source ~/menv/bin/activate && exec "$0" "$@"'
"""
AI Image Generation Pipeline - Web Command Center
Optimized Flask-based web interface with automatic watermarking integration.
"""

import os
import subprocess
import json
import threading
import time
from datetime import datetime
from pathlib import Path
from functools import lru_cache
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from werkzeug.utils import secure_filename

# Import robust output system
try:
    from robust_output import log_safe, generate_descriptive_filename, workflow_manager, filename_generator
    ROBUST_OUTPUT_AVAILABLE = True
except ImportError:
    ROBUST_OUTPUT_AVAILABLE = False
    def log_safe(msg, level="INFO"): pass
    def generate_descriptive_filename(prompt="", platform="ig", descriptors=None): 
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"image_{timestamp}_{platform}.png"
    filename_generator = None

# Import our watermarking pipeline
try:
    from auto_watermark_workflow import WatermarkWorkflow
    from pipeline_integration import AutoWatermarkPipeline
    WATERMARK_AVAILABLE = True
except ImportError:
    print("Warning: Watermarking modules not available")
    WATERMARK_AVAILABLE = False

app = Flask(__name__)
app.secret_key = 'fortuna-bound-ai-pipeline-2024'

# Optimized Configuration
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB max file size
app.config['TEMPLATES_AUTO_RELOAD'] = False  # Disable in production
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 300  # 5 minutes cache

# Thread pool for background tasks
from concurrent.futures import ThreadPoolExecutor
executor = ThreadPoolExecutor(max_workers=3)

# Initialize watermarking pipeline
if WATERMARK_AVAILABLE:
    watermark_pipeline = AutoWatermarkPipeline()
else:
    watermark_pipeline = None

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('images', exist_ok=True)
os.makedirs('video_outputs', exist_ok=True)

# Helper Functions
def run_command(command, cwd=None):
    """Execute a command and return the result"""
    try:
        # Create environment with current environment plus any missing vars
        env = os.environ.copy()
        
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            cwd=cwd or os.getcwd(),
            env=env,
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
    aspect_ratio = data.get('aspect_ratio', '4:5')
    palette = data.get('palette', 'A')
    platform = data.get('platform', 'ig')
    
    if not all([location, item]):
        return jsonify({'success': False, 'error': 'Missing required fields: location and item'})
    
    # Build prompt without mantra - mantras are handled via watermarking only
    prompt_cmd = f'python3 prompt_builder.py "{location}" "{item}" "{aspect_ratio}" "{palette}"'
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
    
    # Generate filename with proper path
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'custom_{timestamp}_{palette}_{platform}.png'
    full_path = f'images/{filename}'
    
    # Generate image with proper escaping
    import shlex
    generate_args = ['python3', 'generate.py', prompt, full_path, aspect_ratio]
    generate_cmd = ' '.join(shlex.quote(arg) for arg in generate_args)
    generate_result = run_command(generate_cmd)
    
    if not generate_result['success']:
        return jsonify({
            'success': False, 
            'error': 'Failed to generate image', 
            'details': generate_result['error'],
            'command': generate_cmd
        })
    
    # Check if image was actually created
    if not os.path.exists(full_path):
        return jsonify({
            'success': False, 
            'error': 'Image file was not created', 
            'expected_path': full_path
        })
    
    # Apply watermark with automatic workflow integration
    if WATERMARK_AVAILABLE:
        try:
            # Use our optimized watermarking workflow
            watermarked_files = watermark_pipeline.workflow.watermark_new_images()
            watermark_success = len(watermarked_files) > 0
        except Exception as e:
            # Fallback to direct watermarking
            platform_name = {'ig': 'instagram', 'tt': 'tiktok', 'tw': 'twitter'}.get(platform, 'instagram')
            watermark_cmd = f'python3 watermark.py "{full_path}" "Fortuna_Bound_Watermark.png" "{platform_name}" --logo'
            watermark_result = run_command(watermark_cmd)
            watermark_success = watermark_result['success']
    else:
        # Fallback watermarking
        platform_name = {'ig': 'instagram', 'tt': 'tiktok', 'tw': 'twitter'}.get(platform, 'instagram')
        watermark_cmd = f'python3 watermark.py "{full_path}" "Fortuna_Bound_Watermark.png" "{platform_name}" --logo'
        watermark_result = run_command(watermark_cmd)
        watermark_success = watermark_result['success']
    
    return jsonify({
        'success': True, 
        'filename': filename,
        'watermarked': watermark_success,
        'prompt': prompt,
        'path': full_path
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

@app.route('/api/generate-video-filename-stub', methods=['POST'])
def api_generate_video_filename_stub():
    """Generate video filename stub for Step 6: descriptor1_descriptor2_descriptor3{platform_suffix}_{YYYYMMDD_HHMMSS}"""
    try:
        data = request.get_json() or {}
        image_path = data.get('image_path', '')
        platform = data.get('platform', 'ig')
        
        if not image_path:
            return jsonify({'success': False, 'error': 'image_path is required'})
        
        if ROBUST_OUTPUT_AVAILABLE:
            # Use the Step 6 implementation
            filename_stub = filename_generator.generate_video_filename_stub(image_path, platform)
            log_safe(f"Generated video filename stub: {filename_stub}")
            
            return jsonify({
                'success': True,
                'filename_stub': filename_stub,
                'video_filename': f"{filename_stub}.mp4",
                'platform': platform,
                'image_path': image_path
            })
        else:
            # Fallback implementation
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            platform_suffix = {'ig': '_ig', 'fb': '_fb', 'tw': '_tw', 'tt': '_tt'}.get(platform, '_ig')
            filename_stub = f"video{platform_suffix}_{timestamp}"
            
            return jsonify({
                'success': True,
                'filename_stub': filename_stub,
                'video_filename': f"{filename_stub}.mp4",
                'platform': platform,
                'image_path': image_path
            })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

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

@app.route('/api/generate-mantras', methods=['POST'])
def api_generate_mantras():
    """Generate uplifting mantras with preview"""
    try:
        from mantra_generator import MantraGenerator
        data = request.get_json() or {}
        
        category = data.get('category')
        count = data.get('count', 5)
        
        generator = MantraGenerator()
        mantras = generator.generate_mantra_options(category, count)
        
        return jsonify(mantras)
    except ImportError:
        return jsonify({'success': False, 'error': 'Mantra generator not available'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/preview-mantra', methods=['POST'])
def api_preview_mantra():
    """Preview text placement for custom mantra"""
    try:
        from mantra_generator import MantraGenerator
        data = request.get_json() or {}
        
        text = data.get('text', '')
        width = data.get('width', 1080)
        height = data.get('height', 1350)
        
        if not text:
            return jsonify({'success': False, 'error': 'No text provided'})
        
        generator = MantraGenerator()
        preview = generator.preview_text_placement(text, width, height)
        
        return jsonify({'success': True, 'preview': preview})
    except ImportError:
        return jsonify({'success': False, 'error': 'Mantra generator not available'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/generate-direct', methods=['POST'])
def api_generate_direct():
    """Generate image directly from custom prompt"""
    try:
        from direct_prompt_generator import DirectPromptGenerator
        data = request.get_json()
        
        base_prompt = data.get('prompt', '')
        style = data.get('style')
        platform = data.get('platform', 'ig')
        aspect_ratio = data.get('aspect_ratio', '4:5')
        custom_mantra = data.get('mantra')
        mantra_category = data.get('mantra_category')
        
        if not base_prompt:
            return jsonify({'success': False, 'error': 'No prompt provided'})
        
        generator = DirectPromptGenerator()
        
        # Generate enhanced prompt
        if custom_mantra or mantra_category:
            result = generator.generate_with_mantra(
                base_prompt, 
                mantra_category, 
                custom_mantra, 
                1
            )
            enhanced_prompt = result['results'][0]['enhanced_prompt']
            mantra_info = result['results'][0]['mantra']
        else:
            enhanced_prompt = generator.enhance_prompt(base_prompt, style, platform)
            mantra_info = None
        
        # Generate descriptive filename with 3 descriptors + timestamp + platform
        if ROBUST_OUTPUT_AVAILABLE:
            filename = generate_descriptive_filename(enhanced_prompt, platform)
            log_safe(f"Generated descriptive filename: {filename}")
        else:
            # Fallback to simple filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'direct_{timestamp}_{platform}.png'
        
        full_path = f'images/{filename}'
        
        # Generate image using enhanced prompt
        import shlex
        api_token = os.getenv('REPLICATE_API_TOKEN', '')
        generate_cmd = f'REPLICATE_API_TOKEN={shlex.quote(api_token)} python3 generate.py {shlex.quote(enhanced_prompt)} {shlex.quote(full_path)} {shlex.quote(aspect_ratio)}'
        generate_result = run_command(generate_cmd)
        
        if not generate_result['success']:
            return jsonify({
                'success': False, 
                'error': 'Failed to generate image', 
                'details': generate_result['error'],
                'enhanced_prompt': enhanced_prompt
            })
        
        # Check if image was created
        if not os.path.exists(full_path):
            return jsonify({
                'success': False, 
                'error': 'Image file was not created', 
                'expected_path': full_path
            })
        
        # Apply watermark
        watermark_success = False
        if WATERMARK_AVAILABLE:
            try:
                watermarked_files = watermark_pipeline.workflow.watermark_new_images()
                watermark_success = len(watermarked_files) > 0
            except Exception as e:
                platform_name = {'ig': 'instagram', 'tt': 'tiktok', 'tw': 'twitter'}.get(platform, 'instagram')
                watermark_cmd = f'python3 watermark.py "{full_path}" "Fortuna_Bound_Watermark.png" "{platform_name}" --logo'
                watermark_result = run_command(watermark_cmd)
                watermark_success = watermark_result['success']
        
        response = {
            'success': True,
            'filename': filename,
            'path': full_path,
            'base_prompt': base_prompt,
            'enhanced_prompt': enhanced_prompt,
            'watermarked': watermark_success,
            'style': style,
            'platform': platform,
            'aspect_ratio': aspect_ratio
        }
        
        if mantra_info:
            response['mantra'] = mantra_info
        
        return jsonify(response)
        
    except ImportError:
        return jsonify({'success': False, 'error': 'Direct prompt generator not available'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    print("Starting AI Image Generation Pipeline Command Center...")
    print("Access the web interface at: http://localhost:8080")
    app.run(debug=False, host='0.0.0.0', port=8080)

