#!/usr/local/bin/python2.7
# coding: utf-8
# (Above line --> cf.: "How to make the python interpreter correctly handle non-ASCII characters in string operations?" (https://stackoverflow.com/questions/1342000/how-to-make-the-python-interpreter-correctly-handle-non-ascii-characters-in-stri))


# dmus.py


#==================
debugModeOn = False
#==================


## Setting the current working directory automatically
import os
project_path = os.getcwd() # getting the path leading to the current working directory
os.getcwd() # printing the path leading to the current working directory
os.chdir(project_path) # setting the current working directory based on the path leading to the current working directory


## Required packages
import glob
import os.path
import platform
import osascript
import applescript # (pip install applescript)
import moviepy.editor # for extracting ".mp3" audio file from ".mp4" video file
from pathlib import Path # for eventually getting the parent directory of the video file from which to extract the audio
from termcolor import colored # (pip install termcolor)
from playsound import playsound # for playing the notification sound
from argparse import ArgumentParser
from validator_collection import checkers # to validate URLs (pip install validator-collection)
from pandas.io.clipboard import clipboard_get # to access the string situated in the clipboard


## Configurations

# Setting the DOWNLOAD_DIRECTORY
DOWNLOAD_DIRECTORY = '/Users/anthony/Downloads' # name of the folder in which we will put the downloaded audio file(s) (this can be adjusted by the user)

# Moving to the "Downloads" directory
os.chdir(DOWNLOAD_DIRECTORY)

# Sound paths
sound_path_start = '/System/Library/Sounds/Blow.aiff'
sound_path_success = '/System/Library/Sounds/Hero.aiff'
sound_path_fail = '/System/Library/Sounds/Sosumi.aiff'


## Parsing the input argument
if not debugModeOn:
    parser = ArgumentParser(description='"dmus.py" is a Python program that\
        allows to retrieve the ".mp3" audio file from either a video URL or a video file path.\
        The software currently supports videos hosted on at least following platforms: \
        YouTube, Instagram. In case a video doesn\'t come from one of the above-mentioned \
        websites, the program might not work and the ".mp3" audio file might not be retrieved.')
    parser.add_argument('--vid', metavar='/my/video/url/or/file/path', type=str, default='clipboard', help='extract the ".mp3" audio content of the video url or video file path')
    args = parser.parse_args()
    argsVid = args.vid
else: # in case we are in "debug mode"
    argsVid = 'video information required'


## Tests (clipboard_value examples)
if argsVid == 'video information required':
    #--- FILE PATH
    # ✅ Absolute file path of existing video:
    #argsVid = project_path + '/tests/test-vid.mp4'
    # ✅ Absolute file path of nonexistent video:
    #argsVid = project_path + '/tests/tada.mp4'
    #--- YOUTUBE
    # ✅ URL of YouTube video resulting in a ".mp4" file if downloaded using the below youtube-dl options
    #argsVid = 'https://www.youtube.com/watch?v=1vnnFYTZGRI'
    # ✅ URL of YouTube video
    #argsVid = 'https://www.youtube.com/watch?v=UIrGxHhdqXo'
    # ✅ URL of YouTube video
    #argsVid = 'https://www.youtube.com/watch?v=A_H8t0OqyQ0'
    # ✅ URL of YouTube video presenting encoding problem for writing metadata ("UnicodeDecodeError: 'ascii' codec can't decode byte 0xc3 in position 26: ordinal not in range(128)")
    # (YouTube video called "MØ - When I Was Young (Lyrics _ Lyric Video)")
    argsVid = 'https://www.youtube.com/watch?v=FVGXaglgCVk'
    # ✅ URL of YouTube video that is NO MORE available
    #argsVid = 'https://youtu.be/UjrlC9mGCD'
    #--- INSTAGRAM
    # ✅ URL of Instagram post containing SEVERAL Instagram videos:
    #argsVid = 'https://www.instagram.com/p/B_-gogqAtuU/?igshid=1pjsrn7we7kdu'
    # ✅ URL of Instagram post containing ONE single Instagram video:
    #argsVid = 'https://www.instagram.com/p/B_3hd-kDVpq/?igshid=r8fbjeekqiv7'
    # ✅ URL of Instagram post containing only ".jpg" files (the program then returns no error but works fine, no video is downloaded and nothing bad happens):
    #argsVid = 'https://www.instagram.com/p/BxCvRcalCsi/'
    # ✅ URL of Instagram post that is NO MORE available
    #argsVid = 'https://instagram.com/p/B-VHAIzpd57/'


## Functions

def audio_downloader(url):
    """
    Uses the youtube_dl Python package to download the ".mp3" audio file(s) from a URL

    Args:
        url (str): The URL of the video

    Returns:
        audio_paths_list (list): List containing the absolute file path(s) of the downloaded audio file(s)
    """

    # Trying to dynamically upgrade youtube_dl (cf.: "How do I update a Python package?" (https://stackoverflow.com/questions/5183672/how-do-i-update-a-python-package))
    # (The code below works but takes at least 10[s] to run, which significantly slows down the overall process...)
    #---
    #print(' Trying to dynamically upgrade youtube_dl...')
    #returned_value_upgrade_ytdl = os.system('pip install youtube_dl --upgrade')
    #---

    # Getting the number of ".mp3" files preliminarily (i.e. before downloading the ".mp3" audio file(s)) situated in the DOWNLOAD_DIRECTORY
    number_mp3_DOWNLOAD_DIRECTORY_before_download = len(glob.glob1(DOWNLOAD_DIRECTORY, "*.mp3"))

    command = 'youtube-dl --extract-audio --audio-format mp3 ' + url
    returned_value = os.system(command)
    print("youtube_dl returned_value: ", returned_value) # prints "0" (this means that the command run successfully)

    # Getting the number of ".mp3" files situated in the DOWNLOAD_DIRECTORY after downloading the ".mp3" audio file(s)
    number_mp3_DOWNLOAD_DIRECTORY_after_download = len(glob.glob1(DOWNLOAD_DIRECTORY, "*.mp3"))

    # Getting the number of downloaded ".mp3" audio file(s)
    number_of_downloaded_audios = number_mp3_DOWNLOAD_DIRECTORY_after_download - number_mp3_DOWNLOAD_DIRECTORY_before_download

    # Getting (all) the new ".mp3" audio file(s) of the current post
    audio_files = glob.glob(DOWNLOAD_DIRECTORY + "/*.mp3")
    audio_files.sort(key=os.path.getctime, reverse=True)
    new_audio_files = audio_files[0:number_of_downloaded_audios]
    audio_file_path_list = []
    for i in range(number_of_downloaded_audios):
        audio_file_path = new_audio_files[i]
        audio_file_path_list.append(audio_file_path)
    print(' audio_file_path_list: {0}'.format(audio_file_path_list))

    return returned_value, audio_file_path_list


def extract_audio(video_file_path):
    """
    Extracts ".mp3" audio file from a ".mp4" video file
    Cf.: https://www.codespeedy.com/extract-audio-from-video-using-python/

    Args:
        video_file_path (str): Video absolute file path

    Returns:
        no_error (int): Number equal to "1" in case there is no error and "0" in case the conversion failed
    """

    no_error = 1

    try:
        # Creating video object
        video = moviepy.editor.VideoFileClip(video_file_path)
        # Retrieving audio object from video object
        audio = video.audio
        # Composing absolute audio file path
        audio_file_path = video_file_path.replace('.mp4', '.mp3')
        # Writing audio file
        audio.write_audiofile(audio_file_path, logger=None) # Cf.: "Moviepy still prints a progress bar even after setting `verbose` to `False`" (https://stackoverflow.com/questions/42695735/moviepy-still-prints-a-progress-bar-even-after-setting-verbose-to-false)
        # Printing success message
        print(' ✅ ".mp3" of "{0}" successfully extracted!'.format(video_file_path))
        no_error *= 1

    except Exception as e:
        colored_error_message = colored('"{0}" could not be converted into ".mp3"!'.format(video_file_path), 'red', attrs=['reverse', 'blink'])
        print(' ❌ ERROR! ' + colored_error_message + '\n Error message:\n  {0}'.format(e))
        no_error *= 0

    return no_error


def add_metadata(url, audio_file_path_list):
    """
    Writes comment in metadata "Comments" part of file

    Args:
        url (str): The URL of the video(s)
        audio_file_path_list (list): List containing the absolute file path(s) of the downloaded audio file(s)
    """

    for audio_file_path in audio_file_path_list:

        try:
            # Writing comment in metadata "Comments" part of the current ".mp3" file
            write_metadata_comment(audio_file_path, url)

        except Exception as e:
            colored_error_message = colored('URL could NOT be written to metadata "Comments" part of "{0}"!'.format(audio_file_path), 'red', attrs=['reverse', 'blink'])
            print(' ❌ ERROR! ' + colored_error_message + '\n Error message:\n  {0}'.format(e))


def write_metadata_comment(file_path, comment):
    """
    Writes comment in metadata "Comments" part of file (in case the operating system on which the program is running is macOS)

    Args:
        file_path (str): The absolute audio file path
        comment (str): The comment to insert in the metadata "Comments" part of the audio file
    """

    if platform.system() == 'Darwin':
        script = 'set comment of (POSIX file "{0}" as alias) to "{1}" as Unicode text'.format(file_path, comment) # cf.: "Try to define your string as unicode: u'Nom du professeur’" (https://www.odoo.com/forum/help-1/unicodedecodeerror-ascii-codec-can-t-decode-byte-0xc3-in-position-27-ordinal-not-in-range-128-20737)
        applescript.tell.app("Finder", script.decode('utf-8'))
    else:
        print(colored("Error!", 'red'), 'Writing comment in metadata "Comments" part of file is currently ONLY supported for macOS.')


def notify(title, subtitle, message, sound_path):
    """
    Posts macOS X notification

    Args:
        title (str): The title
        subtitle (str): The subtitle
        message (str): The message
        sound_path (str): The file path of the ".wav" audio file
    """

    # Playing sound
    playsound(sound_path)
    # Displaying the Desktop notification
    t = '-title {!r}'.format(title)
    s = '-subtitle {!r}'.format(subtitle)
    m = '-message {!r}'.format(message)
    os.system('terminal-notifier {}'.format(' '.join([m, t, s])))


## Main process

# Launching initial notification
notify(title='dmus.py',
       subtitle='Running dmus.py script to extract audio',
       message='Audio extraction process started...',
       sound_path=sound_path_start)


if argsVid == 'clipboard': # this is True (i.e. argsVid == 'clipboard') only if debugModeOn is set to "False"
    # 1) Retrieving stored clipboard value
    print('\n1) Retrieving stored clipboard value')
    clipboard_value = clipboard_get()
else:
    # 1) Retrieving the video argument (i.e. either a video URL or video file path)
    print('\n1) Retrieving the video argument')
    clipboard_value = argsVid
print(' clipboard_value: {0}'.format(clipboard_value.encode('utf-8')))

# 2) Identifying clipboard value (either video file path or URL)
print('2) Identifying clipboard value...')

# FILE PATH case
if os.path.isfile(clipboard_value): # checking if the file exists on the computer (cf.: https://linuxize.com/post/python-check-if-file-exists/)
    print(' ✅ Existence of the video file approved!')
    video_file_path = clipboard_value

    # 3) Extracting the ".mp3" audio file from the ".mp4" video file
    print('3) Extracting the ".mp3" audio file from the ".mp4" video file')
    no_error = extract_audio(video_file_path)

    # 4) Posting macOS X notification
    print('4) Posting macOS X notification')
    parent_directory = Path(video_file_path).parent
    notify(title='dmus.py',
           subtitle='Audio file extracted :-)',
           message='The ".mp3" audio file is available in {0}'.format(parent_directory),
           sound_path=sound_path_success)
    # Exiting the iTerm2 window
    osascript.run('tell application "iTerm2" to close first window')

# URL case
elif checkers.is_url(clipboard_value): # checking the validity of the URL (cf.: https://validator-collection.readthedocs.io/en/latest/checkers.html)
    url = clipboard_value
    print(' ✅ Validity of video URL approved!')
    returned_value = 0
    audio_file_path_list = []

    # 3) Downloading ".mp3" audio file(s) using youtube_dl in DOWNLOAD_DIRECTORY
    print('3) Downloading ".mp3" audio file(s) using youtube_dl in {0}'.format(DOWNLOAD_DIRECTORY))
    try:
        returned_value, audio_file_path_list = audio_downloader(url)
    except Exception as e:
        colored_error_message = colored('Audio download using youtube_dl failed... (Make sure you are connected to Internet!)', 'red', attrs=['reverse', 'blink'])
        print('❌ ERROR! ' + colored_error_message + '\n Error message:\n  {0}'.format(e))
        # Posting macOS X notification
        notify(title='dmus.py',
               subtitle='Audio download using youtube_dl failed :-(',
               message='Make sure you are connected to Internet!',
               sound_path=sound_path_fail)
        # Exiting the iTerm2 window
        osascript.run('tell application "iTerm2" to close first window')
        # Exiting the program
        exit(1)
    if returned_value != 0:
        colored_error_message = colored('Audio download using youtube_dl failed... (/!\ returned_value !=0) (Make sure you are connected to Internet!)', 'red', attrs=['reverse', 'blink'])
        print('❌ ERROR! ' + colored_error_message)
        # Posting macOS X notification
        notify(title='dmus.py',
               subtitle='Audio download using youtube_dl failed :-(',
               message='Make sure you are connected to Internet!',
               sound_path=sound_path_fail)
        # Exiting the iTerm2 window
        osascript.run('tell application "iTerm2" to close first window')
        # Exiting the program
        exit(1)

    # 4) Writing URL to metadata "Comments" part of the downloaded ".mp3" file(s)
    print('4) Writing URL to metadata "Comments" part of the downloaded ".mp3" file(s)')
    add_metadata(url, audio_file_path_list)

    # 5) Cleaning the name of the downloaded ".mp3" file(s)
    print('5) Cleaning the name(s) of the downloaded ".mp3" file(s)')
    for audio_file_path in audio_file_path_list:
        audio_file_path_new = audio_file_path.split('.mp3')[0][0:len(audio_file_path)-16] + '.mp3'
        os.rename(audio_file_path, audio_file_path_new)

    # 6) Posting macOS X notification
    print('6) Posting macOS X notification')
    if len(audio_file_path_list) > 1:
        subtitle = 'Audio files downloaded :-)'
        message = 'The ".mp3" audio files are available in {0}'.format(DOWNLOAD_DIRECTORY)
    else:
        subtitle = 'Audio file downloaded :-)'
        message = 'The ".mp3" audio file is available in {0}'.format(DOWNLOAD_DIRECTORY)
    notify(title='dmus.py',
           subtitle=subtitle,
           message=message,
           sound_path=sound_path_success)
    # Exiting the iTerm2 window
    osascript.run('tell application "iTerm2" to close first window')
    # Exiting the program
    exit(1)

# UNIDENTIFIED case
else:
    colored_error_message = colored('Invalid video path or URL...', 'red', attrs=['reverse', 'blink'])
    print(' ❌ ERROR! ' + colored_error_message)

    # Posting macOS X notification
    notify(title='dmus.py',
           subtitle='Audio file extraction failed :-(',
           message='Invalid video path or URL...',
           sound_path=sound_path_fail)
    # Exiting the iTerm2 window
    osascript.run('tell application "iTerm2" to close first window')
    # Exiting the program
    exit(1)