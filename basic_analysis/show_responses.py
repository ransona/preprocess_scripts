import sys
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import (QApplication, QWidget, QComboBox, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QPushButton, QLabel, QLineEdit, QSizePolicy, QScrollArea, QTableWidget, 
                             QVBoxLayout, QTableWidgetItem, QCheckBox)
from PyQt5.QtCore import Qt
import cv2
import organise_paths
import matplotlib.pyplot as plt
import numpy as np
import pickle
import os
from pandas import read_csv
import warnings
import csv

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

    def init_ui(self):
        
        self.fig = Figure(figsize=(10, 10), dpi=100)
        self.canvas = FigureCanvas(self.fig)

        self.user_lbl = QLabel('Username')
        self.user_txt = QComboBox()
        self.exp_lbl = QLabel('ExpID')
        self.exp_txt = QLineEdit('2023-04-17_10_ESMT123')      
        self.load_button = QPushButton('Load')
        self.stim_combo = QComboBox()
        self.stim_combo.currentIndexChanged.connect(self.stim_combo_selection_changed)
        self.load_button.clicked.connect(self.load_file)
        self.cond_lbl = QLabel('Stimulus conditions to analyse')
        self.cond_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.cond_txt = QLineEdit('0')  
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
        self.best_max_check = QCheckBox()
        self.best_max_check.setChecked(True)
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
        controls_grp_layout.addWidget(self.user_lbl,0,0,1,2)
        controls_grp_layout.addWidget(self.user_txt,0,2,1,2)
        controls_grp_layout.addWidget(self.exp_lbl,1,0,1,2)
        controls_grp_layout.addWidget(self.exp_txt,1,2,1,2)
        controls_grp_layout.addWidget(self.load_button,3,0,1,4)
        controls_grp_layout.addWidget(self.cond_lbl,4,0,1,4)
        controls_grp_layout.addWidget(self.cond_txt,5,0,1,4)
        # manually move through cells
        controls_grp_layout.addWidget(self.cells2anal_lbl,6,0,1,4)
        controls_grp_layout.addWidget(self.prev_cell_button,7,0,1,2)
        controls_grp_layout.addWidget(self.next_cell_button,7,2,1,2)
        controls_grp_layout.addWidget(self.current_cell_txt,8,0,1,4)
        # move through cells ranked by max median response to pref stim
        controls_grp_layout.addWidget(self.calc_max_button,9,0,1,4)
        controls_grp_layout.addWidget(self.prev_max_button,10,0,1,2)
        controls_grp_layout.addWidget(self.next_max_button,10,2,1,2)
        controls_grp_layout.addWidget(self.current_max_txt,11,0,1,4)
        # move through cells ranked by p val
        controls_grp_layout.addWidget(self.calc_p_button,12,0,1,2)
        controls_grp_layout.addWidget(self.best_max_check,12,2,1,2)
        controls_grp_layout.addWidget(self.prev_p_button,13,0,1,2)
        controls_grp_layout.addWidget(self.next_p_button,13,2,1,2)
        controls_grp_layout.addWidget(self.current_p_txt,14,0,1,4)
        # heat plot buttons
        controls_grp_layout.addWidget(self.heat_button,15,0,1,4)      
        # make and display t-sne
        controls_grp_layout.addWidget(self.tsne_button,16,0,1,2)
        controls_grp_layout.addWidget(self.tsne_show_button,17,0,1,2)
        # make and display classifier
        controls_grp_layout.addWidget(self.class_button,16,2,1,2)
        controls_grp_layout.addWidget(self.class_show_button,17,2,1,2)
        # show stim button
        controls_grp_layout.addWidget(self.stim_show_button,18,0,1,4)
        # combo box to load stimulus info
        controls_grp_layout.addWidget(self.stim_combo,19,0,1,4)
        self.plot_cols_lbl = QLabel('Number of columns in plot')
        self.plot_cols_txt = QLineEdit('')
        controls_grp_layout.addWidget(self.plot_cols_lbl,20,0,1,2)
        controls_grp_layout.addWidget(self.plot_cols_txt,20,2,1,2)        
        
        # layout for displaying responses
        response_display_layout = QVBoxLayout()
        response_display_layout.addWidget(self.canvas)

        # add nested layouts to the outer layout
        outer_layout.addLayout(controls_grp_layout,20)
        outer_layout.addLayout(response_display_layout,80)       

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

        if self.plot_cols_txt.text():
            # text box isn't empty
            plot_cols = int(self.plot_cols_txt.text())
            plot_rows = int(np.ceil(len(self.meta['current_cond'])/plot_cols))
        else:
            plot_cols = np.ceil(np.sqrt(len(self.meta['current_cond']))).astype(int)
            plot_rows = np.ceil(np.sqrt(len(self.meta['current_cond']))).astype(int)

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
        animalID, remote_repository_root, processed_root, exp_dir_processed, exp_dir_raw = organise_paths.find_paths(userID, expID)
        # load all exp data
        exp_dir_processed_recordings = os.path.join(exp_dir_processed,'recordings')
        exp_dir_processed_cut = os.path.join(exp_dir_processed,'cut')
        with open(os.path.join(exp_dir_processed_cut,'s2p_ch0_dF_cut.pickle'), "rb") as file: self.data['s2p_dF_cut'] = pickle.load(file)
        self.data['all_trials'] = read_csv(os.path.join(exp_dir_processed, expID + '_all_trials.csv'))
        # organise some meta data
        self.meta['total_cells'] = self.data['s2p_dF_cut']['dF'].shape[0]
        self.meta['current_cell'] = 0
        self.meta['current_cell_amp'] = 0 
        self.meta['max_sort_idx'] = np.nan   
        print('Done')
        self.rank_amp()
        self.update_cell_display()

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
        max_resp = np.max(self.meta['trial_av_resp'][:,self.meta['current_cond']],axis=1)
        # Rank cells using the selected conditions
        self.meta['max_sort_idx'] = np.argsort(max_resp)[::-1] 
        # Find stimulus condition (out of filtered subset) which gives the max response
        self.meta['max_sort_cond'] = np.argmax(self.meta['trial_av_resp'][:,self.meta['current_cond']],axis=1)
        self.meta['max_sort_cond'] = np.array(self.meta['current_cond'])[self.meta['max_sort_cond']]+1
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
        if self.plot_cols_txt.text():
            # text box isn't empty
            plot_cols = int(self.plot_cols_txt.text())
            plot_rows = int(np.ceil(len(self.meta['current_cond'])/plot_cols))
        else:
            plot_cols = np.ceil(np.sqrt(len(self.meta['current_cond']))).astype(int)
            plot_rows = np.ceil(np.sqrt(len(self.meta['current_cond']))).astype(int)

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
                    collapsed_vert = np.nanmean(self.meta['trial_av_resp_heat'][:,:,stim_id],axis=0)
 
                indices = np.flatnonzero(~np.isnan(collapsed_vert))
                index = indices[-1]
                # convert to start and end time
                start_time = self.data['s2p_dF_cut']['t'][0]
                end_time = self.data['s2p_dF_cut']['t'][index]
                ax[i].imshow(self.meta['trial_av_resp_heat'][:,0:index,stim_id],
                             extent=[start_time,end_time,0,self.meta['total_cells']],
                             aspect='auto', vmin=0, vmax=0.5,cmap='gray')
                if len(self.meta['stim_labels'])>=stim_id:
                    # label the plot if label is available
                    ax[i].set_title(self.meta['stim_labels'][stim_id-1])
                # determine if plot is a left hand side one
                row = i // plot_rows
                col = i % plot_cols
                if not row == plot_rows - 1:
                    ax[i].set_xticks([])
                else:
                    ax[i].set_xlabel('Time(s)')
                    
                if not col == 0:
                    ax[i].set_yticks([])                
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
      

def main():
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

