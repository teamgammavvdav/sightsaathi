# app.py - FIXED for Render deployment
from flask import Flask, render_template, request, jsonify, send_from_directory
import base64
import io
from PIL import Image
import google.generativeai as genai
from datetime import datetime
import json
import os

app = Flask(__name__)

# Your API key
API_KEY = "AIzaSyCj4KYsBdB1qzwFppcQF7sHcdH7HsxwYxw"

# Initialize Gemini with FIXED import
try:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    gemini_ready = True
    print("✅ Gemini API initialized successfully")
except Exception as e:
    print(f"❌ Gemini initialization error: {e}")
    gemini_ready = False
    model = None

# Store analysis history
analysis_history = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/manifest.json')
def manifest():
    return jsonify({
        "name": "AI Vision Assistant for Blind Users",
        "short_name": "AIVision",
        "description": "AI-powered vision assistance with camera analysis",
        "start_url": "/",
        "display": "standalone",
        "theme_color": "#2196F3",
        "background_color": "#ffffff",
        "orientation": "portrait-primary",
        "scope": "/",
        "categories": ["accessibility", "utilities", "productivity"],
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
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')

@app.route('/analyze', methods=['POST'])
def analyze_frame():
    if not gemini_ready or not model:
        return jsonify({'error': 'Gemini API not available'})

    try:
        data = request.json
        image_data = data['image']
        mode = data.get('mode', 'Object Detection')

        print(f"🔍 Analyzing image in {mode} mode...")

        # Decode base64 image
        image_bytes = base64.b64decode(image_data.split(',')[1])

        # Convert to PIL Image for Gemini
        pil_image = Image.open(io.BytesIO(image_bytes))

        # Get mode-specific prompt
        prompt = get_optimized_prompt(mode)

        # Call Gemini API with FIXED method
        response = model.generate_content([prompt, pil_image])
        result = response.text.strip()

        # Store in history
        timestamp = datetime.now().strftime("%H:%M:%S")
        analysis_history.append({
            'timestamp': timestamp,
            'mode': mode,
            'result': result
        })

        print(f"✅ Analysis complete: {len(result)} characters")

        return jsonify({
            'result': result,
            'mode': mode,
            'timestamp': timestamp,
            'speak': True
        })

    except Exception as e:
        print(f"❌ Analysis error: {str(e)}")
        return jsonify({'error': f'Analysis failed: {str(e)}'})

def get_optimized_prompt(mode):
    prompts = {
        "Object Detection": '''
        List the objects you see in this image. For each object, only provide:
        1. Object name
        2. Location (left, center, right, top, middle, bottom)

        Keep it simple and brief. Example format:
        "Coffee mug on the left, laptop computer in center, phone on right side"

        Do not include detailed descriptions, colors, or unnecessary details.
        ''',

        "Scene Description": '''
        Describe this scene for someone who cannot see it. Include:
        1. Overall setting and environment
        2. People present and their activities
        3. Lighting and atmosphere
        4. Important details for navigation

        Be comprehensive but clear for audio.
        ''',

        "Money Counter": '''
        Look for currency, coins, or money in this image.
        If money is visible:
        1. List each denomination
        2. Count quantity
        3. Calculate total value

        If no money: "No currency detected"
        Be accurate with counting.
        ''',

        "Reading Mode": '''
        Read all visible text in this image:
        1. Signs and labels
        2. Documents
        3. Digital displays
        4. Any written content

        Provide exact transcription of what the text says.
        If no text: "No readable text detected"
        '''
    }

    return prompts.get(mode, prompts["Object Detection"])

@app.route('/history')
def get_history():
    return jsonify(analysis_history)

@app.route('/clear_history', methods=['POST'])
def clear_history():
    global analysis_history
    analysis_history = []
    return jsonify({'success': True})

# Health check endpoint for Render
@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'gemini_ready': gemini_ready,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)

    print("🚀 Starting AI Vision Assistant...")
    print(f"📊 Gemini ready: {gemini_ready}")

    # Get port from environment (Render provides this)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
