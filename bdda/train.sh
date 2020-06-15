#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BDDA_PATH="$SCRIPT_DIR/driver_attention_prediction"
DATA_PATH="$SCRIPT_DIR/data"
DATE=$(date +'%Y-%m-%d')
EXPERIMENT_PATH="$BDDA_PATH"/logs/MV-ROI-"$DATE"
MODEL_PATH="$BDDA_PATH"/pretrained_models/model_for_inference

if [ -n "$1" ]; then
    MODEL_PATH=$(pwd)/$1
fi

echo "Clean up old states..."
rm -rf "$DATA_PATH"/training/tfrecords "$DATA_PATH"/training/image_features_alexnet
rm -rf "$DATA_PATH"/validation/tfrecords "$DATA_PATH"/validation/image_features_alexnet

pushd "$BDDA_PATH"

echo "Training the model ..."

echo "Convert frames to tf records..."
python3 write_tfrecords_for_inference.py \
    --data_dir="$DATA_PATH"/training \
    --n_divides=2 \
    --longest_seq=35

python3 write_tfrecords_for_inference.py \
    --data_dir="$DATA_PATH"/validation \
    --n_divides=2 \
    --longest_seq=35

echo "Create AlexNet feature maps..."
python3 make_feature_maps.py \
    --data_dir="$DATA_PATH"/training \
    --model_dir="$MODEL_PATH"

python3 make_feature_maps.py \
    --data_dir="$DATA_PATH"/validation \
    --model_dir="$MODEL_PATH"

echo "Create tf records with AlexNet features and gaze maps..."
python3 write_tfrecords.py \
    --data_dir="$DATA_PATH"/training \
    --n_divides=2 \
    --feature_name=alexnet \
    --image_size 288 512 \
    --longest_seq=35

python3 write_tfrecords.py \
    --data_dir="$DATA_PATH"/validation \
    --n_divides=2 \
    --feature_name=alexnet \
    --image_size 288 512 \
    --longest_seq=35

echo "Copy model for fintetuning to create a new experiment..."
mkdir -p "$EXPERIMENT_PATH"
cp "$BDDA_PATH"/pretrained_models/model_for_finetuning/* "$EXPERIMENT_PATH"/

echo "Train..."
python3 train.py \
    --data_dir="$DATA_PATH" \
    --model_dir="$EXPERIMENT_PATH" \
    --batch_size=10 \
    --n_steps=6 \
    --feature_name=alexnet \
    --train_epochs=500 \
    --epochs_before_validation=3 \
    --image_size 288 512 \
    --feature_map_channels=256 \
    --quick_summary_period=20 \
    --slow_summary_period=100
