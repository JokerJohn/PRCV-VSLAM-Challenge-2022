#!/usr/bin/env python2

# Usage: rosrun ramlab_evaluation pose_to_bag.py \
#   --input=/Titan/dataset/FusionPortable_dataset/handheld/20220216_garden_day/groundtruth_traj.txt \
#   --output=/Titan/dataset/FusionPortable_dataset/handheld/20220216_garden_day/groundtruth_traj.bag \
#   --frame_id=world_gt \
#   --child_frame_id=ouster00

import os
import argparse
import numpy as np
import rospy
import rosbag
from nav_msgs.msg import Odometry, Path
from geometry_msgs.msg import PoseStamped, TransformStamped
from tf2_msgs.msg import TFMessage


def extract(in_filename, out_filename, frame_id, child_frame_id):
    with rosbag.Bag(out_filename, 'w') as outbag:
        with open(in_filename, 'rb') as fin:
            data = np.genfromtxt(fin, delimiter=" ")
            seq = 0

            path = Path()
            path.header.frame_id = frame_id
            for l in data:
                timestamp = l[0]
                tx, ty, tz = l[1:4]
                qx, qy, qz, qw = l[4:8]

                odom = Odometry()
                odom.header.seq = seq
                odom.header.stamp = rospy.Time(timestamp)
                odom.header.frame_id = frame_id
                odom.child_frame_id = child_frame_id
                odom.pose.pose.position.x = tx
                odom.pose.pose.position.y = ty
                odom.pose.pose.position.z = tz
                odom.pose.pose.orientation.x = qx
                odom.pose.pose.orientation.y = qy
                odom.pose.pose.orientation.z = qz
                odom.pose.pose.orientation.w = qw
                outbag.write('/gt_odom', odom, odom.header.stamp)

                pose = PoseStamped()
                pose.header.seq = seq
                pose.header.stamp = rospy.Time(timestamp)
                pose.header.frame_id = frame_id
                pose.pose.position.x = tx
                pose.pose.position.y = ty
                pose.pose.position.z = tz
                pose.pose.orientation.x = qx
                pose.pose.orientation.y = qy
                pose.pose.orientation.z = qz
                pose.pose.orientation.w = qw
                outbag.write('/gt_pose', pose, pose.header.stamp)

                path.header.seq = seq
                path.header.stamp = rospy.Time(timestamp)
                path.poses.append(pose)
                outbag.write('/gt_path', path, path.header.stamp)

                tf_msg = TFMessage()
                tf = TransformStamped()
                tf.header.seq = seq
                tf.header.stamp = rospy.Time(timestamp)
                tf.header.frame_id = frame_id
                tf.child_frame_id = child_frame_id
                tf.transform.translation.x = tx
                tf.transform.translation.y = ty
                tf.transform.translation.z = tz
                tf.transform.rotation.x = qx
                tf.transform.rotation.y = qy
                tf.transform.rotation.z = qz
                tf.transform.rotation.w = qw
                tf_msg.transforms.append(tf)
                outbag.write('/tf', tf_msg, tf.header.stamp)

                seq = seq + 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='''
    Extracts pose from a txt file in TUM format to space separated format.
    Timestamp,
    Translation is ordered as [x y z],
    Quaternion is ordered as [x y z w]
    ''')
    parser.add_argument('--input', help='groundtruth.txt')
    parser.add_argument('--output', default='groundtruth.bag')
    parser.add_argument('--frame_id', default='world_gt')
    parser.add_argument('--child_frame_id', default='body_imu')
    args = parser.parse_args()

    print('Extract pose from file ' + args.input)
    print('Saving to bag ' + args.output)
    print('Frame id: ' + args.frame_id)
    extract(args.input, args.output, args.frame_id, args.child_frame_id)
