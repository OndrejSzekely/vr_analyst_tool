#!/usr/bin/env bash
PYTHON3_PATH=""

if [ -n "$PYTHON3_PATH" ]; then
    echo "CUSTOM PYTHON PATH SET"
else
    PYTHON3_PATH="python3"
    echo "DEFAULT PYTHON PATH SET"
fi

cd ..
mkdir ./unit_and_integration_test/temp
mkdir ./unit_and_integration_test/temp/binary_classifier
mkdir ./unit_and_integration_test/temp/binary_classifier/data
mkdir ./unit_and_integration_test/temp/binary_classifier/performance
mkdir ./unit_and_integration_test/temp/multiclass_classifier
mkdir ./unit_and_integration_test/temp/multiclass_classifier/data
mkdir ./unit_and_integration_test/temp/multiclass_classifier/performance
mkdir ./unit_and_integration_test/temp/multiclass_classifier/sorted_images
mkdir ./unit_and_integration_test/temp/negative_tiles
mkdir ./unit_and_integration_test/temp/testing_data_tiling_aux
mkdir ./unit_and_integration_test/temp/testing_data_cropping_aux
mkdir ./unit_and_integration_test/temp/tiling_classifier_output
mkdir ./unit_and_integration_test/temp/cropping_classifier_output
mkdir ./unit_and_integration_test/temp/recursive_classifier_output
cp -r ./unit_and_integration_test/data/testing_data ./unit_and_integration_test/temp/testing_data_tiling_aux
cp -r ./unit_and_integration_test/data/testing_data ./unit_and_integration_test/temp/testing_data_cropping_aux


echo "************************"
echo "RUNNING TEST #1: VR Analyst tool setting"
$PYTHON3_PATH "./run_scripts/run_ANALYST_TOOL_SETTING.py" --output_writer "file"
ret=$?
if [ $ret -ne 0 ]; then
    echo " - FAILED"
    exit
else
    echo " - PASSED"
fi

echo "RUNNING TEST #2: Classifiers list"
$PYTHON3_PATH "./run_scripts/run_CLASSIFIER_classifiers_list.py" --output_writer "file"
ret=$?
if [ $ret -ne 0 ]; then
    echo " - FAILED"
    exit
else
    echo " - PASSED"
fi

echo "RUNNING TEST #3: Downloading images"
$PYTHON3_PATH "./run_scripts/run_IMAGE_download_images.py" --output_writer "file" --conf_file "./unit_and_integration_test/configs/test_json_download_images.json"
ret=$?
if [ $ret -ne 0 ]; then
    echo " - FAILED"
    exit
else
    echo " - PASSED"
fi

echo "RUNNING TEST #4: Checking directory"
$PYTHON3_PATH "./run_scripts/run_IMAGE_check_directory.py" --output_writer "file" --conf_file "./unit_and_integration_test/configs/test_json_check_directory.json"
ret=$?
if [ $ret -ne 0 ]; then
    echo " - FAILED"
    exit
else
    echo " - PASSED"
fi

echo "RUNNING TEST #5: Sets creation for binary classifier"
$PYTHON3_PATH "./run_scripts/run_CLASSIFIER_sets_creation.py" --output_writer "file" --conf_file "./unit_and_integration_test/configs/test_json_sets_creation_binary_classifier.json"
ret=$?
if [ $ret -ne 0 ]; then
    echo " - FAILED"
    exit
else
    echo " - PASSED"
fi

echo "RUNNING TEST #6: Training binary classifier"
$PYTHON3_PATH "./run_scripts/run_CLASSIFIER_train_classifier.py" --output_writer "file" --conf_file "./unit_and_integration_test/configs/test_json_train_binary_classifier.json"
ret=$?
if [ $ret -ne 0 ]; then
    echo " - FAILED"
    exit
else
    echo " - PASSED"
fi

echo "RUNNING TEST #7: Performance measurement of binary classifier"
$PYTHON3_PATH "./run_scripts/run_CLASSIFIER_measure_performance.py" --output_writer "file" --conf_file "./unit_and_integration_test/configs/test_json_measure_performance_binary_classifier.json"
ret=$?
if [ $ret -ne 0 ]; then
    echo " - FAILED"
    exit
else
    echo " - PASSED"
fi

echo "RUNNING TEST #8: Updating classifier with additional images"
$PYTHON3_PATH "./run_scripts/run_CLASSIFIER_update_classifier.py" --output_writer "file" --conf_file "./unit_and_integration_test/configs/test_json_update_binary_classifier.json"
ret=$?
if [ $ret -ne 0 ]; then
    echo " - FAILED"
    exit
else
    echo " - PASSED"
fi

echo "RUNNING TEST #9: Sets creation for multiclass classifier"
$PYTHON3_PATH "./run_scripts/run_CLASSIFIER_sets_creation.py" --output_writer "file" --conf_file "./unit_and_integration_test/configs/test_json_sets_creation_multiclass_classifier.json"
ret=$?
if [ $ret -ne 0 ]; then
    echo " - FAILED"
    exit
else
    echo " - PASSED"
fi

echo "RUNNING TEST #10: Training multiclass classifier"
$PYTHON3_PATH "./run_scripts/run_CLASSIFIER_train_classifier.py" --output_writer "file" --conf_file "./unit_and_integration_test/configs/test_json_train_multiclass_classifier.json"
ret=$?
if [ $ret -ne 0 ]; then
    echo " - FAILED"
    exit
else
    echo " - PASSED"
fi

echo "RUNNING TEST #11: Performance measurement of multiclass classifier"
$PYTHON3_PATH "./run_scripts/run_CLASSIFIER_measure_performance.py" --output_writer "file" --conf_file "./unit_and_integration_test/configs/test_json_measure_performance_multiclass_classifier.json"
ret=$?
if [ $ret -ne 0 ]; then
    echo " - FAILED"
    exit
else
    echo " - PASSED"
fi

echo "RUNNING TEST #11: Classify images by multiclass classifier"
$PYTHON3_PATH "./run_scripts/run_CLASSIFIER_classify_images.py" --output_writer "file" --conf_file "./unit_and_integration_test/configs/test_json_classify_images_multiclass_classifier.json"
ret=$?
if [ $ret -ne 0 ]; then
    echo " - FAILED"
    exit
else
    echo " - PASSED"
fi

echo "RUNNING TEST #12: Sort images based on classification"
$PYTHON3_PATH "./run_scripts/run_CLASSIFIER_sort_images_based_on_classification.py" --output_writer "file" --conf_file "./unit_and_integration_test/configs/test_json_sort_images_based_on_classification.json"
ret=$?
if [ $ret -ne 0 ]; then
    echo " - FAILED"
    exit
else
    echo " - PASSED"
fi

echo "RUNNING TEST #13: Delete binary classifier"
$PYTHON3_PATH "./run_scripts/run_CLASSIFIER_delete_classifier.py" --output_writer "file" --conf_file "./unit_and_integration_test/configs/test_json_delete_binary_classifier.json"
ret=$?
if [ $ret -ne 0 ]; then
    echo " - FAILED"
    exit
else
    echo " - PASSED"
fi

echo "RUNNING TEST #14: Delete multiclass classifier"
$PYTHON3_PATH "./run_scripts/run_CLASSIFIER_delete_classifier.py" --output_writer "file" --conf_file "./unit_and_integration_test/configs/test_json_delete_multiclass_classifier.json"
ret=$?
if [ $ret -ne 0 ]; then
    echo " - FAILED"
    exit
else
    echo " - PASSED"
fi

echo "RUNNING TEST #14: Delete multiclass classifier"
$PYTHON3_PATH "./run_scripts/run_CLASSIFIER_delete_classifier.py" --output_writer "file" --conf_file "./unit_and_integration_test/configs/test_json_delete_multiclass_classifier.json"
ret=$?
if [ $ret -ne 0 ]; then
    echo " - FAILED"
    exit
else
    echo " - PASSED"
fi

echo "RUNNING TEST #15: Generate negative tile images for a tile classifier"
$PYTHON3_PATH "./run_scripts/run_IMAGE_generate_negative_samples_for_tiling.py" --output_writer "file" --conf_file "./unit_and_integration_test/configs/test_json_generate_negative_tiles.json"
ret=$?
if [ $ret -ne 0 ]; then
    echo " - FAILED"
    exit
else
    echo " - PASSED"
fi

echo "RUNNING TEST #16: Create classifiers for advaced scoring techniques"
$PYTHON3_PATH "./run_scripts/run_CLASSIFIER_train_classifier.py" --output_writer "file" --conf_file "./unit_and_integration_test/configs/test_json_train_background_detection_classifier.json"
ret=$?
if [ $ret -ne 0 ]; then
    echo " - FAILED"
    exit
fi
$PYTHON3_PATH "./run_scripts/run_CLASSIFIER_train_classifier.py" --output_writer "file" --conf_file "./unit_and_integration_test/configs/test_json_train_square_detection_classifier.json"
ret=$?
if [ $ret -ne 0 ]; then
    echo " - FAILED"
    exit
else
    echo " - PASSED"
fi

echo "RUNNING TEST #17: Tiling testing images"
$PYTHON3_PATH "./run_scripts/run_IMAGE_process_images.py" --output_writer "file" --conf_file "./unit_and_integration_test/configs/test_json_process_images_tiling.json"
ret=$?
if [ $ret -ne 0 ]; then
    echo " - FAILED"
    exit
else
    echo " - PASSED"
fi

echo "RUNNING TEST #18: Classify tiled images"
$PYTHON3_PATH "./run_scripts/run_CLASSIFIER_classify_tiled_images.py" --output_writer "file" --conf_file "./unit_and_integration_test/configs/test_json_classify_tiled_image.json"
ret=$?
if [ $ret -ne 0 ]; then
    echo " - FAILED"
    exit
else
    echo " - PASSED"
fi


echo "RUNNING TEST #19: Cropping testing images"
$PYTHON3_PATH "./run_scripts/run_IMAGE_process_images.py" --output_writer "file" --conf_file "./unit_and_integration_test/configs/test_json_process_images_cropping.json"
ret=$?
if [ $ret -ne 0 ]; then
    echo " - FAILED"
    exit
else
    echo " - PASSED"
fi


echo "RUNNING TEST #20: Classify cropped images"
$PYTHON3_PATH "./run_scripts/run_CLASSIFIER_classify_cropped_images.py" --output_writer "file" --conf_file "./unit_and_integration_test/configs/test_json_classify_cropped_image.json"
ret=$?
if [ $ret -ne 0 ]; then
    echo " - FAILED"
    exit
else
    echo " - PASSED"
fi

echo "RUNNING TEST #21: Recursive classifier"
$PYTHON3_PATH "./run_scripts/run_CLASSIFIER_recursive_classifier.py" --output_writer "file" --conf_file "./unit_and_integration_test/configs/test_json_recursive_classifier.json"
ret=$?
if [ $ret -ne 0 ]; then
    echo " - FAILED"
    exit
else
    echo " - PASSED"
fi

echo "RUNNING TEST #22: Delete classifiers"
$PYTHON3_PATH "./run_scripts/run_CLASSIFIER_delete_classifier.py" --output_writer "file" --conf_file "./unit_and_integration_test/configs/test_json_delete_binary_classifier.json"
ret=$?
if [ $ret -ne 0 ]; then
    echo " - FAILED"
    exit
fi
$PYTHON3_PATH "./run_scripts/run_CLASSIFIER_delete_classifier.py" --output_writer "file" --conf_file "./unit_and_integration_test/configs/test_json_delete_binary_classifier.json"
ret=$?
if [ $ret -ne 0 ]; then
    echo " - FAILED"
    exit
else
    echo " - PASSED"
fi

echo "ALL TESTS COMPLETED."

rm -rf ./unit_and_integration_test/temp
rm ./log.txt
