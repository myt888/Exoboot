import csv
import scipy.io
import numpy as np
import matplotlib.pyplot as plt


def adjusted_data(time, angle, initial_average_range, threshold):
    initial_value = np.mean(angle[:initial_average_range])
    start_index = next((i for i, angle in enumerate(angle) if abs(angle - initial_value) > threshold), None)

    adjusted_time = [t - time[start_index] for t in time[start_index:]]
    adjusted_angle = angle[start_index:]
    return adjusted_time, adjusted_angle


def load_csv(file_path):
    with open(file_path, mode='r') as file:
        reader = csv.reader(file)

        #iterations = []
        ankle_angle = []
        time = []

        for row in reader:
            if float(row[2]) != 0:
                #iterations.append(int(row[0]))
                time.append(float(row[1]))
                ankle_angle.append(float(row[2]))

        # Adjusting time and angle
        adjusted_time, raw_angles = adjusted_data(time, ankle_angle, 1000, 0.1)
        initial_angle = raw_angles[0]
        adjusted_angles = [-(angle - initial_angle) for angle in raw_angles]
        # Trim the constant data points at the end
        end_value = np.mean(adjusted_angles[-1000:])
        end_index = next((len(adjusted_angles) - i for i, angle in enumerate(reversed(adjusted_angles), 1) if abs(angle - end_value) > 0.5), None) # Threshold is larger

        return adjusted_time[:end_index], adjusted_angles[:end_index]
    

def load_mat(file_path): 
    mat_data = scipy.io.loadmat(file_path)

    JIM_time = mat_data['output'][:,0]
    JIM_angle = np.degrees(mat_data['output'][:,1])
    JIM_torque = mat_data['output'][:,2]

    # Adjusting time
    adjusted_time, adjusted_angle = adjusted_data(JIM_time, JIM_angle, 100, 0.05)

    return adjusted_time, adjusted_angle, JIM_time, JIM_angle, JIM_torque


def plot_angle_data(encoder_time = None, encoder_angle = None, JIM_time = None, JIM_angle = None):
    plt.figure(figsize=(8, 6))
    plt.scatter(encoder_time, encoder_angle, label='Encoder Angle', color='blue', s=3)

    if JIM_time is not None and JIM_angle is not None:
        plt.scatter(JIM_time, JIM_angle, label='JIM Angle', color='red', s=3)

    plt.xlabel('Time')
    plt.ylabel('Ankle Angle')
    plt.grid(True)
    plt.legend()
    plt.show()


def plot_torque_data(JIM_angle, JIM_torque):
    plt.figure(figsize=(8, 6))
    plt.scatter(JIM_angle, JIM_torque, label='Encoder Angle', color='blue', s=3)

    plt.xlabel('Angle')
    plt.ylabel('Torque')
    plt.grid(True)
    plt.legend()
    plt.show()


#Load Files
file_path_encoder = r"I:\My Drive\Neurobionics\ExoBoot\data\encoder_check_test_1.csv"
file_path_JIM = r"I:\My Drive\Neurobionics\ExoBoot\cam_torque_angle\CAL_long_slowsinewithpad001.mat"

encoder_time_adj, encoder_angle_adj = load_csv(file_path_encoder)
JIM_time_adj, JIM_angle_adj, JIM_time, JIM_angle, JIM_torque = load_mat(file_path_JIM)

# plot_angle_data(encoder_time, encoder_angle)
plot_torque_data(JIM_angle, JIM_torque)