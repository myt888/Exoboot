from SoftRealtimeLoop import SoftRealtimeLoop   # Exit upon cntl+C (runs as infinite loop otherwise)
import numpy as np   # Numerical pythonimport math
import pickle  # Document read/save (record foot sensor file)
import os  # For document read/save (combined with pickle)
import gc   # Memory leak clearance
from collections import deque
import processor as proc
import pandas as pd
import sys
import csv
import time
sys.path.append(r"/home/pi/MBLUE/ThermalCharacterization/logic_board_temp_cal/")
from EB51Man import EB51Man  # Dephy Exoboot Manager
from ActPackMan import _ActPackManStates 
from StatProfiler import SSProfile
from thermal_model import ThermalMotorModel


MAX_TORQUE = 30
NM_PER_AMP = 0.146
ANGLE_OFFSET = 0.28

ANKLE_LOG_VARS = ['time', 'desire_torque', 'passive_torque', 'commanded_torque', 'ankle_angle', 'angular_speed','device_current']

class Controller():
    def __init__(self, dev, dt):
        self.dt = dt
        self.dev = dev

        self.cf_name = 'PEA_test_R_{0}.csv'.format(time.strftime("%Y%m%d-%H%M%S"))
        self.cf_path = os.path.join('/home/pi/ExoBoot/data/traj_neg_torque', self.cf_name)
        self.cf = open(self.cf_path, 'w', encoding='UTF8', newline='')
        self.writer = csv.writer(self.cf)

        self.num_samples = 50
        self.prev_angles = deque(maxlen=self.num_samples)
        self.speed_threshold = 5

        self.traj_data = pd.read_csv(f'/home/pi/ExoBoot/JIM_setup/traj_data_Katharine.csv')


    def __enter__(self):
        self.dev.update()
        return self


    def __exit__(self, exc_type, exc_value, tb):
        self.cf.close()
        print("exiting")


    def calibrate_angle(self, samples = 1000):
        self.dev.realign_calibration()
        self.dev.set_current_gains() 

        input("Press Enter to start angle calibration...")
        angles = []
        delay = self.dt

        for i in range(samples):
                current_angle = self.dev.get_output_angle_degrees() - 90 - ANGLE_OFFSET
                angles.append(current_angle)
                time.sleep(delay)
                i += 1
                if i % 50 == 0:
                    print("Current Angle = ", current_angle)
      
        calibration_angle = sum(angles[-100:]) / len(angles[-100:])
        print(f"calibration complete. start angle: {calibration_angle:.3f} deg")
        return calibration_angle
    

    def update_output_torque(self, des_torque, passive_torque):
        potential_torque = des_torque - passive_torque
        
        command_torque = potential_torque if potential_torque < -0.5 else -0.5  # Threshold
        command_torque = max(command_torque, -MAX_TORQUE)
        # command_torque = max(potential_torque, -MAX_TORQUE)

        return command_torque
    

    def control(self):
        self.writer.writerow(ANKLE_LOG_VARS)

        calibration_angle = self.calibrate_angle()
        for _ in range(self.num_samples):
            self.prev_angles.append(calibration_angle)

        i = 0
        line = 0
        t0 = time.time()
        synced = False

        loop = SoftRealtimeLoop(dt = self.dt, report=True, fade=0.01)
        time.sleep(0.5)

        for t in loop: 
            t_curr = time.time() - t0 
            
            i = i + 1
            self.dev.update()   # Update

            current_angle = self.dev.get_output_angle_degrees() - 90 - ANGLE_OFFSET  # Initial angle set at 90
            self.prev_angles.append(current_angle)

            angle_diffs = np.diff(np.array(self.prev_angles))
            if len(angle_diffs) > 0:
                inst_velocities = angle_diffs / self.dt
                angular_speed = np.mean(inst_velocities)
            else:
                angular_speed = 0

            # Check if the JIM starts moving
            if not synced:
                des_torque = 0
                line = 0
                if abs(current_angle - calibration_angle) > 1:
                    synced = True
                    print("Synced with JIM device. Start commanding torque.")
            else:
                if line <= len(self.traj_data) - 1:
                    des_torque = self.traj_data['commanded_torque'][line]
                    # All-negative torque trajectory
                    # if des_torque>0:
                    #     des_torque = 0
                else:
                    des_torque = 0  # Set to 0 after finish the trajectory
            
            # passive_torque = proc.get_passive_torque(current_angle, angular_speed, self.speed_threshold)  # Get Passive Torque
            passive_torque = 0  # No PEA
            command_torque = self.update_output_torque(des_torque, passive_torque)
            self.dev.set_output_torque_newton_meters(command_torque)

            qaxis_curr = self.dev.get_current_qaxis_amps()
            
            if i % 50 == 0:
                print("des_torque = ", des_torque, "commanded_torque = ", command_torque, ", passive_torque = ", passive_torque, ", ankle angle = ", current_angle)
            self.writer.writerow([t_curr, des_torque, passive_torque, command_torque, current_angle, angular_speed, qaxis_curr])
            line += 1
        print("Controller closed")


if __name__ == '__main__':
    dt = 1/250
    with EB51Man(devttyACMport = '/dev/ttyACM0', whichAnkle = 'right', updateFreq=1000, csv_file_name = "ankle_log.csv", dt = dt) as dev:
        with Controller(dev, dt = dt) as controller:
            controller.control()