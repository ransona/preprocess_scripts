import sys
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import (QApplication, QWidget, QComboBox, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QPushButton, QLabel, QLineEdit, QSizePolicy, QScrollArea, QTableWidget, 
                             QVBoxLayout, QTableWidgetItem, QCheckBox)
import tkinter as tk
from tkinter import messagebox
from PyQt5.QtCore import Qt

import cv2
import organise_paths
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pickle
import os
from pandas import read_csv
import warnings
import csv

# os.environ['DISPLAY'] = 'localhost:10.0'

class MyWindow(QWidget):
    def __init__(self):
        super(MyWindow, self).__init__()
        self.data = {}
        self.meta = {}
        self.meta['total_cells'] = np.nan
        self.meta['current_cell'] = np.nan
        self.meta['current_cond'] = np.nan # currently selected stimulus conditions
        self.meta['window_start'] = 0
        self.meta['window_end'] = 3
        self.meta['max_sort_idx'] = np.nan
        self.meta['p_sort_idx'] = np.nan
        self.meta['stim_win'] = 0
        self.meta['stim_labels'] = []

        self.selection = {}
        self.selection['session'] = 0
        self.selection['roi'] = 0
        self.selection['plane'] = 0
        self.init_ui()

    #     self.setLayout(outer_layout)
    def init_ui(self):
        self.fig = Figure(figsize=(10, 10), dpi=100)
        self.canvas = FigureCanvas(self.fig)

        self.user_lbl = QLabel('Username')
        self.user_txt = QComboBox()
        self.exp_lbl = QLabel('ExpID')
        self.exp_txt = QLineEdit('2024-04-24_09_ESMT169')    
        self.ch_lbl = QLabel('Channel')
        self.ch_txt = QLineEdit('0')            
        self.load_button = QPushButton('Load')
        self.stim_combo = QComboBox()
        self.stim_combo.currentIndexChanged.connect(self.stim_combo_selection_changed)
        self.load_button.clicked.connect(self.load_file)
        self.cond_lbl = QLabel('Stimulus conditions to analyse (comma seperated and 1 based, for example 1,2,4,7)')
        self.cond_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.cond_txt = QLineEdit('1')  
        self.cells2anal_lbl = QLabel('Cells to analyse')
        self.cells2anal_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.prev_cell_button = QPushButton('<')
        self.prev_cell_button.clicked.connect(self.prev_cell)
        self.next_cell_button = QPushButton('>')
        self.next_cell_button.clicked.connect(self.next_cell)
        self.current_cell_txt = QLineEdit('0')
        self.current_cell_txt.returnPressed.connect(self.on_return_pressed_cell)
        
        self.calc_max_button = QPushButton('Rank by max response')
        self.calc_max_button.clicked.connect(self.rank_amp)
        # controls time range to calculate max response over
        self.max_t_lbl = QLabel('secs')
        self.max_t1_txt = QLineEdit('0')
        self.max_t2_txt = QLineEdit('1')

        self.best_max_check = QCheckBox('Show best only')
        self.best_max_check.setChecked(False)
        self.best_max_check.stateChanged.connect(self.update_cell_display)
        self.prev_max_button = QPushButton('<')
        self.prev_max_button.clicked.connect(self.prev_rank_amp)
        self.next_max_button = QPushButton('>')
        self.next_max_button.clicked.connect(self.next_rank_amp)
        self.current_max_txt = QLineEdit('NA')
        self.current_max_txt.returnPressed.connect(self.on_return_pressed_cell_max)

        self.calc_p_button = QPushButton('Rank by p response')
        self.calc_p_button.clicked.connect(self.rank_p)
        self.prev_p_button = QPushButton('<')
        self.prev_p_button.clicked.connect(self.prev_rank_p)
        self.next_p_button = QPushButton('>')
        self.next_p_button.clicked.connect(self.next_rank_p)
        self.current_p_txt = QLineEdit('NA')
        self.current_p_txt.returnPressed.connect(self.on_return_pressed_cell_p)

        # btns for heat plots
        self.heat_button = QPushButton('Show heat plots')
        self.heat_button.clicked.connect(self.show_heat)

        self.tsne_button = QPushButton('Calc tSNE')
        self.tsne_button.clicked.connect(self.tSNE_calc)
        self.tsne_show_button = QPushButton('Show tSNE')
        self.tsne_show_button.clicked.connect(self.tSNE_show)

        self.class_button = QPushButton('Calc classifier')
        self.class_button.clicked.connect(self.class_calc)
        self.class_show_button = QPushButton('Show classifier')
        self.class_show_button.clicked.connect(self.class_show)  

        self.stim_show_button = QPushButton('Show stim conditions')      
        self.stim_show_button.clicked.connect(self.stim_show)

        # controls to specify plot columns
        self.plot_cols_lbl = QLabel('Number of columns in plot')
        self.plot_cols_txt = QLineEdit('')

        outer_layout = QHBoxLayout()

        # layout for controls on left
        controls_grp_layout = QGridLayout()

        current_row = 0  # Start row index

        controls_grp_layout.setColumnStretch(0, 1)  # Column 0
        controls_grp_layout.setColumnStretch(1, 1)  # Column 1
        controls_grp_layout.setColumnStretch(2, 1)  # Column 2
        controls_grp_layout.setColumnStretch(3, 1)  # Column 3        

        controls_grp_layout.addWidget(self.user_lbl, current_row, 0, 1, 2)
        controls_grp_layout.addWidget(self.user_txt, current_row, 2, 1, 2)
        current_row += 1

        controls_grp_layout.addWidget(self.exp_lbl, current_row, 0, 1, 2)
        controls_grp_layout.addWidget(self.exp_txt, current_row, 2, 1, 2)
        current_row += 1

        # Create horizontal layout for Channel Label and Text
        ch_layout = QHBoxLayout()
        ch_layout.addWidget(self.ch_lbl)
        ch_layout.addWidget(self.ch_txt)

        controls_grp_layout.addLayout(ch_layout, current_row, 0, 1, 4)
        current_row += 1

        # Add Start and End time controls
        start_end_layout = QHBoxLayout()

        self.start_lbl = QLabel('Start time')
        self.start_txt = QLineEdit('-2')  # Default start time
        self.end_lbl = QLabel('End time')
        self.end_txt = QLineEdit('5')  # Default end time

        start_end_layout.addWidget(self.start_lbl)
        start_end_layout.addWidget(self.start_txt)
        start_end_layout.addWidget(self.end_lbl)
        start_end_layout.addWidget(self.end_txt)

        controls_grp_layout.addLayout(start_end_layout, current_row, 0, 1, 4)
        current_row += 1

        controls_grp_layout.addWidget(self.load_button, current_row, 0, 1, 4)
        current_row += 1

        controls_grp_layout.addWidget(self.cond_lbl, current_row, 0, 1, 4)
        current_row += 1
        controls_grp_layout.addWidget(self.cond_txt, current_row, 0, 1, 4)
        current_row += 1

        # manually move through cells
        controls_grp_layout.addWidget(self.cells2anal_lbl, current_row, 0, 1, 4)
        current_row += 1
        controls_grp_layout.addWidget(self.prev_cell_button, current_row, 0, 1, 2)
        controls_grp_layout.addWidget(self.next_cell_button, current_row, 2, 1, 2)
        current_row += 1
        controls_grp_layout.addWidget(self.current_cell_txt, current_row, 0, 1, 4)
        current_row += 1

        # move through cells ranked by max median response to pref stim
        # Add widgets to the layout
        controls_grp_layout.addWidget(self.calc_max_button, current_row, 0, 1, 1)
        controls_grp_layout.addWidget(self.max_t1_txt, current_row, 1, 1, 1)
        controls_grp_layout.addWidget(self.max_t2_txt, current_row, 2, 1, 1)
        controls_grp_layout.addWidget(self.max_t_lbl, current_row, 3, 1, 1)

        current_row += 1
        controls_grp_layout.addWidget(self.prev_max_button, current_row, 0, 1, 2)
        controls_grp_layout.addWidget(self.next_max_button, current_row, 2, 1, 2)
        current_row += 1
        controls_grp_layout.addWidget(self.current_max_txt, current_row, 0, 1, 4)
        current_row += 1

        # move through cells ranked by p val
        controls_grp_layout.addWidget(self.calc_p_button, current_row, 0, 1, 2)
        controls_grp_layout.addWidget(self.best_max_check, current_row, 2, 1, 2)
        current_row += 1
        controls_grp_layout.addWidget(self.prev_p_button, current_row, 0, 1, 2)
        controls_grp_layout.addWidget(self.next_p_button, current_row, 2, 1, 2)
        current_row += 1
        controls_grp_layout.addWidget(self.current_p_txt, current_row, 0, 1, 4)
        current_row += 1

        # heat plot buttons
        controls_grp_layout.addWidget(self.heat_button, current_row, 0, 1, 4)      
        current_row += 1

        # make and display t-sne
        controls_grp_layout.addWidget(self.tsne_button, current_row, 0, 1, 2)
        controls_grp_layout.addWidget(self.tsne_show_button, current_row, 2, 1, 2)
        current_row += 1

        # make and display classifier
        controls_grp_layout.addWidget(self.class_button, current_row, 2, 1, 2)
        controls_grp_layout.addWidget(self.class_show_button, current_row, 2, 1, 2)
        current_row += 1

        # show stim button
        controls_grp_layout.addWidget(self.stim_show_button, current_row, 0, 1, 4)
        current_row += 1

        # combo box to load stimulus info
        controls_grp_layout.addWidget(self.stim_combo, current_row, 0, 1, 4)
        current_row += 1

        # controls for plot columns
        controls_grp_layout.addWidget(self.plot_cols_lbl, current_row, 0, 1, 2)
        controls_grp_layout.addWidget(self.plot_cols_txt, current_row, 2, 1, 2)

        # layout for displaying responses
        response_display_layout = QVBoxLayout()
        response_display_layout.addWidget(self.canvas)

        # add nested layouts to the outer layout
        outer_layout.addLayout(controls_grp_layout, 20)
        outer_layout.addLayout(response_display_layout, 80)

        self.setLayout(outer_layout)
        # populate stim label combo box
        # Directory path
        dir_path = '/data/common/configs/explore_gui'
        # Get list of file names in the directory
        filenames = os.listdir(dir_path) 
        self.stim_combo.addItem('No labels')
        # Populate QComboBox
        for name in filenames:
            # Remove file extension
            name_without_ext = os.path.splitext(name)[0]
            self.stim_combo.addItem(name_without_ext)

        # populate stim label combo box
        # Directory path
        dir_path = '/home'
        # populate box of usernames
        filenames = os.listdir(dir_path) 
        # Populate QComboBox
        for name in filenames:
            # Remove file extension
            name_without_ext = os.path.splitext(name)[0]
            self.user_txt.addItem(name_without_ext)

    def update_cell_display(self):
        # display currently selected conditions of currently selected cell
        # parse text in current conditions box to convert to a list of numbers
        self.meta['current_cond'] = list(map(int,self.cond_txt.text().split(',')))
        self.meta['current_cond_idx'] = [item - 1 for item in self.meta['current_cond']]
        start_time = float(self.start_txt.text())
        end_time = float(self.end_txt.text())        

        # ensure the requested stimulus conditions are valid
        if max(self.meta['current_cond'])>self.meta['stim_type_count']:
            show_message_box(f"Cancelled display update because at least one of the requested stimulus numbers ({max(self.meta['current_cond'])}) exceeds the number of stimulus conditions ({self.meta['stim_type_count']})")
            return
        
        if self.plot_cols_txt.text():
            # text box isn't empty
            plot_cols = int(self.plot_cols_txt.text())
            plot_rows = int(np.ceil(len(self.meta['current_cond'])/plot_cols))
        else:
            plot_cols = np.ceil(np.sqrt(len(self.meta['current_cond']))).astype(int)
            plot_rows = np.floor(np.sqrt(len(self.meta['current_cond']))).astype(int)
            if plot_cols * plot_rows < len(self.meta['current_cond']):
                plot_rows = plot_rows + 1

        self.fig.clf()
        
        # if you've chosen to just see the best one
        if self.best_max_check.isChecked(): # and
            ax = self.fig.subplots(1, 1, sharex=True, sharey=True)
            self.meta['ax'] = ax 
            stim_id = self.meta['max_sort_cond'][self.meta['current_cell']]
            trial_indices = self.data['all_trials'].loc[(self.data['all_trials']['stim'] == stim_id)].index
            if not trial_indices.empty:
                # if there are trials
                ax.plot(self.data['s2p_dF_cut']['t'],np.transpose(self.data['s2p_dF_cut']['dF'][self.meta['current_cell'],trial_indices,:]),color='lightgray')
                # plot the mean response
                mean_response = np.mean(np.transpose(self.data['s2p_dF_cut']['dF'][self.meta['current_cell'],trial_indices,:]),axis=1)
                ax.plot(self.data['s2p_dF_cut']['t'],mean_response,color='black')
                if len(self.meta['stim_labels'])>=stim_id:
                    # label the plot if label is available
                    ax.set_title(self.meta['stim_labels'][stim_id-1])

            # set time range
            ax.set_xlim([start_time,end_time])

        else:
            ax = np.ravel(self.fig.subplots(plot_rows, plot_cols, sharex=True, sharey=True))
            self.meta['ax'] = ax        
            # cycle through conditions displaying traces of each
            for i, stim_id in enumerate(self.meta['current_cond']):
                trial_indices = self.data['all_trials'].loc[(self.data['all_trials']['stim'] == stim_id)].index
                if not trial_indices.empty:
                    # if there are trials
                    ax[i].plot(self.data['s2p_dF_cut']['t'],np.transpose(self.data['s2p_dF_cut']['dF'][self.meta['current_cell'],trial_indices,:]),color='lightgray')
                    # plot the mean response
                    mean_response = np.mean(np.transpose(self.data['s2p_dF_cut']['dF'][self.meta['current_cell'],trial_indices,:]),axis=1)
                    ax[i].plot(self.data['s2p_dF_cut']['t'],mean_response,color='black')
                    if len(self.meta['stim_labels'])>=stim_id:
                        # label the plot if label is available
                        ax[i].set_title(self.meta['stim_labels'][stim_id-1])
                
                ax[i].set_xlim([start_time,end_time])
            # clear any extra axes not used
            for iAx in range(i+1,(plot_cols*plot_rows)):
                ax[iAx].set_visible(False)

        self.canvas.draw()
        # update current cell text box
        self.current_cell_txt.setText(str(self.meta['current_cell']))
        # update current cell ranked by amplitude text box
        if not np.any(np.isnan(self.meta['max_sort_idx'])):
            current_rank = np.where(self.meta['max_sort_idx']==self.meta['current_cell'])[0][0]
            self.current_max_txt.setText(str(current_rank))
        # update current cell ranked by p text box
        if not np.any(np.isnan(self.meta['p_sort_idx'])):
            current_rank = np.where(self.meta['p_sort_idx']==self.meta['current_cell'])[0][0]
            self.current_p_txt.setText(str(current_rank))

    def load_file(self):
        print('Loading data...')
        # Implement the functionality to load a file
        userID = self.user_txt.currentText()
        expID = self.exp_txt.text()
        ch = self.ch_txt.text()
        animalID, remote_repository_root, processed_root, exp_dir_processed, exp_dir_raw = organise_paths.find_paths(userID, expID)
        # load all exp data
        exp_dir_processed_recordings = os.path.join(exp_dir_processed,'recordings')
        exp_dir_processed_cut = os.path.join(exp_dir_processed,'cut')
        try:
            with open(os.path.join(exp_dir_processed_cut,'s2p_ch'+ch+'_dF_cut.pickle'), "rb") as file: self.data['s2p_dF_cut'] = pickle.load(file)
            self.data['all_trials'] = read_csv(os.path.join(exp_dir_processed, expID + '_all_trials.csv'))
            self.meta['stim_type_count'] = self.data['all_trials']['stim'].unique().shape[0]
            # organise some meta data
            self.meta['total_cells'] = self.data['s2p_dF_cut']['dF'].shape[0]
            self.meta['current_cell'] = 0
            self.meta['current_cell_amp'] = 0 
            self.meta['max_sort_idx'] = np.nan   
            print('Done')
            self.rank_amp()
            self.update_cell_display()
        except Exception as e:
            show_message_box(f"An error occurred: {e}")

    def prev_cell(self):
        # Implement the functionality to move to the previous cell
        self.meta['current_cell'] = self.meta['current_cell'] - 1
        if self.meta['current_cell'] <= 0:
            self.meta['current_cell'] = 0
        self.update_cell_display()

    def next_cell(self):
        # Implement the functionality to move to the next cell
        self.meta['current_cell'] = self.meta['current_cell'] + 1
        if self.meta['current_cell'] > self.meta['total_cells']-1:
            self.meta['current_cell'] = self.meta['total_cells']-1
        self.update_cell_display()

    def calc_time_averaged(self):
        # calculates the time averaged response on each trial for each cell
        print('Calculating time averaged responses...')
        # Calculate start and end sample to average over in time
        self.meta['window_start'] = float(self.max_t1_txt.text())
        self.meta['window_end'] = float(self.max_t2_txt.text())
        start_sample = np.argmax(self.data['s2p_dF_cut']['t']>= self.meta['window_start'])
        end_sample = np.argmax(self.data['s2p_dF_cut']['t']>= self.meta['window_end'])
        # calculate keeping trials seperate
        time_av_resp = np.mean(self.data['s2p_dF_cut']['dF'][:,:,start_sample:end_sample],axis=2)
        # average over trials of same trialID
        all_stim_ids = np.unique(self.data['all_trials']['stim'])
        trial_av_resp = np.zeros([self.meta['total_cells'],len(all_stim_ids)])
        for iStimID in all_stim_ids:
            trial_indices = self.data['all_trials'].loc[(self.data['all_trials']['stim'] == iStimID)].index
            trial_av_resp[:,iStimID-1] = np.mean(time_av_resp[:,trial_indices],axis=1)
        self.meta['time_av_resp'] = time_av_resp
        self.meta['trial_av_resp'] = trial_av_resp
        print('Done')

    def calc_time_averaged_heat(self):
        # calculates the time averaged response on each trial for each cell
        print('Calculating trial averaged response heatplots...')
        # average over trials of same trialID
        all_stim_ids = np.unique(self.data['all_trials']['stim'])
        trial_av_resp_heat = np.zeros([self.meta['total_cells'],len(self.data['s2p_dF_cut']['t']),len(all_stim_ids)])
        for iStimID in all_stim_ids:
            trial_indices = self.data['all_trials'].loc[(self.data['all_trials']['stim'] == iStimID)].index
            stim_heat = self.data['s2p_dF_cut']['dF'][:,trial_indices,:]
            trial_av_resp_heat[:,:,iStimID-1] = np.mean(stim_heat,axis=1)

        self.meta['trial_av_resp_heat'] = trial_av_resp_heat
        print('Done')

    def rank_amp(self):
        # Implement the functionality to rank by max response
        print("Ranking by max response")
        self.calc_time_averaged()
        # Calculate mean responses for each cell x trial
        # Calculate max response over conditions for each cell
        self.meta['current_cond'] = list(map(int,self.cond_txt.text().split(',')))
        # this is to deal with the stim numbers being one based and the indexes of the processed
        # data being 0 based (for example matrices of heatplots)        
        self.meta['current_cond_idx'] = [item - 1 for item in self.meta['current_cond']]
        self.meta['current_cond'] = list(map(int,self.cond_txt.text().split(',')))
        self.meta['current_cond_idx'] = [item - 1 for item in self.meta['current_cond']]

        # ensure the requested stimulus conditions are valid
        if max(self.meta['current_cond'])>self.meta['stim_type_count']:
            show_message_box(f"At least one of the requested stimulus numbers {self.meta['current_cond']} exceeds the number of stimulus conditions {self.meta['stim_type_count']}")
            return
        
        # find max response in each selected stimulus condition
        max_resp = np.max(self.meta['trial_av_resp'][:,self.meta['current_cond_idx']],axis=1)
        # Rank cells using the selected conditions
        self.meta['max_sort_idx'] = np.argsort(max_resp)[::-1] 
        # Find stimulus condition (out of filtered subset) which gives the max response
        self.meta['max_sort_cond'] = np.argmax(self.meta['trial_av_resp'][:,self.meta['current_cond_idx']],axis=1)
        self.meta['max_sort_cond'] = np.array(self.meta['current_cond_idx'])[self.meta['max_sort_cond']]+1
    
    def prev_rank_amp(self):
        # Implement the functionality to move to the previous rank by amplitude
        print("Previous rank by amplitude")
        # find the current cell in the ranking and if possible move to the lower ranked one
        current_rank = np.where(self.meta['max_sort_idx']==self.meta['current_cell'])[0][0]
        new_rank = current_rank - 1
        if new_rank <= 0:
            new_rank = 0
        self.meta['current_cell'] = self.meta['max_sort_idx'][new_rank]    
        self.update_cell_display()

    def next_rank_amp(self):
        # Implement the functionality to move to the next rank by amplitude
        print("Next rank by amplitude")
        # find the current cell in the ranking and if possible move to the next ranked one
        current_rank = np.where(self.meta['max_sort_idx']==self.meta['current_cell'])[0][0]
        new_rank = current_rank + 1
        if new_rank > self.meta['total_cells']-1:
            new_rank = self.meta['total_cells']-1
        self.meta['current_cell'] = self.meta['max_sort_idx'][new_rank]    
        self.update_cell_display()

    def rank_p(self):
        # Implement the functionality to rank by p response
        print("Ranking by p response")

    def prev_rank_p(self):
        # Implement the functionality to move to the previous rank by p-value
        print("Previous rank by p-value")

    def next_rank_p(self):
        # Implement the functionality to move to the next rank by p-value
        print("Next rank by p-value")

    def tSNE_calc(self):
        # Implement the functionality to calculate t-SNE
        print("Calculating t-SNE")

    def tSNE_show(self):
        # Implement the functionality to show t-SNE
        print("Showing t-SNE")

    def class_calc(self):
        # Implement the functionality to calculate classifier
        print("Calculating classifier")

    def class_show(self):
        # Implement the functionality to show classifier
        print("Showing classifier")

    def on_return_pressed_cell(self):
        self.meta['current_cell'] = int(self.current_cell_txt.text())
        if self.meta['current_cell'] <= 0:
            self.meta['current_cell'] = 0
        if self.meta['current_cell'] > self.meta['total_cells']-1:
            self.meta['current_cell'] = self.meta['total_cells']-1
        self.update_cell_display()

    def on_return_pressed_cell_max(self):
        if int(self.current_max_txt.text()) > self.meta['total_cells'] or int(self.current_max_txt.text()) < 0:
            print('Cell requested invalid (too big or small)')
            return
        if not np.any(np.isnan(self.meta['max_sort_idx'])):
            self.meta['current_cell'] = self.meta['max_sort_idx'][int(self.current_max_txt.text())]
            self.update_cell_display()
        else:
            print('Cells not yet sorted by amplitude')

    def on_return_pressed_cell_p(self):
        if int(self.current_p_txt.text()) > self.meta['total_cells'] or int(self.current_p_txt.text()) < 0:
            print('Cell requested invalid (too big or small)')
            return
        if not np.any(np.isnan(self.meta['p_sort_idx'])):
            self.meta['current_cell'] = self.meta['p_sort_idx'][int(self.current_p_txt.text())]
            self.update_cell_display()
        else:
            print('Cells not yet sorted by p value')

    def show_heat(self):
        # display currently selected conditions as heat plot
        self.calc_time_averaged_heat()
        # shows average response of each cell to each condition
        self.meta['current_cond'] = list(map(int,self.cond_txt.text().split(',')))
        # this is to deal with the stim numbers being one based and the indexes of the processed
        # data being 0 based (for example matrices of heatplots)        
        self.meta['current_cond_idx'] = [item - 1 for item in self.meta['current_cond']]

        if self.plot_cols_txt.text():
            # text box isn't empty
            plot_cols = int(self.plot_cols_txt.text())
            plot_rows = int(np.ceil(len(self.meta['current_cond'])/plot_cols))
        else:
            plot_cols = np.ceil(np.sqrt(len(self.meta['current_cond']))).astype(int)
            plot_rows = np.floor(np.sqrt(len(self.meta['current_cond']))).astype(int)
            if plot_cols * plot_rows < len(self.meta['current_cond']):
                plot_rows = plot_rows + 1

        self.fig.clf()
        self.canvas.draw()
        ax_2d = self.fig.subplots(plot_rows, plot_cols)
        ax = np.ravel(ax_2d) #, sharex=True, sharey=True))
        self.meta['ax'] = ax        
        # cycle through conditions displaying traces of each
        for i, stim_id in enumerate(self.meta['current_cond']):
            trial_indices = self.data['all_trials'].loc[(self.data['all_trials']['stim'] == stim_id)].index
            if not trial_indices.empty:
                # if there are trials
                # calculate how to display the time axis by searching from the right hand side of the heatplot for
                # the first non nan value
                with warnings.catch_warnings():
                    warnings.filterwarnings('ignore', category=RuntimeWarning)
                    collapsed_vert = np.nanmean(self.meta['trial_av_resp_heat'][:,:,stim_id-1],axis=0)
 
                indices = np.flatnonzero(~np.isnan(collapsed_vert))
                index = indices[-1]
                # convert to start and end time
                start_time = self.data['s2p_dF_cut']['t'][0]
                end_time = self.data['s2p_dF_cut']['t'][index]
                ax[i].imshow(self.meta['trial_av_resp_heat'][:,0:index,stim_id-1],
                             extent=[start_time,end_time,0,self.meta['total_cells']],
                             aspect='auto', vmin=0, vmax=1,cmap='gray')
                # Ensure y-axis ticks are integers
                ax[i].yaxis.set_major_locator(ticker.MaxNLocator(integer=True))                
                if len(self.meta['stim_labels'])>=stim_id:
                    # label the plot if label is available
                    ax[i].set_title(self.meta['stim_labels'][stim_id-1])
                # determine if plot is a left hand side one
                row = i // plot_rows
                col = i % plot_cols
                if not row == plot_rows - 1:
                #     ax[i].set_xticks([])
                    x = 0 
                else:
                    ax[i].set_xlabel('Time(s)')
                    
                if not col == 0:
                #     ax[i].set_yticks([])  
                    x = 0              
                else:
                    ax[i].set_ylabel('ROI #')
        
        # clear any extra axes not used
        for iAx in range(i+1,(plot_cols*plot_rows)):
            ax[iAx].set_visible(False)
        self.canvas.draw()

    def stim_show(self):
        # Assuming df is your DataFrame
        df = self.data['all_trials'].copy()
        df.drop(columns='time', inplace=True)

        # Remove duplicates
        df.drop_duplicates(inplace=True)

        # Sort by 'stim' column
        df.sort_values(by='stim', inplace=True)

        win = QWidget()
        scroll = QScrollArea()
        layout = QVBoxLayout()
        table = QTableWidget()
        scroll.setWidget(table)
        layout.addWidget(table)
        win.setLayout(layout)

        table.setColumnCount(len(df.columns))
        table.setRowCount(len(df.index))

        # Set the table headers
        table.setHorizontalHeaderLabels(df.columns)

        for i in range(len(df.index)):
            for j in range(len(df.columns)):
                table.setItem(i, j, QTableWidgetItem(str(df.iloc[i, j])))

        # Get the screen resolution of your monitor
        screen = QApplication.primaryScreen()
        screen_resolution = screen.availableGeometry()

        # Set the window size to 70% of the screen size
        win.resize(int(screen_resolution.width() * 0.7), int(screen_resolution.height() * 0.7))

        # Center the window on the screen
        frame_geometry = win.frameGeometry()
        center_point = screen_resolution.center()
        frame_geometry.moveCenter(center_point)
        win.move(frame_geometry.topLeft())

        win.show()
        self.meta['stim_win'] = win
    
    def stim_combo_selection_changed(self,i):
        if i > 0:
            selected_label = self.stim_combo.itemText(i)
            # load the label csv file
            # Path to the CSV file
            file_path = os.path.join('/data/common/configs/explore_gui',selected_label+'.csv')
            # List to store the CSV data
            self.meta['stim_labels'] = []
            # Open the file in read mode
            with open(file_path, 'r') as file:
                # Create a CSV reader
                reader = csv.reader(file)
                for row in reader:
                    # Append each value in the row to the data list
                    #for value in row:
                    self.meta['stim_labels'].append(row[0])            
            # remove description of stim type
            self.meta['stim_labels'].pop(0)
        else:
            # no labels
            self.meta['stim_labels'] = []
      
def show_message_box(msg):
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    messagebox.showinfo("Information", msg)
    root.destroy()

def main():
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

