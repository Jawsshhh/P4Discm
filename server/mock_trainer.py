import numpy as np
import threading
import time
from PIL import Image
import io
import torch
import torchvision
import torchvision.transforms as transforms

class MockTrainer:
    """Simulates ML training with real CIFAR-10 images"""
    
    def __init__(self, use_real_data=True):
        self.is_training = False
        self.current_step = 0
        self.batch_size = 16
        self.max_steps = 1000
        
        # Current batch data
        self.current_batch = None
        self.current_metrics = {'loss': 2.3, 'accuracy': 0.1}
        
        # CIFAR-10 class names
        self.classes = ['airplane', 'automobile', 'bird', 'cat', 'deer', 
                       'dog', 'frog', 'horse', 'ship', 'truck']
        
        # Load CIFAR-10 dataset
        self.use_real_data = use_real_data
        if use_real_data:
            print("Loading CIFAR-10 dataset...")
            self.load_cifar10()
            print(f"Loaded {len(self.dataset)} training images")
        else:
            self.dataset = None
    
    def load_cifar10(self):
        """Load CIFAR-10 dataset"""
        # Download and load CIFAR-10
        transform = transforms.Compose([
            transforms.ToTensor(),
        ])
        
        self.dataset = torchvision.datasets.CIFAR10(
            root='./data', 
            train=True, 
            download=True, 
            transform=transform
        )
        
        # Create dataloader
        self.dataloader = torch.utils.data.DataLoader(
            self.dataset,
            batch_size=self.batch_size,
            shuffle=True,
            num_workers=0  # 0 for Windows compatibility
        )
        
        # Create iterator
        self.data_iter = iter(self.dataloader)
    
    def get_next_batch(self):
        """Get next batch from CIFAR-10"""
        try:
            images, labels = next(self.data_iter)
        except StopIteration:
            # Restart iterator when dataset ends
            self.data_iter = iter(self.dataloader)
            images, labels = next(self.data_iter)
        
        return images, labels
    
    def tensor_to_bytes(self, img_tensor):
        """Convert PyTorch tensor to bytes for gRPC"""
        # img_tensor shape: [C, H, W], values in [0, 1]
        img_np = img_tensor.permute(1, 2, 0).numpy()  # [H, W, C]
        img_np = (img_np * 255).astype(np.uint8)  # Convert to [0, 255]
        
        # Convert to PIL Image
        pil_img = Image.fromarray(img_np, 'RGB')
        
        # Convert to bytes
        img_bytes = io.BytesIO()
        pil_img.save(img_bytes, format='PNG')
        
        return {
            'pixels': img_bytes.getvalue(),
            'width': 32,
            'height': 32
        }
    
    def generate_fake_image(self, label_idx):
        """Generate a random colored image (fallback)"""
        img = np.random.randint(0, 255, (32, 32, 3), dtype=np.uint8)
        pil_img = Image.fromarray(img, 'RGB')
        img_bytes = io.BytesIO()
        pil_img.save(img_bytes, format='PNG')
        
        return {
            'pixels': img_bytes.getvalue(),
            'width': 32,
            'height': 32
        }
    
    def training_loop(self):
        """Simulated training loop with real data"""
        while self.is_training and self.current_step < self.max_steps:
            time.sleep(0.1)  # 100ms per step
            
            self.current_step += 1
            
            # Update metrics (improving over time)
            self.current_metrics['loss'] = 2.3 * np.exp(-self.current_step / 200) + 0.1
            self.current_metrics['accuracy'] = min(0.95, 0.1 + 0.85 * (1 - np.exp(-self.current_step / 200)))
            
            # Generate batch
            images = []
            labels_list = []
            predictions = []
            confidences = []
            
            if self.use_real_data:
                # Use real CIFAR-10 data
                img_batch, label_batch = self.get_next_batch()
                
                for i in range(min(self.batch_size, len(img_batch))):
                    true_label_idx = label_batch[i].item()
                    
                    # Simulate prediction (correct with increasing probability)
                    if np.random.random() < self.current_metrics['accuracy']:
                        pred_label_idx = true_label_idx
                        confidence = np.random.uniform(0.7, 0.99)
                    else:
                        pred_label_idx = np.random.randint(0, len(self.classes))
                        confidence = np.random.uniform(0.4, 0.7)
                    
                    images.append(self.tensor_to_bytes(img_batch[i]))
                    labels_list.append(self.classes[true_label_idx])
                    predictions.append(self.classes[pred_label_idx])
                    confidences.append(confidence)
            else:
                # Use fake data
                for i in range(self.batch_size):
                    true_label_idx = np.random.randint(0, len(self.classes))
                    
                    if np.random.random() < self.current_metrics['accuracy']:
                        pred_label_idx = true_label_idx
                        confidence = np.random.uniform(0.7, 0.99)
                    else:
                        pred_label_idx = np.random.randint(0, len(self.classes))
                        confidence = np.random.uniform(0.4, 0.7)
                    
                    images.append(self.generate_fake_image(true_label_idx))
                    labels_list.append(self.classes[true_label_idx])
                    predictions.append(self.classes[pred_label_idx])
                    confidences.append(confidence)
            
            self.current_batch = {
                'images': images,
                'labels': labels_list,
                'predictions': predictions,
                'confidences': confidences
            }
            
            if self.current_step % 10 == 0:
                print(f"Step {self.current_step}: Loss={self.current_metrics['loss']:.4f}, Acc={self.current_metrics['accuracy']:.4f}")
    
    def start_training(self):
        """Start the training thread"""
        self.is_training = True
        self.training_thread = threading.Thread(target=self.training_loop)
        self.training_thread.start()
    
    def stop_training(self):
        """Stop training"""
        self.is_training = False
        if hasattr(self, 'training_thread'):
            self.training_thread.join()
    
    def get_current_batch(self):
        """Get current batch data"""
        return self.current_batch if self.current_batch else {
            'images': [], 'labels': [], 'predictions': [], 'confidences': []
        }
    
    def get_current_metrics(self):
        """Get current metrics"""
        return self.current_metrics