#!/bin/bash
set -e
export TF_CPP_MIN_LOG_LEVEL=2

example_name="ecc_hinge"

# The training arguments
# 1. Usually we set the epochs:2, batch_size:2, max_train_steps_per_epoch:10
# 2. The expression for the following setup is "--epochs 2 --batch_size 8 --max_train_steps_per_epoch 10"
# 3. The syntax of this expression is different from run_notebook.py
train_info="--epochs 2 --batch_size 8 --max_train_steps_per_epoch 10 --max_eval_steps_per_epoch 10"

# Do you want to run "fastestimator test"? (bool)
need_test=1
# ==============================================================================================

full_path=$(realpath $0)
dir_path=$(dirname $full_path)

source_dir="${dir_path/'test/apphub_scripts'/'apphub'}"
stderr_file="${dir_path}/run_tf_stderr.txt"
py_file="${source_dir}/${example_name}_tf.py"

fastestimator train $py_file $train_info $@ 2> $stderr_file

if [ $need_test -eq 1 ]; then
    fastestimator test $py_file $train_info $@ 2>> $stderr_file
    echo 'run test'
fi
