#!/usr/bin/env python3
"""
Standalone Flask app for audio generation testing - no external dependencies
"""
import os
import wave
import struct
import math
import io
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

def _ensure_audio_dir():
    """Ensure static/audio directory exists and return Path object."""
    audio_dir = Path('static/audio')
    audio_dir.mkdir(parents=True, exist_ok=True)
    return audio_dir

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

@app.route('/test')
def test_page():
    """Simple test page"""
    return '''
    <!DOCTYPE html>
    <html>
    <head><title>Audio Test</title></head>
    <body>
        <h1>Audio Generation Test</h1>
        <button onclick="testAmbient()">Test Ambient</button>
        <button onclick="testVoiceover()">Test Voiceover</button>
        <div id="result"></div>
        <script>
        async function testAmbient() {
            const response = await fetch('/api/generate-ambient', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: 'peaceful forest', duration: 5 })
            });
            const data = await response.json();
            document.getElementById('result').innerHTML = JSON.stringify(data, null, 2);
        }
        async function testVoiceover() {
            const response = await fetch('/api/generate-voiceover', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: 'Hello world', voice: 'female-narrator' })
            });
            const data = await response.json();
            document.getElementById('result').innerHTML = JSON.stringify(data, null, 2);
        }
        </script>
    </body>
    </html>
    '''

if __name__ == '__main__':
    print("Starting Standalone Audio Testing Server...")
    print("Access the test page at: http://localhost:8080/test")
    app.run(debug=False, host='0.0.0.0', port=8080)
