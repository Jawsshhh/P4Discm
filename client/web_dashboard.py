from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import threading
import base64
import sys
import logging
import os

# Handle both script and PyInstaller execution
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
    from dashboard_client import DashboardClient
else:
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from dashboard_client import DashboardClient

# Set template folder
template_dir = os.path.join(base_path, 'templates')
app = Flask(__name__, template_folder=template_dir)
CORS(app)

# Global state
dashboard_state = {
    'metrics': [],
    'images': [],
    'fps': 0,
    'latency_ms': 0,
    'current_step': 0,
    'is_training': False
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
        'current_step': dashboard_state['current_step'],
        'is_training': dashboard_state['is_training']
    })

@app.route('/api/metrics')
def get_metrics():
    return jsonify(dashboard_state['metrics'])

@app.route('/api/images')
def get_images():
    return jsonify(dashboard_state['images'])

@app.route('/api/control/start', methods=['POST'])
def start_training():
    """Start training on the server"""
    global client
    try:
        if client and client.connected:
            # Send start command to server
            success = client.start_training()
            if success:
                dashboard_state['is_training'] = True
                return jsonify({'success': True, 'message': 'Training started'})
            else:
                return jsonify({'success': False, 'message': 'Failed to start training'}), 500
        else:
            return jsonify({'success': False, 'message': 'Not connected to server'}), 503
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/control/stop', methods=['POST'])
def stop_training():
    """Stop training on the server"""
    global client
    try:
        if client and client.connected:
            # Send stop command to server
            success = client.stop_training()
            if success:
                dashboard_state['is_training'] = False
                return jsonify({'success': True, 'message': 'Training stopped'})
            else:
                return jsonify({'success': False, 'message': 'Failed to stop training'}), 500
        else:
            return jsonify({'success': False, 'message': 'Not connected to server'}), 503
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

def start_client():
    """Start the gRPC client in background threads"""
    global client
    client = DashboardClient()
    
    if client.connect():
        metrics_thread = threading.Thread(
            target=client.stream_metrics,
            args=(metrics_callback,),
            daemon=True
        )
        metrics_thread.start()
        
        images_thread = threading.Thread(
            target=client.stream_images,
            args=(images_callback,),
            daemon=True
        )
        images_thread.start()

        heartbeat_thread = threading.Thread(
            target=lambda: client.periodic_heartbeat(),
            daemon=True
        )
        heartbeat_thread.start()

if __name__ == '__main__':
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)  # Only show errors
    start_client()
    
    app.run(host='0.0.0.0', port=5000, debug=False)