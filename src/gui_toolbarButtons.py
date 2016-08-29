#!/usr/bin/env python
# -*- coding: ascii -*-
"""gui_toolbarButtons.py - GUI element: toolbar with Buttons"""

import sys
import Tkinter as Tk
import logging
import settings
import threading
import os
import re
import tkMessageBox

from os import listdir
from os.path import isfile, join
from tkFileDialog   import askdirectory
from defines import *


# Initialize global variables
root = cameraInstance = None


class ToolbarButtons(Tk.Frame):
    """This toolbar allows the user to change settings"""

    def __start(self):
        logging.info("Start button has been pressed")

        # Get Event
        self.eventCameraChosen = self.cameraInstance.getEventCameraChosen()

        # Use and store new FPS value (Because tkInter Text Widgets do not have an onchange() event or similar
        self.curr_settings[IDX_FPS] = int(self.textbox_fps.get("1.0", Tk.END + "-1c"))
        settings.change_parameter(IDX_FPS,int(self.textbox_fps.get("1.0", Tk.END + "-1c")))

        # Disable buttons that change settings
        self.check_button_1.config(state=Tk.DISABLED)
        self.check_button_2.config(state=Tk.DISABLED)
        self.button_start.config(state=Tk.DISABLED)
        self.dropDownListCamera.config(state=Tk.DISABLED)
        self.dropDownListAlgorithm.config(state=Tk.DISABLED)
        self.textbox_fps.config(state=Tk.DISABLED)
        self.button_files.config(state=Tk.DISABLED)
        self.textbox_fps.config(bg='lightgray')

        # Store index of camera in thread

        if self.numberOfCameras > 0:
            logging.info("Camera is started")
            chosenCamera = self.listCamerasStr.get()[-1]
            self.cameraInstance.setCameraIdx(chosenCamera)

        # Update event for camera event
        logging.info("Enabling event: eventCameraChosen ")
        self.eventCameraChosen.set()

    def __quit(self):

        # End program
        logging.info("User pressed ''quit'' button - now halting threads")

        # Close thread running for signal display
        self.signalDisplayInstance.closeSignalPlotterThread()
        logging.info("Signal display thread was closed")

        # If camera connection is active, close it
        self.cameraInstance.closeCameraThread()
        logging.info("Camera capture thread was closed")

        # Close GUI
        self.root.quit()
        logging.info("Tk mainloop() was halted")

        # Debug: Store all still running threads
        logging.debug(threading.enumerate())

        # Exit program
        logging.info("Program will halt now...")
        sys.exit()

    def __init__(self, parent, tk_root, thread, cam, signalDisplay):

        # Store variables
        global root
        self.root = tk_root

        # Add exit function to X button
        self.root.protocol("WM_DELETE_WINDOW", self.__quit)

        # Store camera object
        self.cameraInstance = cam

        # Get number of available cameras
        self.numberOfCameras = self.cameraInstance.getNumberOfCameras()

        # Store thread object
        self.threadInstance = thread

        # Store connection to signal display
        self.signalDisplayInstance = signalDisplay

        # Initialize buttons
        self.check_button_1 = self.check_button_2 = self.check_button_2 = self.check_button_4 = \
            self.listCamerasStr = self.dropDownListCamera = self.listAlgorithmStr = self.dropDownListAlgorithm = None

        # Get current settings
        self.curr_settings = settings.get_parameters()

        # Create GUI
        self.__create_gui()

    def __create_gui(self):

        self.button_frame = Tk.Frame(root, width=500, height=100)
        self.button_frame.pack(side=Tk.BOTTOM)

        # Add button for loading files
        self.button_files = Tk.Button(master=self.button_frame, text='Load files from disk', command=self.__openFiles)
        self.button_files.pack(side=Tk.LEFT)

        # Fill list with available cameras and add to menu
        self.label_x0 = Tk.Label(self.button_frame, text="Camera:")
        self.label_x0.pack(side=Tk.LEFT)
        listCameras = ['']
        # If cameras are available, fill list
        if self.numberOfCameras > 0:
            for cam_idx in range(self.numberOfCameras):
                tmp_string = str(cam_idx)
                listCameras.append(tmp_string)
            listCameras.pop(0)
        # Add list to Button
        self.listCamerasStr = Tk.StringVar()
        self.dropDownListCamera = Tk.OptionMenu(self.button_frame, self.listCamerasStr, *listCameras)
        self.listCamerasStr.set(listCameras[0])
        self.dropDownListCamera.pack(side=Tk.LEFT)
        # If no camera is available, disable button
        if self.numberOfCameras == 0:
            self.dropDownListCamera.config(state=Tk.DISABLED)

        # Add FPS label
        self.label_x1 = Tk.Label(self.button_frame, text="FPS:")
        self.label_x1.pack(side=Tk.LEFT)
        # Add FPS textbox
        self.textbox_fps = Tk.Text(self.button_frame, width=5, height=1)
        # ADD FPS value from settings
        self.textbox_fps.insert(Tk.END, int(self.curr_settings[IDX_FPS]))
        self.textbox_fps.pack(side=Tk.LEFT)

        # Fill list with available algorithms
        self.label_x2 = Tk.Label(self.button_frame, text="Algorithm:")
        self.label_x2.pack(side=Tk.LEFT)
        listAlgorithms = ['']

        # Choose prefered algorithm from settings
        if self.curr_settings[IDX_ALGORITHM] == 0:
            listAlgorithms.append("Estimate Heart rate")
            listAlgorithms.append("Filter waveform")
        elif self.curr_settings[IDX_ALGORITHM] == 1:
            listAlgorithms.append("Filter waveform")
            listAlgorithms.append("Estimate Heart rate")

        # Remove empty entry
        listAlgorithms.pop(0)
        self.listAlgorithmStr = Tk.StringVar()
        self.dropDownListAlgorithm = Tk.OptionMenu(self.button_frame, self.listAlgorithmStr, *listAlgorithms,
                                                   command=lambda _: self.__changeAlgorithm())
        self.listAlgorithmStr.set(listAlgorithms[0])
        self.dropDownListAlgorithm.pack(side=Tk.LEFT)

        # Add checkbox: Show curves
        self.check_button_1 = Tk.Checkbutton(master=self.button_frame, text="Show curves",
                                             command=lambda: settings.flip_parameter(settings.IDX_CURVES))
        self.check_button_1.pack(side=Tk.LEFT)
        if self.curr_settings[IDX_CURVES]:
            self.check_button_1.toggle()

        # Add checkbox: Store frames on hard disk
        self.check_button_2 = Tk.Checkbutton(master=self.button_frame, text="Store frames",
                                             command=lambda: settings.flip_parameter(settings.IDX_FRAMES))
        self.check_button_2.pack(side=Tk.LEFT)
        if self.curr_settings[IDX_FRAMES]:
            self.check_button_2.toggle()

        # Add start button
        self.button_start = Tk.Button(master=self.button_frame, text='Start', command=self.__start)
        self.button_start.pack(side=Tk.RIGHT)

    def __changeAlgorithm(self):
        if self.dropDownListAlgorithm.cget("text") == "Estimate Heart rate":
            settings.change_parameter(IDX_ALGORITHM, 0)
        elif self.dropDownListAlgorithm.cget("text") == "Filter waveform":
            settings.change_parameter(IDX_ALGORITHM, 1)

    def __openFiles(self):
        self.root.option_add('*Dialog.msg.font', 'Helvetica 10')
        tkMessageBox.showinfo("Information", "Please choose a folder containing files with increasing number"
                                             ", e.g. frame0.png frame1.png frame2.png ...")

        # Open Tk dialog
        self.dirName = askdirectory()

        if os.path.isdir(self.dirName):
            logging.info("User has chosen valid directory with images")

            # Define variables
            self.filesInDirSorted = []
            self.filesInDirSortedWithFilenameAndExtension = []

            try:

                # Get files in directory:
                # Format: Name + Number + Extension
                self.filesInDir = [f for f in listdir(self.dirName) if isfile(join(self.dirName, f))]

                # Remove file names and extensions from list of file.
                # Format: Number
                for currentFile in self.filesInDir:

                    # Get file name before index
                    m = re.search("\d", currentFile)
                    self.fileName = currentFile[:m.start()]

                    # Get file extension
                    m2 = re.search("\.", currentFile)
                    self.fileExtension = currentFile[m2.start():]

                    # Store numbers only
                    self.filesInDirSorted.append(currentFile[m.start():m2.start()])

                # Sort files
                self.filesInDirSorted.sort(key=int)

                # Add file name and extension again.
                # Format: Name + Number + Extension
                for currFile in self.filesInDirSorted:
                    self.filesInDirSortedWithFilenameAndExtension.append(self.fileName + currFile + self.fileExtension)

                # Store file names in camera thread
                self.cameraInstance.storeFramesFromDisk(self.dirName, self.filesInDirSortedWithFilenameAndExtension)

                # Update GUI
                self.dropDownListCamera.config(state=Tk.DISABLED)
                self.textbox_fps.config(state=Tk.DISABLED)
                self.textbox_fps.config(bg='lightgray')
                self.button_files.config(bg='green')
                self.button_files.config(state=Tk.DISABLED)

                # Show messagebox
                tkMessageBox.showinfo("Information", "Frames have been loaded. When all frames have been processed, "
                                                     "the program will reset.")

                logging.info("Files have been loaded successfully.")

            except:
                logging.error("Files in folder have a non-correct syntax.")
                tkMessageBox.showerror("Error", "The files in this directory do not have the correct syntax "
                                                "(e.g. frame0.png frame1.png frame2.png ...)")

        else:
            logging.error("User has chosen invalid directory with images")
            tkMessageBox.showerror("Error", "This directory is invalid. Please choose a valid one.")
