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
rm -rf "$DATA_PATH"/testing/tfrecords "$DATA_PATH"/testing/image_features_alexnet

pushd "$BDDA_PATH"

echo "Testing the ROI predictions ..."

echo "Convert frames to tf records..."
python3 write_tfrecords_for_inference.py \
    --data_dir="$DATA_PATH"/testing \
    --n_divides=2 \
    --longest_seq=35

echo "Create AlexNet feature maps..."
# TODO check if finetuned model should be used
# https://github.com/pascalxia/driver_attention_prediction/issues/8
python3 make_feature_maps.py \
    --data_dir="$DATA_PATH"/testing \
    --model_dir="$BDDA_PATH"/pretrained_models/model_for_inference

echo "Create tf records with AlexNet features and gaze maps..."
python3 write_tfrecords.py \
    --data_dir="$DATA_PATH"/testing \
    --n_divides=2 \
    --feature_name=alexnet \
    --image_size 288 512 \
    --longest_seq=35

echo "Test the predictions..."
python3 predict.py \
    --data_dir="$DATA_PATH" \
    --model_dir="$MODEL_PATH" \
    --batch_size=1 \
    --feature_name=alexnet \
    --feature_map_channels=256
