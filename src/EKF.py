#!/usr/bin/env python3

# EKF for the Gerard SLAM project
# Jasper Grant and Michael MacGillivray
# 2024-04-05

from math import pi, sin, cos, atan2, sqrt
import LinearAlgebraPurePython as la
from time import sleep, time

pred_covariance = [[0.1, 0.0, 0.0], [0.0, 0.1, 0.0], [0.0, 0.0, 0.1]]


def set_pred_covariance(new_covariance):
    global pred_covariance
    pred_covariance = new_covariance


def get_pred_covariance():
    return pred_covariance


# called from motor_control.py
# Updateing covariavce between scans, stae is updated in the motor control code.
def propagate_state_covariance(
    velocity, time, heading, state_covariance=[[0, 0, 0], [0, 0, 0], [0, 0, 0]]
):
    # Need velosity setpoint, time, and previous state
    # Q is the process noise covariance matrix
    Q = [[0.01, 0.0, 0.0], [0.0, 0.01, 0.0], [0.0, 0.0, 0.0001]]

    # Calculate the Jacobian of the state transition matrix
    G = [
        [1, 0, -velocity * sin(heading) * time],
        [0, 1, velocity * cos(heading) * time],
        [0, 0, 1],
    ]

    # Calculate the predicted state covariance
    pred_covariance = la.matrix_addition(
        la.matrix_multiply(
            la.matrix_multiply(G, state_covariance),
            la.transpose(G),
        ),
        Q,
    )

    set_pred_covariance(pred_covariance)


def update_state(new_landmark, pred_covariance, prev_landmark, state):
    # Need landmark measurements and previous state
    # R is the measurement noise covariance matrix
    R = [[5, 0.0], [0.0, 5]]

    # Calculate the Jacobian of the measurement model
    H = [[1, 0, 0], [0, 1, 0]]

    # Calculate the Kalman gain
    K = la.matrix_multiply(
        la.matrix_multiply(pred_covariance, la.transpose(H)),
        la.invert_matrix(
            la.matrix_addition(
                la.matrix_multiply(
                    la.matrix_multiply(H, pred_covariance),
                    la.transpose(H),
                ),
                R,
            ),
            1,
        ),
    )

    print("Kalman Gain: ", K)

    # Calculate the innovation
    z = [
        [-(new_landmark[0] - prev_landmark[0])],
        [-(new_landmark[1] - prev_landmark[1])],
    ]

    print("Innovation: ", z)

    # Update the state
    state_update = la.matrix_addition([state], la.transpose(la.matrix_multiply(K, z)))

    # Update the state covariance
    negated_K = la.matrix_multiply(K, [[-1, 0], [0, -1]])

    state_covariance = la.matrix_multiply(
        la.matrix_addition(
            [[1, 0, 0], [0, 1, 0], [0, 0, 1]], la.matrix_multiply(negated_K, H)
        ),
        pred_covariance,
    )

    set_pred_covariance(state_covariance)
    # print("State: ", state_update[0][0], state_update[0][1], state_update[0][2])
    # print(
    #     "change in state: ",
    #     state_update[0][0] - state[0],
    #     state_update[0][1] - state[1],
    #     state_update[0][2] - state[2],
    # )
    return [state_update[0][0], state_update[0][1], state_update[0][2]]
