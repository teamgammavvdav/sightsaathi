# app.py - FIXED for OpenRouter + DeepSeek Integration
# Version Fix: Uses openai==1.55.3 and httpx==0.27.2 to resolve proxies argument error

from flask import Flask, render_template, request, jsonify, send_from_directory
import base64
import io
from PIL import Image
from openai import OpenAI
from datetime import datetime
import json
import os
import sys

app = Flask(__name__)

# OpenRouter API configuration for DeepSeek
OPENROUTER_API_KEY = "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"

# Initialize OpenAI client with OpenRouter
try:
    print("🔧 Initializing OpenRouter client...")
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )

    # Test the connection
    test_response = client.models.list()
    deepseek_ready = True
    print("✅ OpenRouter + DeepSeek API initialized successfully")
    print("📊 Available models loaded from OpenRouter")

except Exception as e:
    print(f"❌ OpenRouter initialization error: {e}")
    print("💡 If you see 'proxies' error, check your package versions:")
    print("   - pip install openai==1.55.3 httpx==0.27.2")
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
    """Main vision analysis endpoint using GPT-4 Vision (DeepSeek doesn't support vision)"""
    if not deepseek_ready or not client:
        return jsonify({
            'error': 'OpenRouter API not available',
            'suggestion': 'Check your API key and network connection'
        })

    try:
        data = request.json
        image_data = data['image']
        mode = data.get('mode', 'Object Detection')

        print(f"🔍 Analyzing image in {mode} mode using GPT-4 Vision...")

        # Decode base64 image for processing
        image_base64 = image_data.split(',')[1]

        # Get mode-specific prompt
        prompt = get_optimized_prompt(mode)

        # Call OpenRouter with GPT-4 Vision (since DeepSeek doesn't support vision)
        response = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://your-vision-app.com",  # Optional
                "X-Title": "AI Vision Assistant",              # Optional
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
            max_tokens=500,
            temperature=0.1  # Low temperature for consistent analysis
        )

        result = response.choices[0].message.content.strip()

        # Store in history
        timestamp = datetime.now().strftime("%H:%M:%S")
        analysis_history.append({
            'timestamp': timestamp,
            'mode': mode,
            'result': result,
            'model_used': 'GPT-4 Vision (via OpenRouter)',
            'tokens_used': response.usage.total_tokens if hasattr(response, 'usage') else 'N/A'
        })

        print(f"✅ Vision analysis complete: {len(result)} characters")

        return jsonify({
            'result': result,
            'mode': mode,
            'timestamp': timestamp,
            'model_used': 'GPT-4 Vision',
            'speak': True,
            'tokens_used': response.usage.total_tokens if hasattr(response, 'usage') else None
        })

    except Exception as e:
        print(f"❌ Vision analysis error: {str(e)}")

        # Provide specific error messages for common issues
        error_message = str(e)
        if "proxies" in error_message.lower():
            error_message = "Version compatibility error. Please update packages: pip install openai==1.55.3 httpx==0.27.2"
        elif "rate_limit" in error_message.lower():
            error_message = "Rate limit exceeded. Please wait a moment and try again."
        elif "api_key" in error_message.lower():
            error_message = "API key issue. Please check your OpenRouter API key."

        return jsonify({
            'error': f'Vision analysis failed: {error_message}',
            'model_used': 'GPT-4 Vision',
            'troubleshooting': 'Check your OpenRouter API key and package versions'
        })

@app.route('/text_analyze', methods=['POST'])
def text_analyze():
    """Text-only analysis endpoint using DeepSeek V3"""
    if not deepseek_ready or not client:
        return jsonify({
            'error': 'DeepSeek API not available',
            'suggestion': 'Check your OpenRouter API key'
        })

    try:
        data = request.json
        text_input = data.get('text', '')

        if not text_input:
            return jsonify({'error': 'No text provided for analysis'})

        print(f"🔍 Analyzing text with DeepSeek V3...")

        # Call DeepSeek through OpenRouter for text analysis
        response = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://your-vision-app.com",  # Optional
                "X-Title": "AI Vision Assistant",              # Optional
            },
            model="deepseek/deepseek-chat",  # Free DeepSeek model for text
            messages=[
                {
                    "role": "user",
                    "content": text_input
                }
            ],
            max_tokens=800,
            temperature=0.3
        )

        result = response.choices[0].message.content.strip()

        # Store in history
        timestamp = datetime.now().strftime("%H:%M:%S")
        analysis_history.append({
            'timestamp': timestamp,
            'mode': 'Text Analysis (DeepSeek)',
            'result': result,
            'model_used': 'DeepSeek V3',
            'tokens_used': response.usage.total_tokens if hasattr(response, 'usage') else 'N/A'
        })

        print(f"✅ Text analysis complete: {len(result)} characters")

        return jsonify({
            'result': result,
            'mode': 'Text Analysis',
            'timestamp': timestamp,
            'model_used': 'DeepSeek V3',
            'speak': True,
            'tokens_used': response.usage.total_tokens if hasattr(response, 'usage') else None
        })

    except Exception as e:
        print(f"❌ Text analysis error: {str(e)}")
        return jsonify({
            'error': f'Text analysis failed: {str(e)}',
            'model_used': 'DeepSeek V3'
        })

def get_optimized_prompt(mode):
    """Get mode-specific prompts optimized for vision analysis"""
    prompts = {
        "Object Detection": """
        You are helping a visually impaired person understand their surroundings. 
        List the objects you see in this image clearly and concisely. For each object, provide:
        1. Object name
        2. Location (left, center, right, top, middle, bottom)

        Format your response like this:
        "I can see: [object] on the [location], [object] in the [location], [object] on the [location]"

        Keep it simple, clear, and helpful for someone who cannot see the image.
        """,

        "Scene Description": """
        You are describing a scene for someone who cannot see it. Provide a comprehensive but clear description including:
        1. Overall setting and environment type
        2. People present and what they're doing
        3. Lighting conditions and atmosphere
        4. Important details for navigation or understanding the space
        5. Any potential hazards or important features

        Make your description vivid but practical for audio consumption.
        """,

        "Money Counter": """
        You are helping someone identify and count money or currency in this image.

        Look carefully for any bills, coins, or monetary items and provide:
        1. Each type of currency/denomination visible
        2. Quantity of each denomination
        3. Total estimated value
        4. Condition of the money (if relevant)

        If no money is visible, clearly state: "No currency or money detected in this image."
        Be accurate and detailed in your counting.
        """,

        "Reading Mode": """
        You are helping someone read text that appears in this image.

        Please identify and transcribe ALL visible text including:
        1. Signs and labels
        2. Documents or papers
        3. Digital displays or screens
        4. Handwritten text
        5. Text on products or packages

        Provide the exact text as it appears. If text is unclear, mention that.
        If no readable text is present, state: "No readable text detected in this image."

        Format multiple text elements clearly, indicating where each piece of text is located.
        """
    }

    return prompts.get(mode, prompts["Object Detection"])

@app.route('/history')
def get_history():
    """Return analysis history"""
    return jsonify(analysis_history)

@app.route('/clear_history', methods=['POST'])
def clear_history():
    """Clear analysis history"""
    global analysis_history
    analysis_history = []
    return jsonify({'success': True, 'message': 'History cleared'})

@app.route('/models', methods=['GET'])
def get_available_models():
    """Get available models from OpenRouter"""
    if not deepseek_ready or not client:
        return jsonify({'error': 'OpenRouter not available'})

    try:
        models = client.models.list()
        model_list = [
            {
                'id': model.id,
                'name': model.id,
                'supports_vision': 'vision' in model.id.lower() or 'gpt-4' in model.id.lower()
            }
            for model in models.data[:20]  # Limit to first 20 models
        ]

        return jsonify({'models': model_list})

    except Exception as e:
        return jsonify({'error': f'Failed to fetch models: {str(e)}'})

@app.route('/health')
def health_check():
    """Health check endpoint with detailed status"""
    return jsonify({
        'status': 'healthy' if deepseek_ready else 'degraded',
        'openrouter_ready': deepseek_ready,
        'vision_model': 'GPT-4 Vision (via OpenRouter)',
        'text_model': 'DeepSeek V3 (via OpenRouter)',
        'timestamp': datetime.now().isoformat(),
        'python_version': sys.version,
        'note': 'Hybrid approach: GPT-4 Vision for images, DeepSeek V3 for text',
        'troubleshooting': {
            'proxies_error': 'pip install openai==1.55.3 httpx==0.27.2',
            'api_key_error': 'Check OPENROUTER_API_KEY in environment',
            'rate_limit': 'Wait and retry, or check OpenRouter credits'
        }
    })

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)

    print("🚀 Starting AI Vision Assistant with OpenRouter Integration...")
    print(f"📊 OpenRouter ready: {deepseek_ready}")
    print("⚠️  NOTE: DeepSeek V3 does not support image analysis")
    print("✅ Using GPT-4 Vision through OpenRouter for image tasks")
    print("🎯 Using DeepSeek V3 through OpenRouter for text-only analysis")
    print("🔧 Fixed version compatibility: openai==1.55.3 + httpx==0.27.2")

    # Environment check
    if not deepseek_ready:
        print("❌ STARTUP ERROR: OpenRouter client not initialized")
        print("🔧 TROUBLESHOOTING:")
        print("   1. Check your API key")
        print("   2. Install correct package versions:")
        print("      pip install openai==1.55.3 httpx==0.27.2")
        print("   3. Restart your application")

    # Get port from environment (Render/Heroku compatible)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
    
