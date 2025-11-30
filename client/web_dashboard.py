from flask import Flask, render_template, jsonify
from flask_cors import CORS
import threading
import base64
import sys
import os

# Fix import paths
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Try to import from same directory (for EXE) or from client module (for script)
try:
    from dashboard_client import DashboardClient
except ImportError:
    from client.dashboard_client import DashboardClient
    
# Set template folder to parent directory's templates folder
template_dir = os.path.join(parent_dir, 'templates')
app = Flask(__name__, template_folder=template_dir)
CORS(app)

# Global state
dashboard_state = {
    'metrics': [],
    'images': [],
    'fps': 0,
    'latency_ms': 0,
    'current_step': 0
}

client = None

def metrics_callback(metrics):
    """Handle incoming metrics"""
    dashboard_state['metrics'].append({
        'step': metrics.step,
        'loss': metrics.loss,
        'accuracy': metrics.accuracy,
        'timestamp': metrics.timestamp_ms
    })
    
    # Keep only last 100 points
    if len(dashboard_state['metrics']) > 100:
        dashboard_state['metrics'].pop(0)
    
    dashboard_state['current_step'] = metrics.step

def images_callback(batch):
    """Handle incoming image batch"""
    images_data = []
    
    for labeled_img in batch.images:
        # Convert bytes to base64 for web display
        img_base64 = base64.b64encode(labeled_img.image.pixel_data).decode('utf-8')
        
        images_data.append({
            'data': img_base64,
            'width': labeled_img.image.width,
            'height': labeled_img.image.height,
            'ground_truth': labeled_img.ground_truth,
            'prediction': labeled_img.prediction,
            'confidence': labeled_img.confidence
        })
    
    dashboard_state['images'] = images_data
    dashboard_state['fps'] = client.fps
    dashboard_state['latency_ms'] = client.latency_ms

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/status')
def get_status():
    return jsonify({
        'connected': client.connected if client else False,
        'fps': dashboard_state['fps'],
        'latency_ms': dashboard_state['latency_ms'],
        'current_step': dashboard_state['current_step']
    })

@app.route('/api/metrics')
def get_metrics():
    return jsonify(dashboard_state['metrics'])

@app.route('/api/images')
def get_images():
    return jsonify(dashboard_state['images'])

def start_client():
    """Start the gRPC client in background threads"""
    global client
    client = DashboardClient()
    
    if client.connect():
        # Start metrics stream in separate thread
        metrics_thread = threading.Thread(
            target=client.stream_metrics,
            args=(metrics_callback,),
            daemon=True
        )
        metrics_thread.start()
        
        # Start images stream in separate thread
        images_thread = threading.Thread(
            target=client.stream_images,
            args=(images_callback,),
            daemon=True
        )
        images_thread.start()

if __name__ == '__main__':
    # Start gRPC client
    start_client()
    
    # Start Flask server
    app.run(host='0.0.0.0', port=5000, debug=False)