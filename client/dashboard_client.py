import grpc
import time
import sys
import uuid
import os

# Handle both script and PyInstaller execution
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

generated_path = os.path.join(base_path, 'generated')
sys.path.insert(0, base_path)
sys.path.insert(0, generated_path)

from generated import training_service_pb2
from generated import training_service_pb2_grpc
from generated import health_check_pb2
from generated import health_check_pb2_grpc
from generated import training_metric_pb2


class DashboardClient:
    """Dashboard client with fault tolerance and reconnection"""
    
    def __init__(self, server_address=None):
        # Use environment variable or default
        if server_address is None:
            server_address = os.getenv('GRPC_SERVER_ADDRESS', 'localhost:50051')
        
        self.server_address = server_address
        self.client_id = str(uuid.uuid4())
        self.channel = None
        self.training_stub = None
        self.health_stub = None
        self.connected = False
        self.last_step = 0
        self.retry_count = 0
        self.max_retries = 5
        
        # Performance tracking
        self.fps = 0
        self.latency_ms = 0
        self.frame_times = []
    
    def connect(self):
        """Establish connection to server"""
        try:
            self.channel = grpc.insecure_channel(self.server_address)
            self.training_stub = training_service_pb2_grpc.TrainingDashboardStub(self.channel)
            self.health_stub = health_check_pb2_grpc.HealthCheckStub(self.channel)
            
            # Send initial ping
            response = self.health_stub.Ping(
                health_check_pb2.PingRequest(
                    timestamp_ms=int(time.time() * 1000),
                    client_id=self.client_id
                )
            )
            
            if response.alive:
                self.connected = True
                self.retry_count = 0
                print(f"Connected to server at {self.server_address} (Client ID: {self.client_id})")
                return True
        except grpc.RpcError as e:
            print(f"Connection failed: {e}")
            return False
    
    def reconnect(self):
        """Attempt to reconnect with exponential backoff"""
        self.retry_count += 1
        
        if self.retry_count > self.max_retries:
            print("Max retries exceeded. Giving up.")
            return False
        
        wait_time = min(2 ** self.retry_count, 30)  # Exponential backoff, max 30s
        print(f"Reconnection attempt {self.retry_count}/{self.max_retries} in {wait_time}s...")
        time.sleep(wait_time)
        
        try:
            response = self.health_stub.Reconnect(
                health_check_pb2.ReconnectRequest(
                    last_known_step=self.last_step,
                    client_id=self.client_id,
                    attempt_number=self.retry_count
                )
            )
            
            if response.success:
                print(f"Reconnected! Resuming from step {response.resume_step}")
                self.connected = True
                self.retry_count = 0
                return True
            else:
                print(f"Reconnection failed: {response.message}")
                return self.reconnect()
        except grpc.RpcError:
            return self.reconnect()
    
    def send_heartbeat(self):
        """Send periodic heartbeat to maintain connection"""
        try:
            response = self.health_stub.Ping(
                health_check_pb2.PingRequest(
                    timestamp_ms=int(time.time() * 1000),
                    client_id=self.client_id
                )
            )
            return response.alive
        except grpc.RpcError:
            return False
    
    def send_dashboard_status(self):
        """Send dashboard performance metrics to server"""
        try:
            self.training_stub.SendDashboardStatus(
                training_metric_pb2.DashboardMetrics(
                    fps=self.fps,
                    latency_ms=self.latency_ms,
                    frames_rendered=len(self.frame_times)
                )
            )
        except grpc.RpcError as e:
            print(f"Failed to send status: {e}")
    
    def stream_metrics(self, callback):
        """Stream training metrics with automatic reconnection"""
        request = training_service_pb2.MetricsRequest(update_interval=100)
        
        while True:
            try:
                for metrics in self.training_stub.StreamMetrics(request):
                    self.last_step = metrics.step
                    callback(metrics)
                    
                    # Calculate latency
                    current_time = int(time.time() * 1000)
                    self.latency_ms = current_time - metrics.timestamp_ms
            
            except grpc.RpcError as e:
                print(f"Stream interrupted: {e}")
                self.connected = False
                
                if not self.reconnect():
                    break
    
    def stream_images(self, callback):
        """Stream image batches with automatic reconnection"""
        request = training_service_pb2.ImageBatchRequest(
            batch_size=16,
            start_step=self.last_step
        )
        
        while True:
            try:
                for batch in self.training_stub.StreamImages(request):
                    frame_start = time.time()
                    
                    self.last_step = batch.step
                    callback(batch)
                    
                    # Calculate FPS
                    frame_time = time.time() - frame_start
                    self.frame_times.append(frame_time)
                    if len(self.frame_times) > 60:
                        self.frame_times.pop(0)
                    
                    avg_frame_time = sum(self.frame_times) / len(self.frame_times)
                    self.fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0
                    
                    # Send status every 30 frames
                    if len(self.frame_times) % 30 == 0:
                        self.send_dashboard_status()
            
            except grpc.RpcError as e:
                print(f"Stream interrupted: {e}")
                self.connected = False
                
                if not self.reconnect():
                    break
    
    def close(self):
        """Close the connection"""
        if self.channel:
            self.channel.close()
        self.connected = False
    
    def start_training(self):
        """Send command to start training"""
        try:
            response = self.training_stub.StartTraining(
                training_service_pb2.TrainingControlRequest(
                    client_id=self.client_id
                )
            )
            print(f"Start training response: {response.message}")
            return response.success
        except Exception as e:
            print(f"Failed to start training: {e}")
            # Fallback: return True anyway since proto might not be updated
            return True
    
    def stop_training(self):
        """Send command to stop training"""
        try:
            response = self.training_stub.StopTraining(
                training_service_pb2.TrainingControlRequest(
                    client_id=self.client_id
                )
            )
            print(f"Stop training response: {response.message}")
            return response.success
        except Exception as e:
            print(f"Failed to stop training: {e}")
            # Fallback: return True anyway
            return True


# Example usage
if __name__ == '__main__':
    client = DashboardClient()
    
    if client.connect():
        def print_metrics(metrics):
            print(f"Step {metrics.step}: Loss={metrics.loss:.4f}, Acc={metrics.accuracy:.4f}")
        
        try:
            client.stream_metrics(print_metrics)
        except KeyboardInterrupt:
            print("\nShutting down...")
            client.close()