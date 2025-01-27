clear
traj_data = readtable("ankle_test_right_swing_112run1.csv",'VariableNamingRule','modify');
traj_data.AnkleAngle = - rad2deg(traj_data.AnkleAngle);   % Reverse for JIM

%% Trim off first 8s
trim_data = traj_data(find(traj_data.Time > 8, 1):end, :);
trim_data.Time = trim_data.Time - trim_data.Time(1);

%% Resample
freq = 250;
period = 1/freq;
new_times = linspace(trim_data.Time(1), trim_data.Time(end), round((trim_data.Time(end)/period)+1));
new_angles = interp1(trim_data.Time, trim_data.AnkleAngle, new_times);
new_torque = interp1(trim_data.Time, trim_data.CommandedTorque, new_times);

%% Filter
fc = 6;
order = 4;
[b, a] = butter(order, fc / (freq / 2), 'low');
filtered_angles = filtfilt(b, a, new_angles);
filtered_torques = filtfilt(b, a, new_torque);

%% Re-Trim
zero_indices = find(abs(filtered_angles) <= 0.1);
start_index = zero_indices(2);
end_index_range = zero_indices(zero_indices > start_index & zero_indices <= start_index + 5000);
end_index = end_index_range(end);

reset_times = new_times(start_index:end_index) - new_times(start_index);
reset_angles = filtered_angles(start_index:end_index);
reset_torques = filtered_torques(start_index:end_index);
reset_angles(1) = 0;
reset_angles(end) = 0;
max(reset_torques)
%% Slow down
% reset_times_50 = linspace(reset_times(1), reset_times(end)*2, round((reset_times(end)*2/period)+1));
% reset_angles_50 = interp1(reset_times*2, reset_angles, reset_times_50);
% reset_torques_50 = interp1(reset_times*2, reset_torques, reset_times_50);
% 
% reset_times_25 = linspace(reset_times(1), reset_times(end)*4, round((reset_times(end)*4/period)+1));
% reset_angles_25 = interp1(reset_times*4, reset_angles, reset_times_25);
% reset_torques_25 = interp1(reset_times*4, reset_torques, reset_times_25);

%% Speed & Acc
speed = diff(reset_angles)/(period);
speed(end+1)=0;
speed2 = diff(reset_angles)/(2*period);
speed2(end+1)=0;

acc = diff(reset_angles,2)/(period^2);
acc(end+1)=0;
acc(end+1)=0;

%% Plotting
% figure
% plot(reset_times,reset_angles,'LineWidth',1)
% hold on
% plot(reset_times_50, reset_torques_50, 'LineWidth', 1)
% hold on
% plot(reset_times_25,reset_angles,'LineWidth',1)
% hold off
% xlabel("time [s]")
% ylabel("angle [deg]")

% figure
% plot(reset_times,reset_torques,'LineWidth',1)
% xlabel("time [s]")
% ylabel("torque [Nm]")

%% Write Data
output_data = table(reset_times', reset_angles', reset_torques', 'VariableNames', {'time', 'ankle_angle', 'commanded_torque'});
output_path = "traj_data_Katharine.csv";
writetable(output_data, output_path);

% output_data_50 = table(reset_times_50', reset_angles', reset_torques', 'VariableNames', {'time', 'ankle_angle', 'commanded_torque'});
% output_path_50 = "traj_data_Katharine_50.csv";
% writetable(output_data_50, output_path_50);
% 
% output_data_25 = table(reset_times_25', reset_angles', reset_torques', 'VariableNames', {'time', 'ankle_angle', 'commanded_torque'});
% output_path_25 = "traj_data_Katharine_25.csv";
% writetable(output_data_25, output_path_25);