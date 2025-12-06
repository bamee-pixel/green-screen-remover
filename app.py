from flask import Flask, render_template, request, jsonify
from processor import process_image
import base64
import traceback

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        image_data_b64 = data.get('image')
        color = data.get('color', '#00FF00')
        sensitivity = float(data.get('sensitivity', 50))
        smoothing = float(data.get('smoothing', 0))

        if not image_data_b64:
            return jsonify({'error': 'No image provided'}), 400

        # Remove header if present (e.g., "data:image/png;base64,")
        if ',' in image_data_b64:
            image_data_b64 = image_data_b64.split(',')[1]

        image_bytes = base64.b64decode(image_data_b64)

        processed_bytes = process_image(image_bytes, color, sensitivity, smoothing)

        processed_b64 = base64.b64encode(processed_bytes).decode('utf-8')

        return jsonify({
            'processed_image': f"data:image/png;base64,{processed_b64}"
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
