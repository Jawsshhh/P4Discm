import grpc
from concurrent import futures
import time
import sys
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
from generated import image_batch_pb2
from generated import training_metric_pb2


# Import mock trainer
if getattr(sys, 'frozen', False):
    import mock_trainer
else:
    from server import mock_trainer


class HealthCheckService(health_check_pb2_grpc.HealthCheckServicer):
    """Implements fault tolerance and connection management"""
    
    def __init__(self):
        self.connected_clients = {}
        self.max_retries = 5
    
    def Ping(self, request, context):
        """Respond to heartbeat pings"""
        client_id = request.client_id
        timestamp = int(time.time() * 1000)
        
        if client_id not in self.connected_clients:
            self.connected_clients[client_id] = {
                'retry_count': 0,
                'connected_since': timestamp
            }
        
        return health_check_pb2.PingResponse(
            alive=True,
            timestamp_ms=timestamp,
            retry_count=self.connected_clients[client_id]['retry_count'],
            max_retries=self.max_retries
        )
    
    def Reconnect(self, request, context):
        """Handle reconnection attempts"""
        client_id = request.client_id
        attempt = request.attempt_number
        
        if attempt > self.max_retries:
            return health_check_pb2.ReconnectResponse(
                success=False,
                resume_step=0,
                message="Max retries exceeded",
                attempts_remaining=0,
                retry_after_ms=0,
                status=health_check_pb2.MAX_RETRIES_EXCEEDED
            )
        
        # Simulate successful reconnection
        return health_check_pb2.ReconnectResponse(
            success=True,
            resume_step=request.last_known_step,
            message="Reconnected successfully",
            attempts_remaining=self.max_retries - attempt,
            retry_after_ms=1000,
            status=health_check_pb2.SUCCESS
        )
    
    def GetConnectionStatus(self, request, context):
        """Get current connection status"""
        client_id = request.client_id
        client_info = self.connected_clients.get(client_id, {})
        
        return health_check_pb2.ConnectionStatus(
            is_connected=client_id in self.connected_clients,
            failed_attempts=client_info.get('retry_count', 0),
            max_allowed_attempts=self.max_retries,
            connected_since_ms=client_info.get('connected_since', 0),
            last_failure_ms=0,
            status_message="Connected" if client_id in self.connected_clients else "Disconnected"
        )


class TrainingDashboardService(training_service_pb2_grpc.TrainingDashboardServicer):
    """Streams training data to dashboard clients"""
    
    def __init__(self, trainer):
        self.trainer = trainer
        self.current_step = 0
    
    def StartTraining(self, request, context):
        """Handle start training request"""
        print(f"Received start training request from client: {request.client_id}")
        success = self.trainer.start_training()
        return training_service_pb2.TrainingControlResponse(
            success=success,
            message="Training started" if success else "Failed to start training",
            is_training=self.trainer.is_training,
            current_step=self.trainer.current_step
        )
    
    def StopTraining(self, request, context):
        """Handle stop training request"""
        print(f"Received stop training request from client: {request.client_id}")
        success = self.trainer.pause_training()
        return training_service_pb2.TrainingControlResponse(
            success=success,
            message="Training stopped" if success else "Failed to stop training",
            is_training=self.trainer.is_training,
            current_step=self.trainer.current_step
        )
    
    def GetTrainingStatus(self, request, context):
        """Get current training status"""
        metrics = self.trainer.get_current_metrics()
        return training_service_pb2.TrainingStatusResponse(
            is_training=self.trainer.is_training,
            current_step=self.trainer.current_step,
            max_steps=self.trainer.max_steps,
            current_loss=metrics['loss'],
            current_accuracy=metrics['accuracy']
        )
    
    def StreamMetrics(self, request, context):
        """Stream training metrics (loss, accuracy)"""
        update_interval = request.update_interval
        
        while True:
            if self.current_step < self.trainer.current_step:
                self.current_step = self.trainer.current_step
                
                metrics = self.trainer.get_current_metrics()
                yield training_metric_pb2.TrainingMetrics(
                    step=self.current_step,
                    loss=metrics['loss'],
                    accuracy=metrics['accuracy'],
                    timestamp_ms=int(time.time() * 1000)
                )
            
            time.sleep(update_interval / 1000.0)  # Convert ms to seconds
    
    def StreamImages(self, request, context):
        """Stream image batches with predictions"""
        batch_size = request.batch_size
        start_step = request.start_step
        
        self.current_step = start_step
        
        while True:
            if self.current_step < self.trainer.current_step:
                self.current_step = self.trainer.current_step
                
                batch = self.trainer.get_current_batch()
                labeled_images = []
                
                # Take up to 16 images (or batch_size)
                for i in range(min(16, len(batch['images']))):
                    img_data = batch['images'][i]
                    
                    labeled_img = image_batch_pb2.LabeledImage(
                        image=image_batch_pb2.Image(
                            pixel_data=img_data['pixels'],
                            width=img_data['width'],
                            height=img_data['height'],
                            format="RGB"
                        ),
                        ground_truth=batch['labels'][i],
                        prediction=batch['predictions'][i],
                        confidence=batch['confidences'][i]
                    )
                    labeled_images.append(labeled_img)
                
                yield image_batch_pb2.ImageBatch(
                    step=self.current_step,
                    images=labeled_images,
                    timestamp_ms=int(time.time() * 1000)
                )
            
            time.sleep(0.1)  # Check every 100ms
    
    def SendDashboardStatus(self, request, context):
        """Receive dashboard performance metrics"""
        print(f"Dashboard Status - FPS: {request.fps:.2f}, Latency: {request.latency_ms:.2f}ms")
        
        return training_service_pb2.StatusAck(
            success=True,
            message="Status received"
        )


def serve(trainer, port=50051):
    """Start the gRPC server"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # Add services
    training_service_pb2_grpc.add_TrainingDashboardServicer_to_server(
        TrainingDashboardService(trainer), server
    )
    health_check_pb2_grpc.add_HealthCheckServicer_to_server(
        HealthCheckService(), server
    )
    
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    print(f"Server started on port {port}")
    print("Waiting for client to send start command...")
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        trainer.stop_training()
        server.stop(0)


if __name__ == '__main__':
    trainer = mock_trainer.MockTrainer()
    # Don't start training automatically - wait for client command
    serve(trainer)