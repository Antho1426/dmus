#!/usr/local/bin/python2.7
# coding: utf-8




# dmus.py
# Python script that automatically extracts ".mp3" audio file from a video




## Required packages
import os
import sys
import pickle as cPickle
from workflow import Workflow

import glob
import os.path
import platform
import youtube_dl # version 2021.1.16 (i.e. the latest version of youtube_dl at the time of the development of this software) (simply reinstall youtube_dl to make sure to have the latest version: "pip uninstall youtube_dl" and then "pip install youtube_dl") (or install the specific youtube_dl version using "pip install 'youtube_dl==2021.1.16' --force-reinstall" (cf.: "Installing specific package versions with pip", https://stackoverflow.com/questions/5226311/installing-specific-package-versions-with-pip))
import applescript # (pip install applescript)
import moviepy.editor # for extracting ".mp3" audio file from ".mp4" video file
from pathlib import Path # for eventually getting the parent directory of the video file
from termcolor import colored # (pip install termcolor)
from validator_collection import checkers # to validate URLs (pip install validator-collection)
from pandas.io.clipboard import clipboard_get # to access the string situated in the clipboard




## Configurations

# Boolean value to print the debug print statements (when set to False, it allows to have a clean {query} output for the Alfred macOS X notifications)
#===========================
display_debug_prints = False
#===========================

# Setting the DOWNLOAD_DIRECTORY
DOWNLOAD_DIRECTORY = '/Users/anthony/Downloads' # name of the folder in which we will put the downloaded video file (this can be adjusted by the user)

# Moving to the "Downloads" directory
os.chdir(DOWNLOAD_DIRECTORY)




## Functions

def video_downloader(url):
    """
    Uses the youtube_dl Python package to download the ".mp4" video file(s) from a URL
    Cf.: https://www.bogotobogo.com/VideoStreaming/YouTube/youtube-dl-embedding.php

    Args:
        url (str): The URL of the video

    Returns:
        video_paths_list (list): List containing the absolute file path(s) of the downloaded video file(s)
    """

    # Getting the number of ".mp4" files preliminarily (i.e. before downloading the ".mp4" video files) situated in the DOWNLOAD_DIRECTORY
    number_mp4_DOWNLOAD_DIRECTORY_before_download = len(glob.glob1(DOWNLOAD_DIRECTORY, "*.mp4"))

    ydl_opts = {
        'format': 'bestautio/best', #'mp4', #'bestautio/best'
        'quiet': True,
        # 'postprocessors': [{
        #     'key': 'FFmpegExtractAudio',
        #     'preferredcodec': 'mp3',
        #     'preferredquality': '192',
        # }]
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        returned_value = ydl.download([url]) # downloading the video
        if display_debug_prints:
            print(' returned_value: {0}'.format(returned_value))

    # Getting the number of ".mp4" files situated in the DOWNLOAD_DIRECTORY after downloading the ".mp4" video file(s)
    number_mp4_DOWNLOAD_DIRECTORY_after_download = len(glob.glob1(DOWNLOAD_DIRECTORY, "*.mp4"))

    # Getting the number of downloaded ".mp4" video file(s)
    number_of_downloaded_videos = number_mp4_DOWNLOAD_DIRECTORY_after_download - number_mp4_DOWNLOAD_DIRECTORY_before_download

    # Getting (all) the new ".mp4" video file(s) of the current post
    video_files = glob.glob(DOWNLOAD_DIRECTORY + "/*.mp4")
    video_files.sort(key=os.path.getctime, reverse=True)
    new_video_files = video_files[0:number_of_downloaded_videos]
    video_file_path_list = []
    for i in range(number_of_downloaded_videos):
        video_file_path = new_video_files[i]
        video_file_path_list.append(video_file_path)

    return returned_value, video_file_path_list


def extract_audio(video_file_path_list):
    """
    Extracts ".mp3" audio file from ".mp4" video file
    Cf.: https://www.codespeedy.com/extract-audio-from-video-using-python/

    Args:
        video_file_path_list (list): List containing (all) the downloaded video absolute file path(s)

    Returns:
        no_error (int): Number equal to "1" in case there is no error and "0" in case (at least one of) the conversion(s) failed
    """

    no_error = 1

    for video_file_path in video_file_path_list:

        try:
            # Creating video object
            video = moviepy.editor.VideoFileClip(video_file_path)
            # Retrieving audio object from video object
            audio = video.audio
            # Composing absolute audio file path
            audio_file_path = video_file_path.replace('.mp4', '.mp3')
            # Writing audio file
            audio.write_audiofile(audio_file_path, logger=None) # Cf.: "Moviepy still prints a progress bar even after setting `verbose` to `False`" (https://stackoverflow.com/questions/42695735/moviepy-still-prints-a-progress-bar-even-after-setting-verbose-to-false)
            if display_debug_prints:
                # Printing success message
                print(' ✅ ".mp3" of "{0}" successfully extracted!'.format(video_file_path))
            no_error *= 1

        except Exception as e:
            colored_error_message = colored('"{0}" could not be converted into ".mp3"!'.format(video_file_path), 'red', attrs=['reverse', 'blink'])
            if display_debug_prints:
                print(' ❌ ERROR! ' + colored_error_message + '\n Error message:\n  {0}'.format(e))
            no_error *= 0

    return no_error


def add_metadata(url, video_file_path_list, no_error):
    """
    Writes comment in metadata "Comments" part of file

    Args:
        url (str): The URL of the video
        video_file_path_list (list): List containing (all) the downloaded video absolute file path(s)
    """

    for video_file_path in video_file_path_list:
        audio_file_path = video_file_path.replace('.mp4', '.mp3')

        try:
            # Writing comment in metadata "Comments" part of the current ".mp3" file
            write_metadata_comment(audio_file_path, url)
            no_error *= 1

        except Exception as e:
            colored_error_message = colored('URL could NOT be written to metadata "Comments" part of "{0}"!'.format(audio_file_path), 'red', attrs=['reverse', 'blink'])
            if display_debug_prints:
                print(' ❌ ERROR! ' + colored_error_message + '\n Error message:\n  {0}'.format(e))
            no_error *= 0

    return no_error


def write_metadata_comment(file_path, comment):
    """
    Writes comment in metadata "Comments" part of file (in case the operating system on which the program is running is macOS)

    Args:
        file_path (str): The absolute video file path
        comment (str): The comment to insert in the metadata "Comments" part of the video file
    """

    if platform.system() == 'Darwin':
        script = 'set comment of (POSIX file "{0}" as alias) to "{1}" as Unicode text'.format(file_path, comment) # cf.: "Try to define your string as unicode: u'Nom du professeur’" (https://www.odoo.com/forum/help-1/unicodedecodeerror-ascii-codec-can-t-decode-byte-0xc3-in-position-27-ordinal-not-in-range-128-20737)
        applescript.tell.app("Finder", script.decode('utf-8'))
    else:
        if display_debug_prints:
            print(colored("Error!", 'red'), 'Writing comment in metadata "Comments" part of file is currently ONLY supported for macOS.')




## Main process
def main(wf):


    ## Procedure
    #-------------------------------

    # 1) Retrieving stored clipboard value
    if display_debug_prints:
        print('\n1) Retrieving stored clipboard value') # If we have a "Large Type" block connected at the output of the "/bin/bash Run Script" block, this will print "1) Retrieving stored clipboard value" on the screen
    clipboard_value = clipboard_get()
    if display_debug_prints:
        print(' clipboard_value: {0}'.format(clipboard_value.encode('utf-8')))
    
    # 2) Identifying clipboard value (either video file path or URL)
    if display_debug_prints:
        print('2) Identifying clipboard value...')

    # FILE PATH case
    if os.path.isfile(clipboard_value): # checking if the file exists on the computer (cf.: https://linuxize.com/post/python-check-if-file-exists/)
        if display_debug_prints:
            print(' ✅ Existence of the video file approved!')
        video_file_path = clipboard_value
        video_file_path_list = [video_file_path]

        # 3) Extracting the ".mp3" audio file from the ".mp4" video file
        if display_debug_prints:
            print('3) Extracting the ".mp3" audio file from the ".mp4" video file')
        no_error = extract_audio(video_file_path_list)

        if no_error:
            #------- output {query} message -------
            print('🏆 Audio extraction successful!')
            #--------------------------------------
        else:
            #------- output {query} message -------
            print('❌ ERROR! Audio file extraction failed...')
            #--------------------------------------

    # URL case
    elif checkers.is_url(clipboard_value): # checking the validity of the URL (cf.: https://validator-collection.readthedocs.io/en/latest/checkers.html)
        url = clipboard_value
        if display_debug_prints:
            print(' ✅ Validity of video URL approved!')
        returned_value = 0
        video_file_path_list = []

        # 3) Downloading ".mp4" video file(s) using youtube_dl in DOWNLOAD_DIRECTORY
        if display_debug_prints:
            print('3) Downloading ".mp4" video file using youtube_dl in {0}'.format(DOWNLOAD_DIRECTORY))
        try:
            returned_value, video_file_path_list = video_downloader(url)
        except Exception as e:
            colored_error_message = colored('Audio download using youtube_dl failed... (Make sure you are connected to Internet!)', 'red', attrs=['reverse', 'blink'])
            if display_debug_prints:
                print('❌ ERROR! ' + colored_error_message + '\n Error message:\n  {0}'.format(e))
            #------- output {query} message -------
            print('❌ ERROR! Video download failed...')
            #--------------------------------------
            # Exiting the program
            exit(1)
        if returned_value != 0:
            colored_error_message = colored('Audio download using youtube_dl failed... (/!\ returned_value !=0) (Make sure you are connected to Internet!)', 'red', attrs=['reverse', 'blink'])
            if display_debug_prints:
                print('❌ ERROR! ' + colored_error_message)
            #------- output {query} message -------
            print('❌ ERROR! Video download failed...')
            #--------------------------------------
            # Exiting the program
            exit(1)
        
        # 4) Extracting the ".mp3" audio file(s) from the downloaded ".mp4" video file(s) in the DOWNLOAD_DIRECTORY
        if display_debug_prints:
            print('4) Extracting ".mp3"')
        no_error = extract_audio(video_file_path_list)

        # 5) Deleting the downloaded video file(s)
        if display_debug_prints:
            print('5) Deleting the downloaded video files')
        for video_file_path in video_file_path_list:
            os.remove(video_file_path)

        # 6) Writing URL to metadata "Comments" part of the converted ".mp3" file(s)
        if display_debug_prints:
            print('6) Writing URL to metadata "Comments" part of the converted ".mp3" file(s)')
        no_error = add_metadata(url, video_file_path_list, no_error)

        # 7) Cleaning the name of the downloaded ".mp3" file(s)
        if display_debug_prints:
            print('7) Cleaning the name(s) of the downloaded ".mp3" file(s)')
        for video_file_path in video_file_path_list:
            audio_file_path = video_file_path.replace('.mp4', '.mp3')
            audio_file_path_new = audio_file_path.split('.mp3')[0][0:len(audio_file_path)-16] + '.mp3'
            os.rename(audio_file_path, audio_file_path_new)

        if no_error and returned_value==0:
            #------- output {query} message -------
            print('🏆 Audio download successful!')
            #--------------------------------------
        else:
            #------- output {query} message -------
            print('❌ ERROR! Audio file extraction failed...')
            #--------------------------------------

    # UNIDENTIFIED case
    else:
        colored_error_message = colored('Invalid video path or URL...', 'red', attrs=['reverse', 'blink'])
        if display_debug_prints:
            print(' ❌ ERROR! ' + colored_error_message)
        
        #------- output {query} message -------
        print('❌ ERROR! Invalid path or URL...')
        #--------------------------------------

        # Exiting the program
        exit(1)
    
    #-------------------------------




if __name__ == u'__main__':
    wf = Workflow()
    sys.exit(wf.run(main))