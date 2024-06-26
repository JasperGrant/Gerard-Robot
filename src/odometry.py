#!/usr/bin/env python3

# Odometry functions for the Gerard SLAM project
# Written by Jasper Grant and Michael MacGillivray
# 2024-04-13


from math import pi, sin, cos, atan2, sqrt
import EV3_math_modules as ev3_math
from time import sleep, time
import threading

# Motor inputs
from ev3dev2.motor import (
    LargeMotor,
    OUTPUT_A,
    OUTPUT_D,
)

from EKF import propagate_state_covariance, set_pred_covariance, get_pred_covariance

# Set up robot as tank along with sensors
left_motor = LargeMotor(OUTPUT_D)
right_motor = LargeMotor(OUTPUT_A)

# Assuming we are on a line to start
# EV3 Parameters
BASE_WIDTH = 13  # cm
TIRE_DIAMETER = 5.8  # cm

# Pose
pose_past = [40, 0, pi / 2]


def get_pose_past():
    return pose_past


pose_mutex = threading.Lock()


def set_pose_past(new_pose):
    with pose_mutex:
        global pose_past
        pose_file = open("pose.csv", "a")
        pose_file.write(
            str(new_pose[0]) + "," + str(new_pose[1]) + "," + str(new_pose[2]) + "\n"
        )
        pose_file.close()
        pose_past = new_pose


def get_wheel_velocity(left_motor, right_motor, TIME):
    start_time = time()
    prev_left_encoder = left_motor.position
    prev_right_encoder = right_motor.position
    sleep(TIME)
    curr_left_encoder = left_motor.position
    curr_right_encoder = right_motor.position
    end_time = time()

    left_encoder_diff = curr_left_encoder - prev_left_encoder
    right_encoder_diff = curr_right_encoder - prev_right_encoder

    wheel_radius = TIRE_DIAMETER / 2

    left_distance = (left_encoder_diff / 360) * 2 * pi * wheel_radius
    right_distance = (right_encoder_diff / 360) * 2 * pi * wheel_radius

    delta_t = end_time - start_time

    left_velocity = left_distance / delta_t
    right_velocity = right_distance / delta_t

    # Calc linear and angular velocity
    velo = (left_velocity + right_velocity) / 2
    x_dot = cos(pose_past[2]) * velo
    y_dot = sin(pose_past[2]) * velo
    omega = (right_velocity - left_velocity) / BASE_WIDTH

    theta_current = pose_past[2] + omega * delta_t
    x_current = pose_past[0] + x_dot * delta_t
    y_current = pose_past[1] + y_dot * delta_t
    set_pose_past([x_current, y_current, ev3_math.circle_minus(theta_current)])

    if velo != 0:
        propagate_state_covariance(velo, delta_t, theta_current, get_pred_covariance())


def update_pose():
    while True:
        get_wheel_velocity(left_motor, right_motor, 0.5)


encoder_thread = threading.Thread(target=update_pose)
encoder_thread.start()
