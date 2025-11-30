import numpy as np
import threading
import time
from PIL import Image
import io

class MockTrainer:
    """Simulates ML training for testing the dashboard"""
    
    def __init__(self):
        self.is_training = False
        self.is_running = False  # Controls the thread
        self.current_step = 0
        self.batch_size = 16
        self.max_steps = 1000
        
        # Current batch data
        self.current_batch = None
        self.current_metrics = {'loss': 2.3, 'accuracy': 0.1}
        
        # Class names for image classification
        self.classes = ['cat', 'dog', 'bird', 'fish', 'horse', 'deer', 'frog', 'ship', 'car', 'plane']
        
        # Training thread
        self.training_thread = None
    
    def generate_fake_image(self, label_idx):
        """Generate a random colored image"""
        # Create a 64x64 image with random colors
        img = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        
        # Convert to bytes
        pil_img = Image.fromarray(img, 'RGB')
        img_bytes = io.BytesIO()
        pil_img.save(img_bytes, format='PNG')
        
        return {
            'pixels': img_bytes.getvalue(),
            'width': 64,
            'height': 64
        }
    
    def training_loop(self):
        """Simulated training loop that can be paused"""
        self.is_running = True
        
        while self.is_running and self.current_step < self.max_steps:
            # Check if training is active
            if not self.is_training:
                time.sleep(0.5)  # Wait while paused
                continue
            
            # Simulate training step
            time.sleep(0.1)  # 100ms per step
            
            self.current_step += 1
            
            # Update metrics (improving over time)
            self.current_metrics['loss'] = 2.3 * np.exp(-self.current_step / 200) + 0.1
            self.current_metrics['accuracy'] = min(0.95, 0.1 + 0.85 * (1 - np.exp(-self.current_step / 200)))
            
            # Generate batch
            images = []
            labels = []
            predictions = []
            confidences = []
            
            for i in range(self.batch_size):
                true_label_idx = np.random.randint(0, len(self.classes))
                
                # Prediction is correct with increasing probability
                if np.random.random() < self.current_metrics['accuracy']:
                    pred_label_idx = true_label_idx
                    confidence = np.random.uniform(0.7, 0.99)
                else:
                    pred_label_idx = np.random.randint(0, len(self.classes))
                    confidence = np.random.uniform(0.4, 0.7)
                
                images.append(self.generate_fake_image(true_label_idx))
                labels.append(self.classes[true_label_idx])
                predictions.append(self.classes[pred_label_idx])
                confidences.append(confidence)
            
            self.current_batch = {
                'images': images,
                'labels': labels,
                'predictions': predictions,
                'confidences': confidences
            }
            
            if self.current_step % 10 == 0:
                status = "TRAINING" if self.is_training else "PAUSED"
                print(f"[{status}] Step {self.current_step}: Loss={self.current_metrics['loss']:.4f}, Acc={self.current_metrics['accuracy']:.4f}")
    
    def start_training(self):
        """Start or resume training"""
        if not self.is_running:
            # Start the training thread if not running
            self.is_training = True
            self.training_thread = threading.Thread(target=self.training_loop)
            self.training_thread.start()
            print("Training started!")
        else:
            # Resume training
            self.is_training = True
            print("Training resumed!")
        return True
    
    def pause_training(self):
        """Pause training without stopping the thread"""
        self.is_training = False
        print("Training paused!")
        return True
    
    def stop_training(self):
        """Stop training completely"""
        self.is_training = False
        self.is_running = False
        if hasattr(self, 'training_thread') and self.training_thread:
            self.training_thread.join(timeout=2)
        print("Training stopped!")
        return True
    
    def reset_training(self):
        """Reset training to step 0"""
        self.stop_training()
        self.current_step = 0
        self.current_metrics = {'loss': 2.3, 'accuracy': 0.1}
        print("Training reset!")
    
    def get_current_batch(self):
        """Get current batch data"""
        return self.current_batch if self.current_batch else {
            'images': [], 'labels': [], 'predictions': [], 'confidences': []
        }
    
    def get_current_metrics(self):
        """Get current metrics"""
        return self.current_metrics