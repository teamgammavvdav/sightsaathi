# app.py - Modified for DeepSeek via OpenRouter
from flask import Flask, render_template, request, jsonify, send_from_directory
import base64
import io
from PIL import Image
from openai import OpenAI
from datetime import datetime
import json
import os

app = Flask(__name__)

# OpenRouter API configuration for DeepSeek
OPENROUTER_API_KEY = "sk-80a051a8bbde225ed776e3a90b02f2490d415b64e7063f501195dbec54d83f99"

# Initialize OpenAI client with OpenRouter
try:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )
    deepseek_ready = True
    print("✅ OpenRouter + DeepSeek API initialized successfully")
except Exception as e:
    print(f"❌ OpenRouter initialization error: {e}")
    deepseek_ready = False
    client = None

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
    if not deepseek_ready or not client:
        return jsonify({'error': 'DeepSeek API not available'})

    try:
        data = request.json
        image_data = data['image']
        mode = data.get('mode', 'Object Detection')

        print(f"🔍 Analyzing image in {mode} mode...")

        # IMPORTANT: DeepSeek V3 does NOT support vision/image input
        # Using GPT-4 Vision through OpenRouter as alternative

        # Decode base64 image for processing
        image_base64 = image_data.split(',')[1]

        # Get mode-specific prompt
        prompt = get_optimized_prompt(mode)

        # Call OpenRouter with a vision-capable model (GPT-4 Vision)
        response = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://your-site.com",  # Optional
                "X-Title": "AI Vision Assistant",        # Optional
            },
            model="openai/gpt-4-vision-preview",  # Vision-capable model
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500
        )

        result = response.choices[0].message.content.strip()

        # Store in history
        timestamp = datetime.now().strftime("%H:%M:%S")
        analysis_history.append({
            'timestamp': timestamp,
            'mode': mode,
            'result': result,
            'model_used': 'GPT-4 Vision (via OpenRouter)'
        })

        print(f"✅ Analysis complete: {len(result)} characters")

        return jsonify({
            'result': result,
            'mode': mode,
            'timestamp': timestamp,
            'model_used': 'GPT-4 Vision',
            'speak': True
        })

    except Exception as e:
        print(f"❌ Analysis error: {str(e)}")
        return jsonify({'error': f'Analysis failed: {str(e)}'})

# Alternative route for text-only DeepSeek capabilities
@app.route('/text_analyze', methods=['POST'])
def text_analyze():
    """Route for text-only analysis using DeepSeek"""
    if not deepseek_ready or not client:
        return jsonify({'error': 'DeepSeek API not available'})

    try:
        data = request.json
        text_input = data.get('text', '')

        if not text_input:
            return jsonify({'error': 'No text provided'})

        print(f"🔍 Analyzing text with DeepSeek...")

        # Call DeepSeek through OpenRouter for text analysis
        response = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://your-site.com",  # Optional
                "X-Title": "AI Vision Assistant",        # Optional
            },
            model="deepseek/deepseek-chat",  # Free DeepSeek model
            messages=[
                {
                    "role": "user",
                    "content": text_input
                }
            ]
        )

        result = response.choices[0].message.content.strip()

        # Store in history
        timestamp = datetime.now().strftime("%H:%M:%S")
        analysis_history.append({
            'timestamp': timestamp,
            'mode': 'Text Analysis',
            'result': result,
            'model_used': 'DeepSeek V3'
        })

        print(f"✅ Text analysis complete: {len(result)} characters")

        return jsonify({
            'result': result,
            'mode': 'Text Analysis',
            'timestamp': timestamp,
            'model_used': 'DeepSeek V3',
            'speak': True
        })

    except Exception as e:
        print(f"❌ Text analysis error: {str(e)}")
        return jsonify({'error': f'Text analysis failed: {str(e)}'})

def get_optimized_prompt(mode):
    """Get mode-specific prompts for vision analysis"""
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
    return jsonify(analysis_history)

@app.route('/clear_history', methods=['POST'])
def clear_history():
    global analysis_history
    analysis_history = []
    return jsonify({'success': True})

# Health check endpoint
@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'deepseek_ready': deepseek_ready,
        'timestamp': datetime.now().isoformat(),
        'note': 'Using GPT-4 Vision for image analysis, DeepSeek V3 for text'
    })

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)

    print("🚀 Starting AI Vision Assistant with DeepSeek + GPT-4 Vision...")
    print(f"📊 DeepSeek ready: {deepseek_ready}")
    print("⚠️  NOTE: DeepSeek V3 does not support image analysis")
    print("💡 Using GPT-4 Vision through OpenRouter for image tasks")
    print("🎯 DeepSeek V3 available for text-only analysis via /text_analyze endpoint")

    # Get port from environment
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
