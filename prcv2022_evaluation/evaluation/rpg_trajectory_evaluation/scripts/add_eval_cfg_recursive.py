#!/usr/bin/env python

import os
import argparse
import yaml
from colorama import init, Fore

init(autoreset=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('root_dir', type=str, help='root folder to iterate')
    parser.add_argument('align_type', type=str, help='alignment type')
    parser.add_argument('align_n', type=int, help='alignment type')
    args = parser.parse_args()
    print("Arguments:\n{}".format('\n'.join(
        ['-{}: {}'.format(k, v) for k, v in args.__dict__.items()])))

    print(Fore.YELLOW +
          "Going to add eval_cfg.yaml under {}.".format(args.root_dir))

    for dirpath, dirnames, filenames in os.walk(args.root_dir):
        for dirname in dirnames:
            if dirname == 'traj':
                eval_cfg_fn = os.path.join(dirpath, dirname, 'eval_cfg.yaml')
                print('- Process {}...'.format(eval_cfg_fn))
                eval_cfg = """\
                  {}: {}
                  {}: {}
                """.format('align_type', args.align_type, 'align_num_frames',
                           args.align_n)
                eval_cfg_str = yaml.safe_load(eval_cfg)
                with open(eval_cfg_fn, 'w') as f:
                    yaml.dump(eval_cfg_str, f)
