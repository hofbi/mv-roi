#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BDDA_PATH="$SCRIPT_DIR/driver_attention_prediction"
DATA_PATH="$SCRIPT_DIR/data"
MODEL_PATH="$BDDA_PATH"/pretrained_models/model_for_inference

if [ -n "$1" ]; then
    MODEL_PATH=$(pwd)/$1
fi

echo "Clean up old states..."
rm -rf "$DATA_PATH"/inference/tfrecords

pushd "$BDDA_PATH"

echo "Generating ROI predictions ..."

echo "Convert frames to tf records..."
python3 write_tfrecords_for_inference.py \
    --data_dir="$DATA_PATH"/inference \
    --n_divides=2 \
    --longest_seq=35

echo "Generate ROI predictions..."
python3 infer.py \
    --data_dir="$DATA_PATH" \
    --model_dir="$MODEL_PATH"
