import sys
import os
import pickle
import shutil
import cv2
import numpy as np

# PyQt5 imports
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import (QMainWindow, QApplication, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QPushButton, QLineEdit, QSlider, QMessageBox)
from PyQt5.QtCore import Qt, QTimer

# Matplotlib integration in PyQt5
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar

# Import your custom module that provides file paths.
import organise_paths

class VideoAnalysisApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.loaded = False
        self.playing = False
        self.timer = QTimer()  # QTimer for playback
        self.timer.timeout.connect(self.playFrame)
        self.vlines = []  # To store vertical line references in the plots
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("Video Analysis GUI")
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        mainLayout = QVBoxLayout(centralWidget)
        
        # --- Top Input Fields ---
        inputLayout = QHBoxLayout()
        self.userIdEdit = QLineEdit()
        self.userIdEdit.setPlaceholderText("Enter User ID")
        self.expIdEdit = QLineEdit()
        self.expIdEdit.setPlaceholderText("Enter Experiment ID")
        self.loadButton = QPushButton("Load Data")
        self.loadButton.clicked.connect(self.loadData)
        inputLayout.addWidget(QLabel("User ID:"))
        inputLayout.addWidget(self.userIdEdit)
        inputLayout.addWidget(QLabel("Experiment ID:"))
        inputLayout.addWidget(self.expIdEdit)
        inputLayout.addWidget(self.loadButton)
        mainLayout.addLayout(inputLayout)
        
        # --- Video Control Buttons and Slider ---
        controlLayout = QHBoxLayout()
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setEnabled(False)
        self.slider.valueChanged.connect(self.updateFrame)
        self.playButton = QPushButton("Play")
        self.playButton.setEnabled(False)
        self.playButton.clicked.connect(self.startPlayback)
        self.stopButton = QPushButton("Stop")
        self.stopButton.setEnabled(False)
        self.stopButton.clicked.connect(self.stopPlayback)
        controlLayout.addWidget(self.slider)
        controlLayout.addWidget(self.playButton)
        controlLayout.addWidget(self.stopButton)
        mainLayout.addLayout(controlLayout)
        
        # --- Video Display Widgets ---
        videoLayout = QHBoxLayout()
        self.leftVideoLabel = QLabel("Left Eye Video")
        self.leftVideoLabel.setFixedSize(320, 240)
        self.rightVideoLabel = QLabel("Right Eye Video")
        self.rightVideoLabel.setFixedSize(320, 240)
        videoLayout.addWidget(self.leftVideoLabel)
        videoLayout.addWidget(self.rightVideoLabel)
        mainLayout.addLayout(videoLayout)
        
        # --- Percentile Control Panel ---
        percentileLayout = QHBoxLayout()
        self.lowerPercentileEdit = QLineEdit("0")
        self.upperPercentileEdit = QLineEdit("99")
        updatePercentileButton = QPushButton("Update Y-Limits")
        updatePercentileButton.clicked.connect(self.plotPupilProperties)
        percentileLayout.addWidget(QLabel("Lower Percentile:"))
        percentileLayout.addWidget(self.lowerPercentileEdit)
        percentileLayout.addWidget(QLabel("Upper Percentile:"))
        percentileLayout.addWidget(self.upperPercentileEdit)
        percentileLayout.addWidget(updatePercentileButton)
        mainLayout.addLayout(percentileLayout)
        
        # --- Matplotlib Canvas for Pupil Property Plots ---
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        mainLayout.addWidget(self.canvas)
        
        # --- Matplotlib Navigation Toolbar (for zooming and panning) ---
        self.toolbar = NavigationToolbar(self.canvas, self)
        mainLayout.addWidget(self.toolbar)
    
    def loadData(self):
        """
        Loads data based on the entered User ID and Experiment ID.
        Sets up file paths, copies videos if necessary, loads pickle data,
        configures the slider, and plots the pupil properties.
        """
        self.userID = self.userIdEdit.text().strip()
        self.expID = self.expIdEdit.text().strip()
        if not self.userID or not self.expID:
            QMessageBox.warning(self, "Input Error", "Please enter both User ID and Experiment ID")
            return
        
        # Get paths using the custom module.
        self.animalID, self.remote_repository_root, self.processed_root, \
            self.exp_dir_processed, self.exp_dir_raw = organise_paths.find_paths(self.userID, self.expID)
        self.exp_dir_processed_recordings = os.path.join(self.exp_dir_processed, 'recordings')
        self.exp_dir_processed_cut = os.path.join(self.exp_dir_processed, 'cut')
        
        # Video file paths.
        self.video_path_left = os.path.join(self.exp_dir_processed, f"{self.expID}_eye1_left.avi")
        self.video_path_right = os.path.join(self.exp_dir_processed, f"{self.expID}_eye1_right.avi")
        
        # Check video existence; attempt to copy from raw if not found.
        if not os.path.isfile(self.video_path_left):
            try:
                print("Copying eye videos if necessary")
                shutil.copyfile(os.path.join(self.exp_dir_raw, f"{self.expID}_eye1_left.avi"), self.video_path_left)
                shutil.copyfile(os.path.join(self.exp_dir_raw, f"{self.expID}_eye1_right.avi"), self.video_path_right)
                print("Copy complete!")
            except Exception as e:
                print("Cropped eye videos not found on server:", e)
                QMessageBox.critical(self, "File Error", "Eye videos not found. Please check the paths.")
                return
        
        # Load pickle data.
        try:
            with open(os.path.join(self.exp_dir_processed_recordings, 'dlcEyeLeft.pickle'), "rb") as file:
                self.left_eyedat = pickle.load(file)
            with open(os.path.join(self.exp_dir_processed_recordings, 'dlcEyeRight.pickle'), "rb") as file:
                self.right_eyedat = pickle.load(file)
        except Exception as e:
            QMessageBox.critical(self, "Data Error", "Error loading pupil data: " + str(e))
            return
        
        # Open left video to get the total number of frames.
        cap = cv2.VideoCapture(self.video_path_left)
        if not cap.isOpened():
            QMessageBox.critical(self, "Video Error", "Could not open left video file.")
            return
        self.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        
        self.slider.setMinimum(0)
        self.slider.setMaximum(self.total_frames - 1)
        self.slider.setEnabled(True)
        self.playButton.setEnabled(True)
        self.stopButton.setEnabled(True)
        self.loaded = True
        
        # Display the first frame and plot the pupil properties.
        self.updateFrame()
        self.plotPupilProperties()
    
    def overlay_plot(self, frame, position, eyeDat):
        """
        Draws the overlay (eye lid polylines and the pupil circle) on the frame.
        """
        if np.isnan(eyeDat['x'][position]) or np.isnan(eyeDat['y'][position]) or np.isnan(eyeDat['radius'][position]):
            return frame
        # Draw eye lid outline in red.
        color = (255, 0, 0)
        thickness = 2
        x = eyeDat['eye_lid_x'][np.newaxis, position, :].T
        y = eyeDat['eye_lid_y'][np.newaxis, position, :].T
        points = np.concatenate([x, y], axis=1)
        points = points.reshape((-1, 1, 2)).astype(int)
        frame = cv2.polylines(frame, [points], isClosed=False, color=color, thickness=thickness)
        
        # Draw pupil circle in blue.
        color = (0, 0, 255)
        center = (int(eyeDat['x'][position]), int(eyeDat['y'][position]))
        radius = int(eyeDat['radius'][position])
        frame = cv2.circle(frame, center, radius, color, thickness)
        return frame

    def playVideoFrame(self, frame_position, video_path, eyedat, side="Left"):
        """
        Opens the video file at video_path, grabs the frame at frame_position,
        applies the overlay, and returns the frame.
        """
        cap = cv2.VideoCapture(video_path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_position)
        ret, frame = cap.read()
        cap.release()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = self.overlay_plot(frame, frame_position, eyedat)
            return frame
        return None

    def updateFrame(self):
        """
        Called when the slider value changes. Updates both the video displays and the vertical line.
        """
        if not self.loaded:
            return
        
        position = self.slider.value()
        # Update left video frame.
        frame_left = self.playVideoFrame(position, self.video_path_left, self.left_eyedat, side="Left")
        if frame_left is not None:
            image_left = QtGui.QImage(frame_left.data, frame_left.shape[1], frame_left.shape[0],
                                      frame_left.strides[0], QtGui.QImage.Format_RGB888)
            pixmap_left = QtGui.QPixmap.fromImage(image_left)
            self.leftVideoLabel.setPixmap(pixmap_left.scaled(self.leftVideoLabel.size(), Qt.KeepAspectRatio))
        
        # Update right video frame.
        frame_right = self.playVideoFrame(position, self.video_path_right, self.right_eyedat, side="Right")
        if frame_right is not None:
            image_right = QtGui.QImage(frame_right.data, frame_right.shape[1], frame_right.shape[0],
                                       frame_right.strides[0], QtGui.QImage.Format_RGB888)
            pixmap_right = QtGui.QPixmap.fromImage(image_right)
            self.rightVideoLabel.setPixmap(pixmap_right.scaled(self.rightVideoLabel.size(), Qt.KeepAspectRatio))
        
        # Update vertical sliding lines on the plots.
        if self.vlines:
            for vline in self.vlines:
                vline.set_xdata(position)
            self.canvas.draw_idle()

    def startPlayback(self):
        if not self.loaded:
            return
        self.playing = True
        self.timer.start(33)  # roughly 30 frames per second

    def stopPlayback(self):
        self.playing = False
        self.timer.stop()

    def playFrame(self):
        if self.slider.value() < self.total_frames - 1:
            self.slider.setValue(self.slider.value() + 1)
        else:
            self.stopPlayback()

    def plotPupilProperties(self):
        """
        Loads the pupil data and creates 4 subplots for:
          1. Left pupil positions (x and y; median subtracted)
          2. Right pupil positions (x and y; median subtracted)
          3. Pupil radius
          4. Pupil velocity
        Modifications include:
          - Y-limits are set based on user-specified percentiles (default 0 and 99).
          - Only the bottom plot displays x-axis tick labels.
          - Y-axis labels are set as 'Left Pos', 'Right Pos', 'Radius', and 'Velocity'.
          - Plot titles are removed.
          - The top and right spines are hidden.
          - A vertical dashed line indicates the current frame on each subplot.
        """
        try:
            with open(os.path.join(self.exp_dir_processed_recordings, 'dlcEyeLeft.pickle'), "rb") as file:
                left_dlc = pickle.load(file)
            with open(os.path.join(self.exp_dir_processed_recordings, 'dlcEyeRight.pickle'), "rb") as file:
                right_dlc = pickle.load(file)
        except Exception as e:
            print("Error loading pupil data for plotting:", e)
            return
        
        # Read the lower and upper percentile values from the user text boxes.
        try:
            lower_pct = float(self.lowerPercentileEdit.text())
            upper_pct = float(self.upperPercentileEdit.text())
        except ValueError:
            lower_pct, upper_pct = 0, 99  # default values if conversion fails
        
        self.figure.clear()
        # sharex=True ensures that only the bottom subplot shows x-axis tick labels.
        axs = self.figure.subplots(4, 1, sharex=True)
        
        # --- Plot 1: Left pupil positions ---
        left_x = left_dlc['x'] - np.nanmedian(left_dlc['x'])
        left_y = left_dlc['y'] - np.nanmedian(left_dlc['y'])
        ax = axs[0]
        ax.plot(left_x, color='skyblue')
        ax.plot(left_y, color='navy')
        combined = np.concatenate([left_x, left_y])
        lower_lim = np.nanpercentile(combined, lower_pct)
        upper_lim = np.nanpercentile(combined, upper_pct)
        ax.set_ylim(lower_lim, upper_lim)
        ax.set_ylabel('Left Pos')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.tick_params(axis='x', labelbottom=False)
        
        # --- Plot 2: Right pupil positions ---
        right_x = right_dlc['x'] - np.nanmedian(right_dlc['x'])
        right_y = right_dlc['y'] - np.nanmedian(right_dlc['y'])
        ax = axs[1]
        ax.plot(right_x, color='lightcoral')
        ax.plot(right_y, color='maroon')
        combined = np.concatenate([right_x, right_y])
        lower_lim = np.nanpercentile(combined, lower_pct)
        upper_lim = np.nanpercentile(combined, upper_pct)
        ax.set_ylim(lower_lim, upper_lim)
        ax.set_ylabel('Right Pos')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.tick_params(axis='x', labelbottom=False)
        
        # --- Plot 3: Pupil radius ---
        ax = axs[2]
        ax.plot(left_dlc['radius'], color='blue')
        ax.plot(right_dlc['radius'], color='red')
        combined = np.concatenate([left_dlc['radius'], right_dlc['radius']])
        lower_lim = np.nanpercentile(combined, lower_pct)
        upper_lim = np.nanpercentile(combined, upper_pct)
        ax.set_ylim(lower_lim, upper_lim)
        ax.set_ylabel('Radius')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.tick_params(axis='x', labelbottom=False)
        
        # --- Plot 4: Pupil velocity ---
        ax = axs[3]
        ax.plot(left_dlc['velocity'], color='blue')
        ax.plot(right_dlc['velocity'], color='red')
        combined = np.concatenate([left_dlc['velocity'], right_dlc['velocity']])
        lower_lim = np.nanpercentile(combined, lower_pct)
        upper_lim = np.nanpercentile(combined, upper_pct)
        ax.set_ylim(lower_lim, upper_lim)
        ax.set_ylabel('Velocity')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # --- Add a vertical dashed line to each subplot ---
        self.vlines = []
        current_frame = self.slider.value() if self.loaded else 0
        for ax in axs:
            vline = ax.axvline(x=current_frame, color='k', linestyle='--')
            self.vlines.append(vline)
        
        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = VideoAnalysisApp()
    win.show()
    sys.exit(app.exec_())
