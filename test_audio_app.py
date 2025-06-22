#!/usr/bin/env python3
"""
Simple test app for audio generation testing
"""
import os
import wave
import struct
import math
import io
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, render_template

app = Flask(__name__)

def _ensure_audio_dir():
    """Ensure static/audio directory exists and return Path object."""
    audio_dir = Path('static/audio')
    audio_dir.mkdir(parents=True, exist_ok=True)
    return audio_dir

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
    
    # Count generated images in images directory
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

@app.route('/')
def dashboard():
    """Main dashboard"""
    status = get_system_status()
    return render_template('dashboard.html', status=status)

@app.route('/api/image-stats')
def api_image_stats():
    """Get image organization statistics"""
    try:
        from pathlib import Path
        
        images_dir = Path('images')
        stats = {
            'base_pngs': len(list(images_dir.glob('*.png'))) if images_dir.exists() else 0,
            'pending': 0,
            'approved': 0,
            'rejected': 0,
            'selected_for_video': 0,
            'total_videos': 0
        }
        
        if images_dir.exists():
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

@app.route('/api/generate-ambient', methods=['POST'])
def api_generate_ambient():
    """Generate ambient audio from prompt"""
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        duration = data.get('duration', 30)
        
        if not prompt.strip():
            return jsonify({'success': False, 'error': 'Prompt is required'})
        
        # Generate mock audio - simple sine wave
        import wave
        import struct
        import math
        
        sample_rate = 44100
        frequency = 440  # A4 note for ambient sound
        amplitude = 0.1
        num_samples = sample_rate * duration
        
        # Generate sine wave
        samples = []
        for i in range(num_samples):
            sample = amplitude * math.sin(2 * math.pi * frequency * i / sample_rate)
            samples.append(struct.pack('<h', int(sample * 32767)))
        
        # Create WAV data in memory
        import io
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(b''.join(samples))
        
        audio_bytes = wav_buffer.getvalue()
        
        # Ensure output directory exists
        audio_dir = _ensure_audio_dir()
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'ambient_{timestamp}.wav'
        filepath = audio_dir / filename
        
        # Write audio file
        with open(filepath, 'wb') as f:
            f.write(audio_bytes)
        
        # Return URLs for preview and download
        audio_url = f'/static/audio/{filename}'
        
        return jsonify({
            'success': True,
            'filename': filename,
            'audio_url': audio_url,
            'path': str(filepath)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/generate-voiceover', methods=['POST'])
def api_generate_voiceover():
    """Generate voiceover from text"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        voice = data.get('voice', 'female-narrator')
        
        if not text.strip():
            return jsonify({'success': False, 'error': 'Text is required'})
        
        # Generate mock audio - simple sine wave with lower frequency for voice
        import wave
        import struct
        import math
        
        sample_rate = 44100
        frequency = 320  # Lower frequency for voice-like sound
        amplitude = 0.05
        num_samples = sample_rate * 5  # 5 second audio
        
        # Generate sine wave
        samples = []
        for i in range(num_samples):
            sample = amplitude * math.sin(2 * math.pi * frequency * i / sample_rate)
            samples.append(struct.pack('<h', int(sample * 32767)))
        
        # Create WAV data in memory
        import io
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(b''.join(samples))
        
        audio_bytes = wav_buffer.getvalue()
        
        # Ensure output directory exists
        audio_dir = _ensure_audio_dir()
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'voiceover_{timestamp}.wav'
        filepath = audio_dir / filename
        
        # Write audio file
        with open(filepath, 'wb') as f:
            f.write(audio_bytes)
        
        # Return URLs for preview and download
        audio_url = f'/static/audio/{filename}'
        
        return jsonify({
            'success': True,
            'filename': filename,
            'audio_url': audio_url,
            'path': str(filepath)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Add static file serving for audio files
@app.route('/static/audio/<filename>')
def serve_audio(filename):
    """Serve audio files for preview and download"""
    audio_dir = _ensure_audio_dir()
    return send_from_directory(audio_dir, filename)

if __name__ == '__main__':
    print("Starting Audio Testing Server...")
    print("Access the web interface at: http://localhost:8080")
    app.run(debug=True, host='0.0.0.0', port=8080)
