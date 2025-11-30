#!/bin/bash

# Create output directory
mkdir -p generated

# Generate Python code from protos
python -m grpc_tools.protoc \
    -I./protos \
    --python_out=./generated \
    --grpc_python_out=./generated \
    ./protos/health_check.proto \
    ./protos/image_batch.proto \
    ./protos/training_metric.proto \
    ./protos/training_service.proto

# Add __init__.py
touch generated/__init__.py

echo "Proto files compiled successfully!"