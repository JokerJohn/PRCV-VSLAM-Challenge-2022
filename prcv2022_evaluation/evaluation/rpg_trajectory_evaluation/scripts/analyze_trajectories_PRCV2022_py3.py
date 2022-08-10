#!/usr/bin/env python2

from matplotlib import pylab, colors
import os
import argparse
from ruamel.yaml import YAML
import shutil
import json
from datetime import datetime

if os.environ.get('DISPLAY', '') == '':
    print('no display found. Using non-interactive Agg backend')
    import matplotlib
    matplotlib.use('Agg')  # set the backend before importing pyplot

    import matplotlib.pyplot as plt
    from matplotlib import rc
    from matplotlib import pylab, colors

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rc
from colorama import init, Fore

import add_path
from trajectory import Trajectory
import plot_utils as pu
import results_writer as res_writer
from analyze_trajectory_single import analyze_multiple_trials, analyze_multiple_trials_specify_gt_est_path
from fn_constants import kNsToEstFnMapping, kNsToMatchFnMapping, kFnExt
from rule_score_PRCV2022 import N_segment, rule_score
from collections import OrderedDict

init(autoreset=True)
rc('font', **{'family': 'serif', 'serif': ['Times'], 'size': 6})
rc('text', usetex=True)
FORMAT = '.pdf'


params = {'axes.titlesize': 8, 'legend.fontsize': 6, 'legend.numpoints': 1}
pylab.rcParams.update(params)


def spec(N):
    t = np.linspace(-510, 510, N)
    return np.round(np.clip(np.stack([-t, 510 - np.abs(t), t], axis=1), 0,
                            255)).astype("float32") / 255


PALLETE = spec(20)

# colormap: https://matplotlib.org/3.1.1/tutorials/colors/colormaps.html
PALLETE[0] = [0, 1.0 * 152 / 255, 1.0 * 83 / 255]  # green
PALLETE[1] = [1.0 * 228 / 255, 1.0 * 53 / 255, 1.0 * 39 / 255]  # red
PALLETE[2] = [1.0 * 140 / 255, 1.0 * 3 / 255, 1.0 * 120 / 255]  # purple
PALLETE[3] = [0, 1.0 * 95 / 255, 1.0 * 129 / 255]  # blue
PALLETE[4] = [0.9290, 0.6940, 0.1250]
PALLETE[5] = [0.6350, 0.0780, 0.1840]
PALLETE[6] = [0.494, 0.184, 0.556]
PALLETE[7] = [0.850, 0.3250, 0.0980]

# plot according to dataset


def plot_trajectories(dataset_trajectories_list,
                      dataset_names,
                      algorithm_names,
                      datasets_out_dir,
                      table_score,
                      plot_settings,
                      plot_idx=0,
                      plot_side=True,
                      plot_aligned=True,
                      plot_traj_per_alg=True):
    columns = []
    for k in table_score['Total']:
        v = k
        columns.append(v)
    rows = []
    for k in table_score:
        v = k
        if (k != 'Total'):
            v = plot_settings['datasets_titles'][k]
        rows.append(v)
    for alg in algorithm_names:
        fig, ax = plt.subplots(len(dataset_names) + 1, 1,
                               figsize=(4.0, 4.0 * len(dataset_names)))
        if (len(dataset_names)) == 0:
            continue

        cell_text = []
        for k in table_score:
            cell_text.append(['{0:.0f}'.format(v)
                             for v in table_score[k].values()])
        cell_text = np.array(cell_text)
        ax[0].axis('off')
        ax[0].axis('tight')
        ax[0].table(cellText=cell_text, rowLabels=rows,
                    colLabels=columns, loc='center')

        output_dir = datasets_out_dir
        for dataset_idx, dataset_nm in enumerate(dataset_names):
            dataset_trajs = dataset_trajectories_list[dataset_idx]
            p_es_0 = {}
            p_gt_0 = {}
            p_gt_sparse_0 = {}
            for traj_list in dataset_trajs:
                p_es_0[traj_list[plot_idx].alg] = traj_list[plot_idx].p_es_aligned
                p_gt_0[traj_list[plot_idx].alg] = traj_list[plot_idx].p_gt
                p_gt_sparse_0[traj_list[plot_idx].alg] = traj_list[plot_idx].p_gt_raw_sparse
            print("Collected trajectories to plot: {0}".format(
                algorithm_names))
            assert sorted(algorithm_names) == sorted(list(p_es_0.keys()))
            print("Plotting {0}...".format(dataset_nm))

            ax[dataset_idx +
                1].set_title(plot_settings['datasets_titles'][dataset_nm])
            ax[dataset_idx + 1].set_xlabel('X [m]')
            ax[dataset_idx + 1].set_ylabel('Y [m]')
            ax[dataset_idx + 1].set_aspect('equal')
            ax[dataset_idx + 1].plot(p_gt_sparse_0[alg][:, 0],
                                     p_gt_sparse_0[alg][:, 1],
                                     'o',
                                     markersize=3,
                                     color=PALLETE[0],
                                     alpha=1.0,
                                     label='Reference Points')
            pu.plot_trajectory_top(
                ax[dataset_idx + 1], p_gt_sparse_0[alg], PALLETE[1], 'Reference', 1.0, linewidth=0.5)
            pu.plot_trajectory_top(ax[dataset_idx + 1], p_es_0[alg], PALLETE[3],
                                   plot_settings['algo_labels'][alg], 1.0, linewidth=0.5)
            plt.sca(ax[dataset_idx + 1])
            plt.legend(bbox_to_anchor=(1.02, 1), loc=2, borderaxespad=0.)

        print('output folder: ' + output_dir + '/' +
              'estimated_trajectory_top' + FORMAT)
        fig.tight_layout()
        # print(output_dir + '/' + 'estimated_trajectory_top' + FORMAT)
        fig.savefig(output_dir + '/' + 'estimated_trajectory_top' + FORMAT,
                    bbox_inches="tight",
                    dpi=args.dpi)
        plt.close(fig)


def parse_config_file(config_fn, sort_names):
    yaml = YAML()
    with open(config_fn) as f:
        d = yaml.load(f)

    # Dataset info
    datasets = list(d['Datasets'].keys())
    if sort_names:
        datasets = sorted(datasets)
    datasets_platforms = {}
    datasets_labels = {}
    datasets_titles = {}
    for v in datasets:
        datasets_platforms[v] = d['Datasets'][v]['platform']
        datasets_labels[v] = d['Datasets'][v]['label']
        if 'title' in d['Datasets'][v]:
            datasets_titles[v] = d['Datasets'][v]['title']

    # Algorithm info
    algorithms = list(d['Algorithms'].keys())
    if sort_names:
        algorithms = sorted(algorithms)
    alg_labels = {}
    alg_fn = {}
    for v in algorithms:
        alg_labels[v] = d['Algorithms'][v]['label']
        alg_fn[v] = d['Algorithms'][v]['fn']

    # Other info
    boxplot_distances = []
    if 'RelDistances' in d:
        boxplot_distances = d['RelDistances']
    boxplot_percentages = []
    if 'RelDistancePercentages' in d:
        boxplot_percentages = d['RelDistancePercentages']

    if boxplot_distances and boxplot_percentages:
        print(
            Fore.RED +
            "Found both both distances and percentages for boxplot distances")
        print(Fore.RED + "Will use the distances instead of percentages.")
        boxplot_percentages = []

    #
    return datasets, datasets_platforms, datasets_labels, datasets_titles, \
        algorithms, alg_labels, alg_fn, \
        boxplot_distances, boxplot_percentages


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='''Analyze trajectories''')

    default_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '../results')
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               '../analyze_trajectories_config')
    parser.add_argument('config',
                        type=str,
                        help='yaml file specifying algorithms and datasets')
    parser.add_argument('--groundtruth_dir',
                        help='GT folder with the results',
                        default=default_path)
    parser.add_argument('--output_dir',
                        help="Folder to output plots and data",
                        default=default_path)
    parser.add_argument('--results_dir',
                        help='base folder with the results to analyze',
                        default=default_path)
    parser.add_argument('--computer',
                        help='HW computer: [laptop, nuc, odroid, up]',
                        default='laptop')
    parser.add_argument('--mul_trials',
                        type=int,
                        help='number of trials, None for single run',
                        default=None)
    parser.add_argument('--no_sort_names',
                        action='store_false',
                        dest='sort_names',
                        help='whether to sort dataset and algorithm names')

    # odometry error
    parser.add_argument(
        '--odometry_error_per_dataset',
        help="Analyze odometry error for individual dataset. "
        "The same subtrajectory length will be used for the same dataset "
        "and different algorithms",
        action='store_true')
    parser.add_argument(
        '--overall_odometry_error',
        help="Collect the odometry error from all datasets and calculate statistics.",
        dest='overall_odometry_error',
        action='store_true')

    # RMSE (ATE)
    parser.add_argument('--rmse_table',
                        help='Output rms erros into latex tables',
                        action='store_true')
    parser.add_argument('--rmse_table_median_only',
                        action='store_true',
                        dest='rmse_median_only')
    parser.add_argument('--rmse_boxplot',
                        help='Plot the trajectories',
                        action='store_true')
    parser.add_argument('--rmse_table_alg_col',
                        help='Algorithm name format the column',
                        action='store_true')

    parser.add_argument('--write_time_statistics',
                        help='write time statistics',
                        action='store_true')

    # plot trajectories
    parser.add_argument('--plot_trajectories',
                        help='Plot the trajectories',
                        action='store_true')
    parser.add_argument('--no_plot_side',
                        action='store_false',
                        dest='plot_side')
    parser.add_argument('--no_plot_aligned',
                        action='store_false',
                        dest='plot_aligned')
    parser.add_argument('--no_plot_traj_per_alg',
                        action='store_false',
                        dest='plot_traj_per_alg')
    parser.add_argument('--recalculate_errors',
                        help='Deletes cached errors',
                        action='store_true')
    parser.add_argument('--png',
                        help='Save plots as png instead of pdf',
                        action='store_true')
    parser.add_argument('--dpi', type=int, default=300)
    parser.set_defaults(odometry_error_per_dataset=False,
                        overall_odometry_error=False,
                        rmse_table=False,
                        plot_trajectories=False,
                        rmse_boxplot=False,
                        rmse_table_alg_col=False,
                        recalculate_errors=False,
                        png=False,
                        time_statistics=False,
                        sort_names=True,
                        plot_side=True,
                        plot_aligned=True,
                        plot_traj_per_alg=True,
                        rmse_median_only=False,
                        plot_display=False)
    # try:
    args = parser.parse_args()
    print("Arguments:\n{}".format('\n'.join(
        ['- {}: {}'.format(k, v) for k, v in args.__dict__.items()])))

    print("Will analyze results from {0} and output will be "
          "in {1}".format(args.results_dir, args.output_dir))
    output_dir = args.output_dir

    config_fn = os.path.join(config_path, args.config)
    print("Parsing evaluation configuration {0}...".format(config_fn))

    datasets, datasets_platforms, datasets_labels, datasets_titles, \
        algorithms, algo_labels, algo_fn, \
        rel_e_distances, rel_e_perc = \
        parse_config_file(config_fn, args.sort_names)

    # create the result path
    report_result_path = os.path.join(output_dir, 'report')
    print('Create result path: {}'.format(report_result_path))
    os.system('mkdir -p {}'.format(report_result_path))
    shutil.copy2(config_fn, report_result_path)

    # check the existence of estimated and GT
    remove_key = []
    for d in datasets:
        for config_i in algorithms:  # config_i = 'estimated'
            trace_dir = os.path.join(args.results_dir, 'traj')
            est_traj_path = os.path.join(
                trace_dir, '{}.{}'.format(d, kFnExt))
            print('Est_Traj_path: {}'.format(est_traj_path))

            gt_dir = os.path.join(args.groundtruth_dir, 'traj')
            gt_traj_path = os.path.join(gt_dir, '{}.{}'.format(d, kFnExt))
            print('GT_Traj_path: {}'.format(gt_traj_path))

            if not os.path.exists(est_traj_path):
                print('Not exist est_traj: {}'.format(est_traj_path))
                remove_key.append(d)
                break

        if not os.path.exists(gt_traj_path):
            print('Not exist gt_traj: {}'.format(gt_traj_path))
            remove_key.append(d)
            break

    print('remove keys: {}'.format(remove_key))
    for v in remove_key:
        datasets.remove(v)
        del datasets_platforms[v]
        del datasets_labels[v]
        del datasets_titles[v]

    same_subtraj = True if rel_e_distances else False
    assert len(PALLETE) > len(algorithms),\
        "Not enough colors for all configurations"
    algo_colors = {}
    for i in range(len(algorithms)):
        algo_colors[algorithms[i]] = PALLETE[i + 1]

    print(Fore.YELLOW + "=== Evaluation Configuration Summary ===")
    print(Fore.YELLOW + "Datasests to evaluate: ")
    for d in datasets:
        print(Fore.YELLOW + '- {0}: {1}'.format(d, datasets_labels[d]))
    print(Fore.YELLOW + "Algorithms to evaluate: ")
    for a in algorithms:
        print(Fore.YELLOW + '- {0}: {1}, {2}, {3}'.format(
            a, algo_labels[a], algo_fn[a], algo_colors[a]))
    plot_settings = {
        'datasets_platforms': datasets_platforms,
        'datasets_titles': datasets_titles,
        'datasets_labels': datasets_labels,
        'algo_labels': algo_labels,
        'algo_colors': algo_colors
    }

    if args.png:
        FORMAT = '.png'

    eval_uid = '_'.join(list(plot_settings['algo_labels'].values())) +\
        datetime.now().strftime("%Y%m%d%H%M")

    need_odometry_error = args.odometry_error_per_dataset or args.overall_odometry_error
    if need_odometry_error:
        print(Fore.YELLOW + "Will calculate odometry errors")

    print("#####################################")
    print(">>> Loading and calculating errors....")
    print("#####################################")
    # organize by configuration
    config_trajectories_list = []
    config_multierror_list = []
    dataset_boxdist_map = {}
    for d in datasets:
        dataset_boxdist_map[d] = rel_e_distances

    n_trials = 1
    ape_sparse = OrderedDict()
    for config_i in algorithms:
        cur_trajectories_i = []
        cur_mulierror_i = []
        for d in datasets:
            print(Fore.RED +
                  "--- Processing {0}-{1}... ---".format(config_i, d))

            trace_dir = os.path.join(args.results_dir, 'traj')
            print('Trace_dir: {}'.format(trace_dir))
            assert os.path.exists(
                trace_dir), "{0} not found.".format(trace_dir)

            est_traj_path = os.path.join(trace_dir, '{}'.format(d))
            print('Est_Traj_path: {}'.format(est_traj_path))

            gt_dir = os.path.join(args.groundtruth_dir, 'traj')
            print('GT_dir: {}'.format(gt_dir))
            assert os.path.exists(gt_dir), "{0} not found.".format(gt_dir)

            gt_traj_path = os.path.join(gt_dir, '{}'.format(d))
            print('GT_Traj_path: {}'.format(gt_traj_path))

            traj_list, mt_error = analyze_multiple_trials_specify_gt_est_path(
                est_dir=trace_dir,
                est_traj_path=est_traj_path,
                gt_dir=gt_dir,
                gt_traj_path=gt_traj_path,
                dataset_name=d,
                est_type=algo_fn[config_i],
                n_trials=n_trials,
                recalculate_errors=args.recalculate_errors,
                preset_boxplot_distances=dataset_boxdist_map[d],
                preset_boxplot_percentages=rel_e_perc,
                compute_odometry_error=need_odometry_error)

            # computer sparse APE
            for traj in traj_list:
                select_idx = np.floor(np.linspace(
                    start=0, stop=traj.t_gt_raw.shape[0]-1, num=N_segment+1)).astype(int)
                select_idx = select_idx[1:]
                select_idx = list(select_idx)

                traj.t_gt_raw_sparse = traj.t_gt_raw[select_idx]
                # tx, ty, tz, tw
                traj.p_gt_raw_sparse = traj.p_gt_raw[select_idx][:]
                # qx, qy, qz, qw
                traj.q_gt_raw_sparse = traj.q_gt_raw[select_idx][:]

                traj.t_es_sparse = []
                traj.p_es_aligned_sparse = []
                traj.q_es_aligned_sparse = []
                for timestamp_ref in traj.t_gt_raw_sparse:
                    idx = (np.abs(traj.t_gt - timestamp_ref)).argmin()
                    traj.t_es_sparse.append(traj.t_es[idx])
                    traj.p_es_aligned_sparse.append(
                        traj.p_es_aligned[idx][:])
                    traj.q_es_aligned_sparse.append(
                        traj.q_es_aligned[idx][:])
                traj.t_es_sparse = np.array(traj.t_es_sparse)
                traj.p_es_aligned_sparse = np.array(
                    traj.p_es_aligned_sparse)
                traj.q_es_aligned_sparse = np.array(
                    traj.q_es_aligned_sparse)

                e_trans_vec = (traj.p_gt_raw_sparse -
                               traj.p_es_aligned_sparse)
                e_trans = np.sqrt(np.sum(e_trans_vec**2, 1))
                ape_sparse[d] = e_trans

                if not dataset_boxdist_map[d] and traj_list:
                    print(
                        "Assign the boxplot distances for {0}...".format(d))
                    dataset_boxdist_map[d] = traj_list[0].preset_boxplot_distances
                for traj in traj_list:
                    traj.alg = config_i
                    traj.dataset_short_name = d
                # TODO: not save trajectory evaluation results
                # mt_error.saveErrors()
                # mt_error.cache_current_error()
                mt_error.uid = '_'.join(
                    [args.computer, config_i, d,
                        str(n_trials)])
                mt_error.alg = config_i
                mt_error.dataset = d
                cur_trajectories_i.append(traj_list)
                cur_mulierror_i.append(mt_error)
        config_trajectories_list.append(cur_trajectories_i)
        config_multierror_list.append(cur_mulierror_i)

        # organize by dataset name
        dataset_trajectories_list = []
        dataset_multierror_list = []
        for ds_idx, dataset_nm in enumerate(datasets):
            dataset_trajs = [v[ds_idx] for v in config_trajectories_list]
            dataset_trajectories_list.append(dataset_trajs)
            dataset_multierrors = [v[ds_idx]
                                   for v in config_multierror_list]
            dataset_multierror_list.append(dataset_multierrors)

        # output PRCV2022 score
        print('ape_sparse: {}'.format(ape_sparse))
        print('rule_score: {}'.format(rule_score))

        dataset_score = []
        table_score = OrderedDict()
        for d in ape_sparse:
            table_score[d] = OrderedDict()
            for k in rule_score:
                table_score[d][str(k * 100) + 'cm'] = 0
            table_score[d]['Others'] = 0
            table_score[d]['Score'] = 0

            score = 0
            for i in range(ape_sparse[d].shape[0]):
                flag = True
                for k in rule_score:
                    if ape_sparse[d][i] <= k:
                        score += rule_score[k]
                        table_score[d][str(k * 100) + 'cm'] += 1
                        flag = False
                        break
                if flag:
                    table_score[d]['Others'] += 1
                table_score[d]['Score'] = score
            print('{}: {} (upto {})'.format(d, score, N_segment))
            dataset_score.append(score)

        table_score['Total'] = OrderedDict()
        for d in table_score:
            if (d == 'Total'):
                continue
            for k, v in table_score[d].items():
                if k in table_score['Total'].keys():
                    table_score['Total'][k] += v
                else:
                    table_score['Total'][k] = v
        print(table_score)

        total_score = np.sum(np.array(dataset_score))
        print('total score: {} (upto {})'.format(
            total_score, N_segment * len(datasets)))

        # if args.plot_trajectories:
        print(Fore.MAGENTA +
              '--- Plotting trajectory top and side view ... ---')
        plot_trajectories(dataset_trajectories_list,
                          datasets,
                          algorithms,
                          report_result_path,
                          table_score,
                          plot_settings,
                          plot_side=False,
                          plot_aligned=args.plot_aligned,
                          plot_traj_per_alg=args.plot_traj_per_alg)

        print("#####################################")
        print("<<< Finished.")
        print("#####################################")
    # except:
    #     print('Format Error')
    #     total_score = -1
