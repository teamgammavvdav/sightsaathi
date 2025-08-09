
# app.py - PWA Backend for AI Vision Assistant
from flask import Flask, render_template, request, jsonify, send_from_directory
import base64
import io
from PIL import Image
from google import genai
from datetime import datetime
import json
import os

app = Flask(__name__)

# Your hardcoded API key from the original code
API_KEY = "AIzaSyCj4KYsBdB1qzwFppcQF7sHcdH7HsxwYxw"

# Initialize Gemini (same as your original code)
try:
    client = genai.Client(api_key=API_KEY)
    gemini_ready = True
    print("✅ Gemini API initialized successfully")
except Exception as e:
    print(f"❌ Gemini initialization error: {e}")
    gemini_ready = False

# Store analysis history (like your original app)
analysis_history = []

@app.route('/')
def index():
    """Serve the main PWA interface"""
    return render_template('index.html')

@app.route('/manifest.json')
def manifest():
    """PWA manifest for installability"""
    return jsonify({
        "name": "AI Vision Assistant for Blind Users",
        "short_name": "AIVision",
        "description": "AI-powered vision assistance with camera analysis",
        "start_url": "/",
        "display": "standalone",
        "theme_color": "#2196F3",
        "background_color": "#ffffff",
        "orientation": "portrait",
        "scope": "/",
        "icons": [
            {
                "src": "/static/icon-192.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any maskable"
            },
            {
                "src": "/static/icon-512.png",
                "sizes": "512x512", 
                "type": "image/png",
                "purpose": "any maskable"
            }
        ]
    })

@app.route('/sw.js')
def service_worker():
    """Service worker for PWA functionality"""
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')

@app.route('/analyze', methods=['POST'])
def analyze_frame():
    """Main analysis endpoint - converts your _perform_analysis logic"""
    if not gemini_ready:
        return jsonify({'error': 'Gemini API not available'})

    try:
        data = request.json
        image_data = data['image']
        mode = data.get('mode', 'Object Detection')

        # Decode base64 image (same as your original conversion)
        image_bytes = base64.b64decode(image_data.split(',')[1])

        # Use your exact prompt logic
        prompt = get_optimized_prompt(mode)

        # Call Gemini API (same as your original code)
        from google.genai import types

        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type='image/jpeg',
                ),
                prompt
            ]
        )

        result = response.text.strip()

        # Store in history (like your original app)
        timestamp = datetime.now().strftime("%H:%M:%S")
        analysis_history.append({
            'timestamp': timestamp,
            'mode': mode,
            'result': result
        })

        return jsonify({
            'result': result,
            'mode': mode,
            'timestamp': timestamp,
            'speak': True  # Auto-speak like your original
        })

    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'})

def get_optimized_prompt(mode):
    """Your exact prompt logic from the original code"""
    prompts = {
        "Object Detection": """
        List the objects you see in this image. For each object, only provide:
        1. Object name
        2. Location (left, center, right, top, middle, bottom)

        Keep it simple and brief. Example format:
        "Coffee mug on the left, laptop computer in center, phone on right side"

        Do not include detailed descriptions, colors, or unnecessary details.
        """,

        "Scene Description": """
        Describe this scene for someone who cannot see it. Include:
        1. Overall setting and environment
        2. People present and their activities
        3. Lighting and atmosphere
        4. Important details for navigation

        Be comprehensive but clear for audio.
        """,

        "Money Counter": """
        Look for currency, coins, or money in this image.
        If money is visible:
        1. List each denomination
        2. Count quantity
        3. Calculate total value

        If no money: "No currency detected"
        Be accurate with counting.
        """,

        "Reading Mode": """
        Read all visible text in this image:
        1. Signs and labels
        2. Documents
        3. Digital displays
        4. Any written content

        Provide exact transcription of what the text says.
        If no text: "No readable text detected"
        """
    }

    return prompts.get(mode, prompts["Object Detection"])

@app.route('/history')
def get_history():
    """Get analysis history"""
    return jsonify(analysis_history)

@app.route('/clear_history', methods=['POST'])
def clear_history():
    """Clear analysis history"""
    global analysis_history
    analysis_history = []
    return jsonify({'success': True})

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)

    print("🚀 Starting AI Vision Assistant PWA...")
    print("📱 Open http://localhost:5000 on your phone")
    print("💡 Add to home screen for app-like experience")

    app.run(host='0.0.0.0', port=5000, debug=True)
