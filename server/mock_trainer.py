import numpy as np
import threading
import time
from PIL import Image
import io
import os
import sys


class MockTrainer:
    """Simulates ML training using MNIST (3k subset) for dashboard testing"""

    def __init__(self):
        self.is_training = False
        self.is_running = False
        self.current_step = 0
        self.batch_size = 16
        self.max_steps = 1000

        # Current batch data
        self.current_batch = None
        self.current_metrics = {'loss': 2.3, 'accuracy': 0.1}

        # MNIST digit classes (0–9)
        self.classes = [str(i) for i in range(10)]

        # Dataset storage
        self.images = None   # (3000, 28, 28)
        self.labels = None   # (3000,)

        # Load MNIST dataset
        self.load_mnist_3k()

        # Training thread
        self.training_thread = None

    def load_mnist_3k(self):
        """Load MNIST 3k subset safely (works for PyInstaller)"""

        # Handle PyInstaller vs normal Python
        if hasattr(sys, '_MEIPASS'):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))

        dataset_path = os.path.join(base_dir, "datasets", "mnist_3k.npz")

        try:
            data = np.load(dataset_path)
            self.images = data["images"]
            self.labels = data["labels"]
            print(f"MNIST 3k loaded: {len(self.images)} images")
        except Exception as e:
            print(f"Failed to load MNIST dataset: {e}")
            self.images = None
            self.labels = None


    def get_mnist_image(self, idx):
        """Convert MNIST image to PNG bytes (RGB for frontend compatibility)"""
        if self.images is None:
            return self.generate_fake_image(0)

        img_array = self.images[idx]  # (28, 28) grayscale
        pil_img = Image.fromarray(img_array, mode="L").convert("RGB")

        buf = io.BytesIO()
        pil_img.save(buf, format="PNG")

        return {
            'pixels': buf.getvalue(),
            'width': 28,
            'height': 28
        }

    def generate_fake_image(self, label_idx):
        """Fallback: generate random grayscale image"""
        img = np.random.randint(0, 255, (28, 28), dtype=np.uint8)

        pil_img = Image.fromarray(img, mode="L").convert("RGB")
        img_bytes = io.BytesIO()
        pil_img.save(img_bytes, format="PNG")

        return {
            'pixels': img_bytes.getvalue(),
            'width': 28,
            'height': 28
        }

    def training_loop(self):
        """Simulated training loop that can be paused"""
        self.is_running = True

        while self.is_running and self.current_step < self.max_steps:
            if not self.is_training:
                time.sleep(0.5)
                continue

            time.sleep(0.1)  # Simulated computation time
            self.current_step += 1

            # Fake learning curve
            self.current_metrics['loss'] = 2.3 * np.exp(-self.current_step / 200) + 0.1
            self.current_metrics['accuracy'] = min(
                0.95,
                0.1 + 0.85 * (1 - np.exp(-self.current_step / 200))
            )

            images = []
            labels = []
            predictions = []
            confidences = []

            for _ in range(self.batch_size):
                if self.images is not None:
                    idx = np.random.randint(0, len(self.images))
                    true_label_idx = self.labels[idx]
                    images.append(self.get_mnist_image(idx))
                else:
                    true_label_idx = np.random.randint(0, len(self.classes))
                    images.append(self.generate_fake_image(true_label_idx))

                if np.random.random() < self.current_metrics['accuracy']:
                    pred_label_idx = true_label_idx
                    confidence = np.random.uniform(0.7, 0.99)
                else:
                    pred_label_idx = np.random.randint(0, len(self.classes))
                    confidence = np.random.uniform(0.4, 0.7)

                labels.append(self.classes[int(true_label_idx)])
                predictions.append(self.classes[int(pred_label_idx)])
                confidences.append(confidence)

            self.current_batch = {
                'images': images,
                'labels': labels,
                'predictions': predictions,
                'confidences': confidences
            }

            if self.current_step % 10 == 0:
                status = "TRAINING" if self.is_training else "PAUSED"
                print(
                    f"[{status}] Step {self.current_step}: "
                    f"Loss={self.current_metrics['loss']:.4f}, "
                    f"Acc={self.current_metrics['accuracy']:.4f}"
                )

    def start_training(self):
        """Start or resume training"""
        if not self.is_running:
            self.is_training = True
            self.training_thread = threading.Thread(
                target=self.training_loop,
                daemon=True
            )
            self.training_thread.start()
            print("Training started!")
        else:
            self.is_training = True
            print("Training resumed!")
        return True

    def pause_training(self):
        """Pause training"""
        self.is_training = False
        print("Training paused!")
        return True

    def stop_training(self):
        """Stop training completely"""
        self.is_training = False
        self.is_running = False
        if self.training_thread:
            self.training_thread.join(timeout=2)
        print("Training stopped!")
        return True

    def reset_training(self):
        """Reset training state"""
        self.stop_training()
        self.current_step = 0
        self.current_metrics = {'loss': 2.3, 'accuracy': 0.1}
        print("Training reset!")

    def get_current_batch(self):
        """Get current batch data"""
        return self.current_batch if self.current_batch else {
            'images': [],
            'labels': [],
            'predictions': [],
            'confidences': []
        }

    def get_current_metrics(self):
        """Get current metrics"""
        return self.current_metrics
