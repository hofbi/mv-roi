# Annotation Framework

The annotation framework can be used to generate pseudo labels from the model prediction and handle this data for manual human inspection. This includes merging and splitting images and finally convert them into the hdf5 file format.

## Naming Convention

The expected file naming contention is `key_index.suffix`, with a 6 digit integer for `index`. This is required to process the files properly. See [reindexing](annotation#reindex) to automatically convert your data into the right format.

## Generate Pseudo Label

The pseudo label generation module can be used to convert the predicted heatmaps into json label files. It provides the following CLI interface.

```shell
usage: generate_pseudo_label.py [-h] [-s SUFFIX] [-r RES] [-bt BIN_THRESHOLD]
                                [-md MIN_DIAMETER]
                                input_dir output_dir

Generate pseudo labels from predicted heatmaps

positional arguments:
  input_dir             Path to the predicted heatmaps
  output_dir            Path to the RGB images where the generated labels
                        belong to and should be stored

optional arguments:
  -h, --help            show this help message and exit
  -s SUFFIX, --suffix SUFFIX
                        Suffix of the image files. (default: .png)
  -r RES, --res RES     Single camera resolution WIDTHxHEIGHT (default:
                        640x480)
  -bt BIN_THRESHOLD, --bin_threshold BIN_THRESHOLD
                        Values over this threshold will be binarized to 1
                        (default: 96)
  -md MIN_DIAMETER, --min_diameter MIN_DIAMETER
                        Minimum diameter for an ROI in percent to the image
                        width (default: 0.05)
```

## Create ROI Consistency

The model cannot ensure to detect all ROIs consistently for all views.
To simplify the labeling process, use this module which syncs the ROI for all views based on a given camera layout

```shell
usage: create_roi_consistency.py [-h] [-o OUTPUT_DIR] [-c CAMERA_CONFIG] [-f FOV_DEGREE] [-i IOU_THRESHOLD] input_dir

Create ROI consistent label json files for multiple views

positional arguments:
  input_dir             Path to the directory which contains the images and labels in json format.

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT_DIR, --output_dir OUTPUT_DIR
                        Path to the directory where the roi consistent label files will be put. (default: _out)
  -c CAMERA_CONFIG, --camera-config CAMERA_CONFIG
                        Path to the camera config file that contains the camera positions (default: record/config/6_camera_setup.ini)
  -f FOV_DEGREE, --fov-degree FOV_DEGREE
                        Field of camera view in degree (default: 90.0)
  -i IOU_THRESHOLD, --iou-threshold IOU_THRESHOLD
                        IOU threshold to adjust if a new ROI circle need to be added (default: 0.7)
```

## Merge

The merge module can be used to combine individual frames and label files into a merged frame, to inspect all camera views at the same time. It provides the following CLI interface.

```shell
usage: merge.py [-h] [-o OUTPUT_DIR] [-s SUFFIX] [-r RES]
                [--image_topics IMAGE_TOPICS [IMAGE_TOPICS ...]]
                [--images_per_row IMAGES_PER_ROW] [--hdf5] [--reindex]
                input_dir

Merge images and json labels

positional arguments:
  input_dir             Path to the directory which contains the images and
                        labels in json format.

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT_DIR, --output_dir OUTPUT_DIR
                        Path to the directory where the generated files will
                        be put. (default: annotation)
  -s SUFFIX, --suffix SUFFIX
                        Suffix of the image files. (default: .png)
  -r RES, --res RES     Single camera resolution WIDTHxHEIGHT (default:
                        640x480)
  --image_topics IMAGE_TOPICS [IMAGE_TOPICS ...]
                        All image topics that should be should be merged
                        together. The order defines the layout of merging
                        (default: ['front_left', 'front', 'front_right',
                        'rear_left', 'rear', 'rear_right'])
  --images_per_row IMAGES_PER_ROW
                        Number of images that are aligned next to each other
                        (default: 3)
  --hdf5                Merge files into hdf5 file (default: False)
  --reindex             Reindex image and label files to a sequential
                        continuous numbering (default: False)
```

Additionally, it provides the following 2 features.

### Reindex

Run with `--reindex` to reindex the data using the correct [format](#naming-convention). It will delete frames that do not have an image for every view as we assume this means an identical timestamp. The other images will be shifted to a sequential indexing starting at `000000`.

Images generated with the recording module are not aligned and need to be reindexed before further usage.

### HDF5

Images and labels can be combined into a HDF5 file by running with `--hdf5`.

## Split

The split module can be used to split the merged images and label files back into individual ones. By default splitting the images is disabled to safe memory and speed up the runtime as usually the individual images before merging are still available. The script provides the following CLI interface.

```shell
usage: split.py [-h] [-o OUTPUT_DIR] [-s SUFFIX] [--split_images] input_dir

Split images and json labels

positional arguments:
  input_dir             Path to the directory which contains the images and
                        labels in json format.

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT_DIR, --output_dir OUTPUT_DIR
                        Path to the directory where the generated files will
                        be put. (default: annotation)
  -s SUFFIX, --suffix SUFFIX
                        Suffix of the image files. (default: .png)
  --split_images        Split merged images into individual ones. This is
                        disabled by default safe memory and speed up the
                        runtime as usually the individual images before
                        merging are still available. (default: False)

```

## Extract Data

Use `h5_extract.py` to extract data from one or more hdf5 files.

```shell
usage: h5_extract.py [-h] [-o OUTPUT_DIR] h5_files [h5_files ...]

Extract data from hdf5 file

positional arguments:
  h5_files              Path to the hdf5 files.

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT_DIR, --output_dir OUTPUT_DIR
                        Path to the output directory (default: annotation)
```
