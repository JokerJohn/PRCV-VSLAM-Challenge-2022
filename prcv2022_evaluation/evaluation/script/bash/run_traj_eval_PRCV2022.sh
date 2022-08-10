# add eval_cfg.yaml
export Base_Folder=/home/xchu/Downloads/PRCV-VSLAM-Challenge-2022-main/prcv2022_evaluation
export Evaluation_Script_Path=$Base_Folder/evaluation
export Algorithm_Result_Path=$Base_Folder/benchmark/estimated
export Groundtruth_Path=$Base_Folder/groundtruth
python3 $Evaluation_Script_Path/rpg_trajectory_evaluation/scripts/add_eval_cfg_recursive.py $Algorithm_Result_Path/ se3 -1

# evalaution
python3 $Evaluation_Script_Path/rpg_trajectory_evaluation/scripts/analyze_trajectories_PRCV2022_py3.py \
--groundtruth_dir=$Groundtruth_Path \
--results_dir=$Algorithm_Result_Path \
--output_dir=$Algorithm_Result_Path \
--computer=laptop \
--mul_trials=0 \
--odometry_error_per_dataset \
--overall_odometry_error \
--plot_trajectories \
--no_sort_names \
--recalculate_errors \
PRCV2022.yaml
