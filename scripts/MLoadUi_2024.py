import os
import sys
import subprocess
from PySide2.QtWidgets import QApplication, QMessageBox, QWidget,  QPushButton, QShortcut, QVBoxLayout, QLabel, QFileDialog, QHBoxLayout, QSpacerItem, QSizePolicy, QFrame, QLineEdit, QGridLayout, QComboBox, QStackedLayout, QSlider
from PySide2.QtCore import Qt, QTimer, QSize, QEvent, QUrl, QThread, QObject, Slot
from PySide2.QtGui import QImage, QPixmap, QFont, QIntValidator, QTransform, QKeySequence
import imp
import customWidgets as cw
imp.reload(cw)
import styleSheet
imp.reload(styleSheet)
import editorSettingsWindow as sett
imp.reload(sett)
import ntpath
import json
from pathlib import Path
import shutil
import maya.cmds as cmds
import threading
import maya.OpenMaya as om
import maya.OpenMayaAnim as oma
from maya import OpenMayaUI as omui
import maya.mel as mel
import inspect 
from shiboken2 import wrapInstance
import time
from PySide2.QtMultimedia import QMediaPlayer, QMediaContent
import tempfile
import gc


def _getMainMayaWindow():
    mayaMainWindowPtr = omui.MQtUtil.mainWindow()
    mayaMainWindow = wrapInstance(int(mayaMainWindowPtr), QWidget)
    return mayaMainWindow

sceneFrameRate = 1.0 / om.MTime(1.0, om.MTime.uiUnit()).asUnits(om.MTime.kSeconds) 
animationStartTime = oma.MAnimControl.animationStartTime().value()
playbackStartTime = oma.MAnimControl.minTime().value()

script_directory = (os.path.dirname(os.path.abspath( 
    inspect.getfile(inspect.currentframe()))) ).replace(os.sep, '/')


def import_scoped_cv2():
    if os.name == 'nt':
        cv2_path = f"{script_directory}/cv2Bundle"
    else:
        cv2_path = f"{script_directory}/cv2Bundle/cv2"
    
    if cv2_path not in sys.path:
        sys.path.insert(0, cv2_path)

    try:
        import cv2
        return cv2
    except Exception as e:
        print(f"❌ Failed to import cv2 from {cv2_path}: {e}")
        return None
    finally:
        # Clean up so it doesn't stay in global path
        if cv2_path in sys.path:
            sys.path.remove(cv2_path)

class ReferenceEditor(QWidget):

    def __init__(self, file, parent=None):
        super(ReferenceEditor, self).__init__(parent)
        self.installEventFilter(self)

        self.cv2 = import_scoped_cv2()
        if not self.cv2:
            QMessageBox.warning(self, "Import Error", "OpenCV/NumPy not available. Some features will be disabled.")
        self.cv2.setUseOptimized(True)
        
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.start_time = None
        self.cap = None
        self.speed = 1

        self.input_path = file
        self.input_type = 1
        self.file_name_list = ntpath.basename(file).rsplit(".", 1)
        self.file_nice_name  = ''.join([char for char in self.file_name_list[0] if char.isalnum()])
        self.my_ref_folder = None

        self.pathConfig_file = Path(f"{script_directory}/pathconfig.txt")
        self.cacheConfig_file = Path(f"{script_directory}/cacheconfig.txt")
        self.plateConfig_file = Path(f"{script_directory}/plateconfig.txt")

        #Caching
        self.cacheThread = QThread()
        self.cacheWorker = CacheWorker()
        self.cacheWorker.moveToThread(self.cacheThread)
        self.frame_cache = cw.CacheDict(800, 750, 50, 35)

        #Audio
        self.audio_player = QMediaPlayer()
        temp_dir = tempfile.gettempdir()
        self.temp_audio_path = os.path.join(temp_dir, "re_temp_audio.wav")


        ### Ui elements ###

        # VIDEO
        self.video_label = cw.CropLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(1, 1)
        self.video_label.setStyleSheet("background-color: black; color: white;")
        self.video_label.setScaledContents(False)

        # FRAME COUNT
        self.FC_label = QLabel("1", self)
        self.FC_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.FC_label.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum))
        self.FC_label.setStyleSheet(f"background-color: black; color: rgb{self.ecol(1)};")
        self.FC_label.setFont(self.efont(12))

        self.frameCount_label = QLabel("1 frames", self)
        self.frameCount_label.setContentsMargins(0, 0, 0, 5)
        self.frameCount_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.frameCount_label.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum))
        self.frameCount_label.setStyleSheet(f"background-color: black; color: rgb{self.ecol(.8)};")
        self.frameCount_label.setMinimumSize(QSize(60, 0))
        self.frameCount_label.setFont(self.efont(7))
        
        # SLIDER
        self.slider = cw.VideoRangeSlider()
        self.slider.setSizePolicy(QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Maximum))
        self.slider.setEnabled(self.input_type)

        # PLAYBACK SPEED
        self.empty_label = QLabel("", self)
        self.empty_label.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum))
        self.empty_label.setFont(self.efont(12))

        self.playbackSpeed_label = QLabel(self)
        self.playbackSpeed_label.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum))
        self.playbackSpeed_label.setMinimumSize(QSize(30, 0))
        self.playbackSpeed_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.playbackSpeed_label.setStyleSheet(f"background-color: black; color: rgb{self.ecol(.8)};")
        self.playbackSpeed_label.setContentsMargins(0, 0, 6, 5)
        self.playbackSpeed_label.setFont(self.efont(7))

        # FPS SETTER
        self.setFPS_Label = QLabel("", self)
        self.setFPS_Label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.setFPS_Label.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum))
        self.setFPS_Label.setStyleSheet(f"color: rgb{self.ecol(1)};")
        self.setFPS_Label.setFont(self.efont(12))
        self.setFPS_Label.setText(f"FPS [{str(1000/self.speed)}]:")

        self.setFPS_lineEdit = cw.AutoLineEdit()
        self.setFPS_lineEdit.setValidator(QIntValidator(1, 2147483647))
        self.setFPS_lineEdit.returnPressed.connect(self.set_stacked_widget)
        self.setFPS_lineEdit.editingFinished.connect(self.editing_finished)
        self.setFPS_lineEdit.setStyleSheet(styleSheet.Black_line_edit_style())

        
        # SEPARATOR
        self.line = QFrame(self)
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        # DATA TABLE

        def data_title(name, style):
            dataLabel = QLabel(name, self)
            dataLabel.setSizePolicy(QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Maximum))
            dataLabel.setContentsMargins(50, 0, 0, 0)
            dataLabel.setMargin(4)
            style_func = getattr(styleSheet, f"{style}_style", None)
            dataLabel.setStyleSheet(style_func())
            return dataLabel

        self.sourceData_label = data_title("Source metadata", "Dark")
        self.sourceData_label.setContentsMargins(0, 4, 0, 3)
        self.sourceData_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.convertForMaya_label = data_title("Cconvert for Maya", "Dark")
        self.convertForMaya_label.setContentsMargins(0, 4, 0, 3)
        self.convertForMaya_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sourceFramerate_label = data_title("", "Light")
        self.sourceResolution_label = data_title("", "Dark")
        self.sourceFormat_label = data_title("", "Light")
        self.sourceStartAt_label = data_title("", "Dark")

        def data_label(name, style):
            datalabel = QLabel(name, self)
            datalabel.setMinimumSize(QSize(90, 10))
            datalabel.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))
            datalabel.setContentsMargins(15, 0, 0, 0)
            style_func = getattr(styleSheet, f"{style}_style", None)
            datalabel.setStyleSheet(style_func())
            return datalabel

        self.fill_label = data_label("", "Dark")
        self.framerate_label = data_label("Framerate", "Light")
        self.resolution_label = data_label("Resolution", "Dark")
        self.format_label = data_label("Fromat", "Light")
        self.startAt_label = data_label("Start at", "Dark")


        def my_comboBox(n, style):
            if n == 0:
                myComboBox = QComboBox(self)
            elif n == 1:
                myComboBox = cw.EComboBox(self)
            myComboBox.setMinimumHeight(10)
            myComboBox.setSizePolicy(QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum))
            style_func = getattr(styleSheet, f"{style}_style", None)
            myComboBox.setStyleSheet(style_func())
            return myComboBox
        
        self.framerate_comboBox = my_comboBox(1, "Light")
        self.resolution_comboBox = my_comboBox(0, "Dark")
        self.format_comboBox = my_comboBox(0, "Light")
        self.startAt_comboBox = my_comboBox(1, "Dark")

        # MY BUTTONS 
        def my_PushButton(name,size):
            myPushButton = cw.IconButton(name)
            myPushButton.setObjectName(name)
            sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
            sizePolicy2.setHorizontalStretch(0)
            sizePolicy2.setVerticalStretch(0)
            sizePolicy2.setHeightForWidth(myPushButton.sizePolicy().hasHeightForWidth())
            myPushButton.setSizePolicy(sizePolicy2)
            myPushButton.setEnabled(self.input_type)
            myPushButton.setMinimumSize(QSize(size, 24))

            style_func = getattr(styleSheet, f"{name}_style", None)
            if callable(style_func):  
                myPushButton.setStyleSheet(styleSheet.button_style() + style_func())
            else:
                myPushButton.setStyleSheet(styleSheet.button_style())
            return myPushButton

        def my_button_layout(size, **kwargs):
            twoButton_layout = QHBoxLayout()
            twoButton_layout.setSpacing(0)
            for name in kwargs.values():
                twoButton_layout.addWidget(my_PushButton(name, size))
            return twoButton_layout


        self.helpLine_lineEdit = QLineEdit()
        self.helpLine_lineEdit.setReadOnly(True)
        self.helpLine_lineEdit.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.helpLine_lineEdit.setStyleSheet(styleSheet.Help_line_style())

        self.reset_pushbutton = cw.IconButton("Reset")
        self.reset_pushbutton.setFixedSize(32, 28)
        self.reset_pushbutton.setStyleSheet(styleSheet.Dark_button_style())

        self.info_pushbutton = cw.IconButton("Info")
        self.info_pushbutton.setFixedSize(32, 28)
        self.info_pushbutton.setStyleSheet(styleSheet.Dark_button_style())

        self.volume_pushbutton = cw.IconButton("Volume")
        self.volume_pushbutton.setFixedSize(32, 28)
        self.volume_pushbutton.setStyleSheet(styleSheet.Dark_button_style())
        self.volume_pushbutton.setCheckable(True)
        self.volume_pushbutton.setChecked(False)

        self.confirm_pushbutton = QPushButton("Confirm")
        self.confirm_pushbutton.setMinimumSize(120, 30)
        self.confirm_pushbutton.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum))
        self.confirm_pushbutton.setStyleSheet(styleSheet.Dark_button_style())

        self.volume_slider = QSlider(Qt.Horizontal, self)
        self.volume_slider.setFixedSize(QSize(90, 28))
        self.volume_slider.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed))
        self.volume_slider.setStyleSheet(styleSheet.slider_style())

        ### Layout ###
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(self.video_label)

        slider_widget = cw.FilledWidget(38, "black", self)
        self.stacked_layout = QStackedLayout()

        self.slider_layout = cw.FilledWidget(38, "black", self)
        self.FC_layout = QVBoxLayout()
        self.FC_layout.addWidget(self.FC_label)
        self.FC_layout.addWidget(self.frameCount_label)
        self.slider_layout.layout.addLayout(self.FC_layout)
        self.slider_layout.layout.addWidget(self.slider)
        self.fps_layout = QVBoxLayout()
        self.fps_layout.addWidget(self.empty_label)
        self.fps_layout.addWidget(self.playbackSpeed_label)
        self.slider_layout.layout.addLayout(self.fps_layout)

        self.setfps_layout = cw.FilledWidget(38, "black", self)
        self.setfps_layout.layout.setContentsMargins(10, 0, 10, 0)
        self.setfps_layout.layout.setSpacing(10)
        self.setfps_layout.layout.addWidget(self.setFPS_Label)
        self.setfps_layout.layout.addWidget(self.setFPS_lineEdit)

        self.stacked_layout.addWidget(self.slider_layout)
        self.stacked_layout.addWidget(self.setfps_layout)
        slider_widget.layout.addLayout(self.stacked_layout)

        layout.addWidget(slider_widget)

        playBar_layout = cw.FilledWidgetGradient(32, self)
        playBar_layout.layout.addItem(QSpacerItem(120, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))
        playBar_layout.layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        playBar_layout.layout.addLayout(my_button_layout( 33, name1 = u"Step_one_frame_backwards", name2 = u"Step_one_frame_forwards"))
        playBar_layout.layout.addItem(QSpacerItem(30, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))
        playBar_layout.layout.addLayout(my_button_layout( 55, name1 = u"Play_forwards"))
        playBar_layout.layout.addItem(QSpacerItem(30, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))
        playBar_layout.layout.addLayout(my_button_layout( 33, name1 = u"Set_range_start", name2 = u"Set_range_end"))
        playBar_layout.layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        playBar_layout.layout.addLayout(my_button_layout( 30, name1 = u"Flop", name2 = u"Crop", name3 = u"Flip", name4 = u"Timer"))
        playBar_layout.layout.setContentsMargins(10, 0, 10, 2)

        layout.addWidget(playBar_layout)
        
        self.gridLayout = QGridLayout()
        self.gridLayout.addWidget(self.fill_label, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.sourceData_label, 0, 1, 1, 1)
        self.gridLayout.addWidget(self.convertForMaya_label, 0, 2, 1, 1)
        self.gridLayout.addWidget(self.framerate_label, 1, 0, 1, 1)
        self.gridLayout.addWidget(self.sourceFramerate_label, 1, 1, 1, 1)
        self.gridLayout.addWidget(self.resolution_label, 2, 0, 1, 1)
        self.gridLayout.addWidget(self.sourceResolution_label, 2, 1, 1, 1)
        self.gridLayout.addWidget(self.format_label, 3, 0, 1, 1)
        self.gridLayout.addWidget(self.sourceFormat_label, 3, 1, 1, 1)
        self.gridLayout.addWidget(self.startAt_label, 4, 0, 1, 1)
        self.gridLayout.addWidget(self.sourceStartAt_label, 4, 1, 1, 1)
        self.gridLayout.addWidget(self.framerate_comboBox, 1, 2, 1, 1)
        self.gridLayout.addWidget(self.resolution_comboBox, 2, 2, 1, 1)
        self.gridLayout.addWidget(self.format_comboBox, 3, 2, 1, 1)
        self.gridLayout.addWidget(self.startAt_comboBox, 4, 2, 1, 1)     
        
        layout.addLayout(self.gridLayout)
        layout.addWidget(cw.FilledWidget(4, "#111111", self))
        layout.addWidget(cw.FilledWidget(1, "#333333", self))

        confirm_layout = cw.FilledWidget(38, "#212121", self)
        confirm_layout.layout.setSpacing(4)
        confirm_layout.layout.addItem(QSpacerItem(10, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))
        confirm_layout.layout.addWidget(self.info_pushbutton)
        confirm_layout.layout.addWidget(self.reset_pushbutton)
        confirm_layout.layout.addWidget(self.volume_pushbutton)
        confirm_layout.layout.addWidget(self.volume_slider)
        confirm_layout.layout.addWidget(self.helpLine_lineEdit)
        confirm_layout.layout.addWidget(self.confirm_pushbutton)
        confirm_layout.layout.addItem(QSpacerItem(10, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))

        layout.addWidget(confirm_layout)
        
        self.setLayout(layout)    

        ### Shortcuts ###

        self.shortcut_list = []

        def mk_shortcut(shortcut, key_seq, task):
            shortcut = QShortcut(QKeySequence(key_seq), _getMainMayaWindow())
            shortcut.setContext(Qt.ApplicationShortcut)
            shortcut.activated.connect(task)
            self.shortcut_list.append(shortcut)
            return shortcut
        
        mk_shortcut("self.sh_range_start", Qt.Key_BracketLeft, self.range_start)
        mk_shortcut("self.sh_range_end", Qt.Key_BracketRight, self.range_end)
        mk_shortcut("self.sh_range_start", Qt.Key_I, self.range_start)
        mk_shortcut("self.sh_range_end", Qt.Key_O, self.range_end)
        mk_shortcut("self.sh_toggle_playback1", Qt.Key_L, self.toggle_playback)
        mk_shortcut("self.sh_toggle_playback2", Qt.Key_Space, self.toggle_playback)
        mk_shortcut("self.sh_toggle_playback3", Qt.AltModifier | Qt.Key_V, self.toggle_playback)
        mk_shortcut("self.sh_toggle_playback4", Qt.MetaModifier | Qt.Key_V, self.toggle_playback)
        mk_shortcut("self.sh_step_backwards", Qt.Key_Comma, self.step_backwards)
        mk_shortcut("self.sh_step_backwards2", Qt.Key_Left, self.step_backwards)
        mk_shortcut("self.sh_step_forwards", Qt.Key_Period, self.step_forwards)
        mk_shortcut("self.sh_step_forwards2", Qt.Key_Right, self.step_forwards)
        mk_shortcut("self.sh_set_framerate", Qt.ShiftModifier | Qt.Key_F, self.set_stacked_widget)
        mk_shortcut("self.sh_flop", Qt.ShiftModifier | Qt.Key_X, self.flop_vis)
        mk_shortcut("self.sh_flip", Qt.ShiftModifier | Qt.Key_Y, self.flip_vis)
        mk_shortcut("self.sh_crop", Qt.Key_C, self.crop_vis)
        mk_shortcut("self.timeline_marker", Qt.Key_M, self.timeliene_marker)
        mk_shortcut("self.next_marker", Qt.AltModifier | Qt.Key_Right, lambda: self.step_forwards(self.next_marker()))
        mk_shortcut("self.previous_marker", Qt.AltModifier | Qt.Key_Left, lambda: self.step_backwards(self.previous_marker()))

        ### Event handlers ###
        self.findChild(QPushButton, "Step_one_frame_backwards").clicked.connect(lambda: self.step_backwards(1))
        self.findChild(QPushButton, "Step_one_frame_forwards").clicked.connect(lambda: self.step_forwards(1))
        self.findChild(QPushButton, "Play_forwards").clicked.connect(self.toggle_playback)
        self.timer.timeout.connect(self.update_frame)
        self.slider.valueChanged.connect(self.set_frame)
        self.findChild(QPushButton, "Set_range_start").clicked.connect(self.range_start)
        self.findChild(QPushButton, "Set_range_end").clicked.connect(self.range_end)
        self.framerate_comboBox.currentIndexChanged.connect(self.set_custom_framerate)
        self.startAt_comboBox.currentIndexChanged.connect(self.set_custom_startAt)  
        self.slider.in_out_valueChanged.connect(self.FC_update)   
        self.slider.slider_active.connect(self.toggle_02)  
        self.findChild(QPushButton, "Crop").clicked.connect(self.crop_vis)
        self.findChild(QPushButton, "Flip").clicked.connect(self.flip_vis)
        self.findChild(QPushButton, "Flop").clicked.connect(self.flop_vis)
        self.findChild(QPushButton, "Timer").clicked.connect(self.set_stacked_widget)
        self.reset_pushbutton.clicked.connect(self.reset)
        self.confirm_pushbutton.clicked.connect(self.ffmpeg_command)
        self.video_label.sig_forwards.connect(self.step_forwards)
        self.video_label.sig_backwards.connect(self.step_backwards)
        self.video_label.slider_active.connect(self.toggle_02)
        self.info_pushbutton.clicked.connect(self.open_settings)
        self.frame_cache.cache_changed.connect(self.slider.update)
        self.slider.sliderStateChanged.connect(lambda inP, val, outP: self.cacheWorker.update_slider_info(inP, val, outP))
        self.volume_pushbutton.toggled.connect(self.volume_toggle)
        self.volume_slider.valueChanged.connect(self.set_volume)

        #self.audio_player.mediaStatusChanged.connect(lambda s: print("Media status:", s))
        #self.audio_player.error.connect(lambda e: print("Error:", self.audio_player.errorString()))
        
        # Track
        self.is_playing = False # Main playback tracker
        self.is_playing02 = False # Tracks interaction over the timeline (ie:pauses the video and lets the user scroll the timeline, then starts playback once the playhead is released)
        self.active = False
        self.start_time = 0
        self.end_time = 0
        self.crop = False
        self.flip = False
        self.flop = False
        self.metadata = None
        self.volume = 0
        self.timeline_markers=[]

    def printsilly(*args, **kwargs):
        print("Signal emitted!")
        print("Positional arguments:", args)
        print("Keyword arguments:", kwargs)

    def get_metadata(self, video_path):
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration:stream=width,height,codec_name,r_frame_rate,avg_frame_rate,nb_frames,codec_type,pix_fmt, color_space,color_transfer,color_primaries",
            "-of", "json",
            video_path
        ]
        
        ffmpeg_cmd = [
            "ffmpeg", "-y",                # Overwrite output if it exists
            "-i", video_path,              # Input video path
            "-map", "0:a?",                # Map the first audio stream if present
            "-vn",                         # Ignore video
            "-af", "aresample=async=1",    # Smooth out gaps / duplicate samples
            "-ac", "2",                    # Force stereo output
            "-ar", "48000",                # Set sample rate to 48 kHz
            "-c:a", "pcm_s16le",           # Encode as PCM 16-bit little endian
            "-fflags", "+genpts",          # Generate fresh timestamps to prevent offset
            self.temp_audio_path  
        ]

        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW  # Hides terminal popup on Windows
        else:
            startupinfo = None

        ffprobe_proc  = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
        stdout, stderr = ffprobe_proc.communicate()


        vid_stream = next((stream for stream in json.loads(stdout)['streams'] if stream['codec_type'] == 'video'), None)
        audio_stream = next((s for s in json.loads(stdout)["streams"] if s["codec_type"] == "audio"), None)
        self.has_audio = audio_stream is not None

        if self.has_audio: 
            self.ffmpeg_audio_proc = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo=startupinfo)
        else:
            self.ffmpeg_audio_proc = None

        if not vid_stream:
            print("Error: No video stream found.")
            return None
        
        num, den = map(int, vid_stream["r_frame_rate"].split('/'))
        framerate = num / den
        frame_duration = 1.0 / framerate
        
        self.metadata = {
            "Width": vid_stream.get("width"),
            "Height": vid_stream.get("height"),
            "Framerate": round(framerate, 2),
            "Framecount": vid_stream.get("nb_frames"),
            "Resolution": str(vid_stream.get("width")) + " x " + str(vid_stream.get("height")),
            "FrameDuration":frame_duration,
            #"Colourspace": vid_stream.get("pix_fmt"),  # Example: "yuv420p", "rgb24"
            #"Colourinfo": vid_stream.get("color_space") + vid_stream.get("color_transfer") + vid_stream.get("color_primaries")
        }
        #print (self.metadata["Colourspace"], self.metadata["Colourinfo"])
   
    def set_custom_framerate(self):
        if self.framerate_comboBox.currentText() == "custom":
            self.framerate_comboBox.setEditable(True)
            self.framerate_comboBox.clearEditText()
            self.framerate_comboBox.lineEdit().setStyleSheet(styleSheet.Light_style())
            self.framerate_comboBox.lineEdit().setValidator(QIntValidator(1, 2147483647))
        else: 
            self.framerate_comboBox.setEditable(False)
            self.validate()
    
    def set_custom_startAt(self):
        if self.startAt_comboBox.currentText() == "custom":
            self.startAt_comboBox.setEditable(True)
            self.startAt_comboBox.clearEditText()
            self.startAt_comboBox.lineEdit().setStyleSheet(styleSheet.Dark_style())
            self.startAt_comboBox.lineEdit().setValidator(QIntValidator(-2147483647, 2147483647))
        else: 
            self.startAt_comboBox.setEditable(False)
            self.validate()
    
    def reset(self):
        self.slider.variables["_outPoint"] = self.slider.maximum()
        self.slider.variables["_inPoint"] = self.slider.minimum()
        self.slider.variables["_frame"] = self.slider.minimum()
        
        self.crop = False
        self.video_label.set_crop_to_image(self.metadata.get("Width"), self.metadata.get("Height"))
        self.flip = False
        self.flop = False
        fps = self.metadata.get("Framerate")
        self.set_speed(fps)
        self.set_frame(self.slider.variables.get("_frame"))
        self.timeline_markers.clear()
        self.frame_cache._data.clear()
        self.cacheWorker.update_slider_info(self.slider.minimum(), self.slider.minimum(), self.slider.maximum())

        self.framerate_comboBox.setCurrentIndex(0)
        self.resolution_comboBox.setCurrentIndex(1)
        self.format_comboBox.setCurrentIndex(0)
        self.startAt_comboBox.setCurrentIndex(0)

        if self.is_playing:
            self.toggle_playback()

        self.update()
        self.slider.update()

    def load_image(self):
        self.close()
        try:
            names = self.file_name_list[0].rsplit(".", 1)
            cameraDialog(names[0], self.input_path, names[1])
        except:
            cameraDialog(self.file_name_list[0], self.input_path, None)

    def load_video(self):
        """Sets video settings"""
        self.get_metadata(self.input_path)
        self.cap = self.cv2.VideoCapture(self.input_path)
        self.slider.setMaximum(int(self.cap.get(self.cv2.CAP_PROP_FRAME_COUNT)))
        self.slider.variables["_outPoint"] = self.slider.maximum()
        self.slider.setEnabled(True)
        self.show_frame()
        self.end_time = int(self.cap.get(self.cv2.CAP_PROP_FRAME_COUNT))
        self.frameCount_label.setText(str(self.metadata.get("Framecount")) + " frames")
        self.FC_update()
        fps = self.metadata.get("Framerate")
        self.set_speed(fps)
        self.video_label.set_crop_to_image(self.metadata.get("Width"), self.metadata.get("Height"))
        self.sourceFramerate_label.setText(str(fps) + " fps")
        self.sourceResolution_label.setText(self.metadata.get("Resolution"))
        self.sourceFormat_label.setText(self.file_name_list[1])

        framerate_list = [
            "Scene frame rate ( " + str(sceneFrameRate) + " fps)",
            "Source frame rate( " + str(self.metadata.get("Framerate", "Unknown")) + " )",
            "custom"
        ]
        self.framerate_comboBox.addItems(framerate_list)
        resolution_list = [
            "small ( 480p )",
            "medium ( 720p )",
            "large ( 1080p )",
            "use source( " + self.metadata.get("Resolution") + " )"
            ]
        self.resolution_comboBox.addItems(resolution_list)
        self.resolution_comboBox.setCurrentIndex(3)
        self.format_comboBox.addItems(["JPEG", "PNG"])
        startAt_list = [
            "Animation start time ( " + str(animationStartTime) + " )",
            "Playback start time ( " + str(playbackStartTime) + " )",
            "custom"
            #,"fit audio to scene"            
        ]
        self.startAt_comboBox.addItems(startAt_list)

        self.initShortcuts() 
        self.load_audio(self.temp_audio_path)
        self.setCacheSettings()
        self.cacheWorker = CacheWorker(self.input_path, self.frame_cache, self.slider.minimum(), self.slider.maximum())
        self.cacheThread.start()
        self.toggleCache()

    def load_audio( self, audio_path):
        if not getattr(self, "has_audio", False):
            return
        if self.ffmpeg_audio_proc:
            self.ffmpeg_audio_proc.wait()

        self.audio_player.setMedia(QMediaContent(QUrl.fromLocalFile(audio_path)))
        self.set_volume()
        #prime the buffer
        self.audio_player.setPosition(0) #Still a bit of delay on first play

    def volume_toggle(self, muted):
        if muted == True: 
            self.volume = self.volume_slider.value() or 60
            self.audio_player.setMuted(True)
            self.volume_slider.blockSignals(True)
            self.volume_slider.setValue(0)
            self.volume_slider.blockSignals(False)
        else: 
            self.audio_player.setMuted(False)
            self.volume_slider.setValue(self.volume if self.volume > 0 else 60)
        self.volume_pushbutton.repaint()


    def set_volume(self, value=0):
        if value > 0:
            self.audio_player.setMuted(False)
            self.volume_pushbutton.blockSignals(True)
            self.volume_pushbutton.setChecked(False)
            self.volume_pushbutton.blockSignals(False)
            self.last_volume = value
        if value == 0:
            self.volume_pushbutton.setChecked(True)
        self.audio_player.setVolume(value)
        self.volume_pushbutton.repaint()

    def set_speed(self, fps):
        self.playbackSpeed_label.setText(str(fps) + " fps")
        self.setFPS_Label.setText(f"FPS [{str(float(fps))}]:")
        self.speed = fps

    def load_scale(self, pixmap):

        scale_factor = min(self.video_label.width() / pixmap.width(), self.video_label.height() / pixmap.height())
        w = pixmap.width() * scale_factor
        h = pixmap.height() * scale_factor

        scaled_pixmap = pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.FastTransformation)

        transform = QTransform()
        if self.flip:
            transform.scale(1, -1)
        if self.flop:
            transform.scale(-1, 1)

        scaled_pixmap = scaled_pixmap.transformed(transform, Qt.FastTransformation)
        #scaled_pixmap = QPixmap.fromImage(image)

        self.video_label.setPixmap(scaled_pixmap)

    def get_frame(self, frame_idx):
        if frame_idx in self.frame_cache:
            return self.frame_cache[frame_idx]

        # Seek only if needed:
        self.cap.set(self.cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = self.cap.read()
        if ret:
            rgb = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2RGB)
            if (self.cacheConfig_file.exists() and self.readCacheSettings().get("status") == True) or not self.cacheConfig_file.exists():                
                self.frame_cache[frame_idx] = rgb
                #self.cacheWorker._enforce_cache_size()
            return rgb

        return None
    
    def show_frame(self):
        if self.input_type == 0:
            self.load_scale(QPixmap(self.input_path))
            return
        
        if self.is_playing:
            expected_frame = self.slider.variables.get("_frame")
            if expected_frame < self.slider.variables["_outPoint"] - 1:

                # Try cache first:
                if expected_frame in self.frame_cache:
                    rgb = self.frame_cache[expected_frame]
                    self.schedule_next_tick()

                else:
                    # No cache? Just read sequentially.
                    ret, frame = self.cap.read()
                    if ret:
                        frame_idx = int(self.cap.get(self.cv2.CAP_PROP_POS_FRAMES)) - 1
                        if frame_idx < self.slider.variables["_outPoint"]:
                            rgb = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2RGB)
                            self.schedule_next_tick()
                        else:
                            self.toggle_playback()
                            return
                        
                        if (self.cacheConfig_file.exists() and self.readCacheSettings().get("status") == True) or not self.cacheConfig_file.exists(): 
                            self.frame_cache[frame_idx] = rgb
                            #self.cacheWorker._enforce_cache_size()

                    else:
                        self.toggle_playback()
                        return
            else:
                self.toggle_playback()
                return

        else:
            # Not playing → must seek accurately
            frame_idx = self.slider.variables.get("_frame")
            rgb = self.get_frame(frame_idx)
            if rgb is None:
                return
            
        # Render
        height, width, channel = rgb.shape
        bytes_per_line = 3 * width
        q_img = QImage(rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
        self.load_scale(QPixmap.fromImage(q_img))

    def update_frame(self):
        """Updates the video frame on timer event."""
        self.show_frame()
        self.slider.variables["_frame"] += 1
        self.slider.emit_sliderStateChanged()
        self.slider.update()

    def set_frame(self, position):
        """Sets the video to a specific frame based on slider."""
        self.cap.set(self.cv2.CAP_PROP_POS_FRAMES, position)
        self.show_frame()
        self.update()

    def set_stacked_widget(self):
        if self.stacked_layout.currentWidget() == self.slider_layout:
            self.stacked_layout.setCurrentWidget(self.setfps_layout)
            self.findChild(QPushButton, "Timer").setEnabled(False)
            self.setFPS_lineEdit.clear()
            self.setFPS_lineEdit.setFocus()
        elif self.stacked_layout.currentWidget() == self.setfps_layout:
            if self.setFPS_lineEdit.hasAcceptableInput():
                fps = float(self.setFPS_lineEdit.text())
                self.set_speed(fps)
            self.editing_finished()

    def editing_finished(self):
        self.stacked_layout.setCurrentWidget(self.slider_layout)
        self.findChild(QPushButton, "Timer").setEnabled(True)
        self.update()

    def FC_update(self):
        self.FC_label.setText(str(self.slider.variables.get("_outPoint") - self.slider.variables.get("_inPoint")))
        self.slider.emit_sliderStateChanged()
    
    def step_backwards(self, delta=1):
        if self.slider.variables["_frame"] > self.slider.minimum():
            self.slider.setValue(max(self.slider.minimum(), self.slider.variables.get("_frame") - delta))
            
    def step_forwards(self, delta=1):
        if self.slider.variables["_frame"] < self.slider.maximum():
            self.slider.setValue(min(self.slider.variables.get("_frame") + delta, self.slider.maximum()))
            
    def next_marker(self):
        playhead = self.slider.variables.get("_frame")
        markers = sorted(self.timeline_markers)
        for m in markers:
            if m > playhead:
                return abs(m - playhead)
        return 0

    def previous_marker(self):
        playhead = self.slider.variables.get("_frame")
        markers = sorted(self.timeline_markers)
        for m in reversed(markers):
            if m < playhead:
                return abs(m - playhead)
        return 0

    def toggle_playback(self):
        """Play/Pause the video."""
        if self.is_playing: #Stop
            self.audio_player.pause()
            self.slider.valueChanged.connect(self.set_frame)
            self.update()
            
        else: #Play
            if self.slider.variables["_frame"] >= self.slider.variables["_outPoint"] or self.slider.variables["_frame"] < self.slider.variables["_inPoint"]:
                self.slider.setValue(self.slider.variables.get("_inPoint"))
            self.slider.valueChanged.disconnect(self.set_frame)
            self.start_timer()
            self.update()
        self.is_playing = not self.is_playing
        self.is_playing02 = not self.is_playing02

    # The is_playing02 tracker tracks the focus scroll/user interaction.
    def toggle_02(self, is_active):
        if self.is_playing02 and is_active:
            self.cacheWorker.precache_timer.stop()
            self.audio_player.pause()
            self.slider.valueChanged.connect(self.set_frame)
            self.is_playing = False
        elif self.is_playing02 and not is_active:
            if self.slider.variables["_frame"] >= self.slider.variables["_outPoint"] - 1 or self.slider.variables["_frame"] < self.slider.variables["_inPoint"]:
                self.is_playing = False
                self.is_playing02 = False
                return

            self.slider.valueChanged.disconnect(self.set_frame)
            self.cacheWorker.precache_timer.start()
            self.start_timer()
            self.is_playing = True
        elif not self.is_playing02:
            self.active = is_active
            if is_active:
                self.cacheWorker.precache_timer.stop()
            else:
                self.cacheWorker.precache_timer.start()
            return
        
    def start_timer(self):
        time_sec = self.slider.variables["_frame"] * self.metadata["FrameDuration"]
        #time_sec = self.slider.variables["_frame"] / self.metadata.get("Framerate")
        self.audio_player.setPosition(int(time_sec * 1000))
        self.audio_player.setPlaybackRate(self.speed/self.metadata.get("Framerate"))
        self.start_time = time.perf_counter() - ((int(self.slider.variables.get("_frame")) * 1000/self.speed)/1000)
        self.schedule_next_tick()
        self.audio_player.play()
        
    def schedule_next_tick(self):
        """Compute interval to next tick based on perf_counter."""
        expected_time = ((int(self.slider.variables.get("_frame")) + 1) * 1000/self.speed)
        elapsed = (time.perf_counter() - self.start_time) * 1000
        sleep_time = expected_time - elapsed
        interval_ms = max(0, int(sleep_time))
        self.timer.start(interval_ms)

    def range_start(self):
        if self.slider.variables["_frame"] != self.slider.maximum():
            self.slider.variables["_inPoint"] = self.slider.variables.get("_frame")
            if self.slider.variables["_inPoint"] >= self.slider.variables["_outPoint"]:
                self.slider.variables["_outPoint"] = self.slider.variables.get("_inPoint") + 1
            self.frameCount_label.setText(str(self.slider.maximum() - self.slider.minimum()) + " frames")
            self.FC_update()
            self.slider.repaint()

    def range_end(self):
        if self.slider.variables["_frame"] != self.slider.minimum():
            self.slider.variables["_outPoint"] = self.slider.variables.get("_frame")
            if self.slider.variables["_outPoint"] <= self.slider.variables["_inPoint"]:
                self.slider.variables["_inPoint"] = self.slider.variables.get("_outPoint") - 1
            self.frameCount_label.setText(str(self.slider.maximum() - self.slider.minimum()) + " frames")
            self.FC_update()
            self.slider.repaint()

    def crop_vis(self):
        self.crop = not self.crop
        self.update()
    
    def flip_vis(self):
        self.flip = not self.flip
        self.video_label.crop_flip()
        self.set_frame(self.slider.variables.get("_frame"))
        
    def flop_vis(self):
        self.flop = not self.flop
        self.video_label.crop_flop()
        self.set_frame(self.slider.variables.get("_frame"))

    def timeliene_marker(self):
        frame = self.slider.variables.get("_frame")
        if frame in self.timeline_markers:
            self.timeline_markers.remove(frame)
            self.slider.repaint()
            return
        else:
            self.timeline_markers.append(frame)
            self.timeline_markers.sort()
            self.slider.repaint()
            return
         
    def path_config(self):
        ref_file = QFileDialog.getExistingDirectory(self, "Pick where you want to save your references", script_directory, QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        if ref_file:
            config_file = Path(f"{script_directory}/pathconfig.txt")
            with open (config_file, "w") as f:
                f.write(ref_file)
            self.set_my_ref_folder(config_file)
            if self.settings_win:
                self.settings_win.path_lineEdit.setText(ref_file)
            return True
        else:
            return False

    def set_my_ref_folder(self, config_file):
        with open (config_file)as f:
            self.my_ref_folder = f"{f.read()}/{self.file_nice_name}"
        
    def validate_my_ref_folder(self):
        config_file = Path(f"{script_directory}/pathconfig.txt")
        try: 
            self.set_my_ref_folder(config_file)
        
            if config_file.exists() and config_file.stat().st_size > 0:
                with config_file.open("r") as f:
                    path = f.readline().strip()
                    target_path = Path(path)
                    if target_path.exists():
                        return True
                    else:
                        return self.path_config()
            else: 
                return False
        except:
            return self.path_config()
        
    def open_settings(self):
        if hasattr(self, "settings_win") and self.settings_win is not None:
            self.settings_win.close()

        self.settings_win = sett.SettingsWindow(parent=self)
        self.settings_win.editButton.clicked.connect(self.path_config)

        outputPath = ""
        if not self.pathConfig_file.exists():
            outputPath = ""
        
        if self.pathConfig_file.exists():
            with open(self.pathConfig_file, "r") as f:
                outputPath = f.read().strip()

        if not self.cacheConfig_file.exists():
            with open(self.cacheConfig_file, "w") as f:
                f.write("True\n800\n750\n50\n")

        if self.cacheConfig_file.exists():
            try:
                cache_settings = self.readCacheSettings()
            except:
                with open(self.cacheConfig_file, "w") as f:
                    f.write("True\n800\n750\n50\n")
        
        if not self.plateConfig_file.exists():
            with open(self.plateConfig_file, "w") as f:
                f.write("0")
        
        if self.plateConfig_file.exists():
            with open(self.plateConfig_file, "r") as f:
                plateConfig = f.read().strip()

        for line_edit in self.settings_win.caching_widget.findChildren(QLineEdit):
            line_edit.textChanged.connect(self.onLineEditChanged)
        #Slots for the settings window
        self.settings_win.cachingCheckbox.clicked.connect(self.onLineEditChanged)
        self.settings_win.cacheReset.clicked.connect(self.onLineEditChanged)
        self.settings_win.radioButton_layout.imagePlane_rb.toggled.connect(lambda: self.onRadioButtonClicked(value=0))
        self.settings_win.radioButton_layout.floatingImagePlane_rb.toggled.connect(lambda: self.onRadioButtonClicked(value=1))
        self.settings_win.radioButton_layout.sean_rb.toggled.connect(lambda: self.onRadioButtonClicked(value=2))

        try:
            self.settings_win.populateSettings(outputPath, cache_settings["status"], str(cache_settings["size"]), str(cache_settings["lookAhead"]), str(cache_settings["lookBehind"]), int(plateConfig))
            self.settings_win.show()
        except:
            for cfg_file in (self.plateConfig_file, self.cacheConfig_file):
                try:
                    if os.path.exists(cfg_file):
                        os.remove(cfg_file)
                        print(f"Deleted corrupted config: {cfg_file}")
                except Exception as del_err:
                    print(f"Could not delete {cfg_file}: {del_err}")

            self.open_settings()
            

    def writeCache(self):
        cacheStatus = self.settings_win.cachingCheckbox.isChecked()
        cacheSize = self.settings_win.cacheSize.line_edit.text()
        lookAhead = self.settings_win.lookAhead.line_edit.text()
        lookBehind = self.settings_win.lookBehind.line_edit.text()
        with open(self.cacheConfig_file, "w") as f:
                f.write(f"{cacheStatus}\n{cacheSize}\n{lookAhead}\n{lookBehind}\n")

    def setCacheSettings(self):
        if self.cacheConfig_file.exists():
            cache_settings = self.readCacheSettings()

            if cache_settings["status"]:
                self.frame_cache.configure(
                    cache_settings["size"],
                    cache_settings["lookAhead"],
                    cache_settings["lookBehind"],
                    mini_margin=35
                )
            else:
                self.frame_cache.configure(0, 0, 0, 0)
        else:
            self.frame_cache.configure(
                cache_size=800,
                look_ahead=750,
                look_behind=50,
                mini_margin=35
            )

        return self.frame_cache
    
    def readCacheSettings(self):
        #import traceback
        #print("readCacheSettings called")
        #traceback.print_stack(limit=5)
        if self.cacheConfig_file.exists():
            try:
                with open(self.cacheConfig_file, "r") as f:
                        lines = [line.strip() for line in f.readlines()]
                return {
                    "status": lines[0].lower() == "true",
                    "size": int(lines[1]),
                    "lookAhead": int(lines[2]),
                    "lookBehind": int(lines[3])
                }
            except:
                return {
                    "status": True,
                    "size": 800,
                    "lookAhead": 750,
                    "lookBehind": 50
                }

    def toggleCache(self):
        self.frame_cache._data.clear()

        try:
            self.cacheWorker.precache_timer.timeout.disconnect(self.cacheWorker.precache)
        except (TypeError, RuntimeError):
            pass  # no existing connection

        if self.cacheConfig_file.exists() and not self.readCacheSettings().get("status"):
            self.cacheWorker.precache_timer.stop()
        else:
            self.cacheWorker.precache_timer.timeout.connect(self.cacheWorker.precache)
            self.cacheWorker.precache_timer.start()

    
    def onRadioButtonClicked(self, value=0):
        value = str(value)
        with open(self.plateConfig_file, "w") as f:
            f.write(value)

    def onLineEditChanged(self):
        self.writeCache()
        self.setCacheSettings()
        self.toggleCache()
        self.slider.update()
                
    def resizeEvent(self, event):
        if self.cap:
            self.set_frame(self.slider.variables.get("_frame"))
        if self.input_type == 0:
            self.show_frame()
        super().resizeEvent(event) 

    def mousePressEvent(self, event):
        if QApplication.focusWidget():  # Check if any widget has focus
            QApplication.focusWidget().clearFocus()  # Explicitly remove focus
        super().mousePressEvent(event)

    def efont(self, size):
         font = QFont()
         font.setPointSize(size)
         return font       
    
    def ecol(self, brt):
        colour = (
            int(169 * brt),
            int(169 * brt),
            int(169 * brt)
        )
        return f"({colour[0]}, {colour[1]}, {colour[2]})"

    def numeric(self, txt):
        for i in txt:
            if (i.isnumeric() == False) and (i != ".") :
                txt = txt.replace(i, "")
        return(int(float(txt)))
    
    def validate(self):
        self.framerate_comboBox.clearFocus()
        self.startAt_comboBox.clearFocus()
        if int(self.framerate_comboBox.currentIndex()) != 2 and int(self.startAt_comboBox.currentIndex()) != 2:
            self.helpLine_lineEdit.clear()
            return True
        else: 
            self.helpLine_lineEdit.setText("🔴 Not Acceptable sorry") #this unicode is not red in linux >:/
            return False

    def ffmpeg_build_command(self):
        input_fps = self.metadata.get("Framerate")
        height = self.metadata.get("Height")
        start_time = self.slider.variables.get("_inPoint") / input_fps
        duration = (self.slider.variables.get("_outPoint") - self.slider.variables.get("_inPoint"))/ input_fps
        vf_list = []

        if self.flip:
            vf_list.append('vflip')
        
        if self.flop:
            vf_list.append('hflip')
        
        if self.crop:
            crop = self.video_label.ffmpeg_crop()
            height = abs(self.video_label.crop_points["bottomLeft"].y() - self.video_label.crop_points["topLeft"].y())
            vf_list.append(crop)

        if self.resolution_comboBox.currentIndex() <= 3:
            vf_list.append(f"scale=-2:'min({self.numeric(self.resolution_comboBox.currentText())}, {height})'")

        exportfps = 'fps=' + str(input_fps / self.speed * self.numeric(self.framerate_comboBox.currentText()))
        vf_list.append(exportfps)

        file_path = f"{Path(self.my_ref_folder)}/{self.file_nice_name}.%04d." + self.format_comboBox.currentText().casefold()
        start_number = f"{self.numeric(self.startAt_comboBox.currentText())}"
        #print ("the ffmeg go here " + file_path)
        
        
        FFmpegCommands = [
            "ffmpeg",

            "-ss",
            str(start_time), 
            
            "-i", 
            self.input_path,

            "-t",
            str(duration), 

            "-vf",
            f"{', '.join(vf_list)}",

            "-start_number", 
            start_number,

            "-q:v","0",

            file_path,
        ]

        return FFmpegCommands, file_path, start_number
    
    def copy_to_folder(self, folder_path):
        dst_file = folder_path / ntpath.basename(self.input_path)
        if not dst_file.exists():
            shutil.copy2(self.input_path, dst_file)

    def delete_old(self, folder_path):
        image_extensions = [".jpeg", ".png"]
        for file in folder_path.iterdir():
            if file.suffix.lower() in image_extensions and file.is_file():
                file.unlink()
    
    def ffmpeg_command(self):
        if self.validate() and self.validate_my_ref_folder():
            
            cameraDialog(self.file_nice_name, self.ffmpeg_build_command()[1], self.ffmpeg_build_command()[2])

            folder_path = Path(self.my_ref_folder)
            folder_path.mkdir(parents=True, exist_ok=True)

            self.copy_to_folder(folder_path)
            self.delete_old(folder_path)

            ffmpeg_thread = threading.Thread(target=self.run_ffmpeg)
            ffmpeg_thread.start()
            self.close()

        else:
            self.validate()

    def run_ffmpeg(self):
        
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW  # Hides terminal popup on Windows
        else: 
            startupinfo = None

        with open(f"{self.my_ref_folder}/ffmpeg_log.txt", "w") as log:
            subprocess.run(self.ffmpeg_build_command()[0], stdout=log, stderr=log, startupinfo=startupinfo)

    #using this because having the context set to Qt.WindowShortcut doesn't know how to overwrite maya's default shortcuts.
    def eventFilter(self, obj, event):
        if event.type() == QEvent.WindowActivate:
            self.initShortcuts()
        elif event.type() == QEvent.WindowDeactivate:
            self.exitShortcuts()
        return QWidget.eventFilter(self, obj, event)
        #return super(ReferenceEditor, self).eventFilter(obj, event)

    def initShortcuts(self):
        for shortcut in self.shortcut_list:
            shortcut.setEnabled(1)
    
    def exitShortcuts(self):
        for shortcut in self.shortcut_list:
            shortcut.setEnabled(0)

    def closeEvent(self, event):
        self.exitShortcuts()
        if hasattr(self, "cacheWorker"):
            try:
                self.cacheWorker.precache_timer.timeout.disconnect()
                self.cacheWorker.precache_timer.stop()
                self.cacheWorker.stop()
                self.cacheWorker.deleteLater()
                self.cacheWorker.cap_cache.release()
                del self.cacheWorker.cap_cache
            except:
                pass
        if hasattr(self, "cacheThread"):
            try:
                self.cacheThread.quit()
                self.cacheThread.wait()
                self.cacheThread.deleteLater()
            except:
                pass
        if hasattr(self, "cap"):
            try:
                if hasattr(self, "frame_cache"):
                    self.frame_cache._data.clear()
                    del self.frame_cache
                self.cap.release()
                del self.cap
            except:
                pass

        if hasattr(self, "settings_win") and self.settings_win is not None:
            self.settings_win.close()

        if self.audio_player is not None:
            self.audio_player.stop()
            self.audio_player.setMedia(QMediaContent())
            self.audio_player.deleteLater()
            del self.audio_player

        # Remove temp wav
        if self.temp_audio_path and os.path.exists(self.temp_audio_path):
            try:
                os.remove(self.temp_audio_path)
            except Exception as e:
                print("Failed to remove temp audio:", e)

        self.deleteLater()
        gc.collect()
        event.accept()

class CacheWorker(QObject):

    #@slot for the playhead position
    def __init__(self, input_path=None, cacheDict=None, start=0, end=2):
        super().__init__()

        if cacheDict is None:
            cacheDict = cw.CacheDict()

        self.cv2 = import_scoped_cv2()
        self.cap_cache = self.cv2.VideoCapture(input_path)
        self.cache = cacheDict

        self._start = start
        self._inPoint = start
        self._playhead = start
        self._outPoint = end
        self._end = end

        self.precache_timer = QTimer()
        self.precache_timer.setInterval(5)  # 0 => Idle-like

    @Slot(int, int, int)
    def update_slider_info(self, inP, val, outP):
        self._inPoint = inP
        self._playhead = val
        self._outPoint = outP

    def print_check(self):
        print(self._inPoint, self._playhead, self._outPoint)

    def stop(self):
        self.running = False
    
    def _enforce_cache_size(self):
        if self._inPoint <= self._playhead < self._outPoint:
            window_start = self._playhead - self.cache.look_behind
            window_end = self._playhead + self.cache.look_ahead #min(self._playhead + self.cache.look_ahead, self.cache.look_behind + self.cache.cache_size)
        else:
            window_start = self._playhead - self.cache.mini_margin
            window_end = self._playhead + self.cache.mini_margin


        while len(self.cache._data) > self.cache.cache_size:
            candidates = [k for k in self.cache if k < window_start or k > window_end]
            if candidates:
                furthest = max(candidates, key=lambda k: abs(k - self._playhead))
            else:
                furthest = max(self.cache, key=lambda k: abs(k - self._playhead))
            self.cache.evict(furthest)

    def precache(self):

        if self._inPoint <= self._playhead < self._outPoint:
        # while there are cache frames available to inside the range, prioritise this over the already cached frames outside the range
            for i in range(self._playhead - self.cache.look_behind, self._playhead + self.cache.look_ahead):
                if i < self._inPoint or i >= self._outPoint:
                    continue
                if i not in self.cache:
                    current_pos = int(self.cap_cache.get(self.cv2.CAP_PROP_POS_FRAMES))
                    if current_pos != i:
                        self.cap_cache.set(self.cv2.CAP_PROP_POS_FRAMES, i)
                    ret, frame = self.cap_cache.read()
                    if ret:
                        rgb = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2RGB)
                        self.cache[i] = rgb
                        self._enforce_cache_size()
                    break  # Do only one at a time
                

        if  self._playhead < self._inPoint or self._playhead > self._outPoint:
            for i in range(self._playhead - self.cache.mini_margin, self._playhead + self.cache.mini_margin):
                if i < 0 or i > self._end:
                    continue
                if i not in self.cache:
                    current_pos = int(self.cap_cache.get(self.cv2.CAP_PROP_POS_FRAMES))
                    if current_pos != i:
                        self.cap_cache.set(self.cv2.CAP_PROP_POS_FRAMES, i)
                    ret, frame = self.cap_cache.read()
                    if ret:
                        rgb = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2RGB)
                        self.cache[i] = rgb
                        self._enforce_cache_size()
                    break  # Do only one at a time

    QThread.msleep(1)

def cameraDialog(name, file_path, start_number):
    if cmds.window("CameraDialog", exists=True):
        cmds.deleteUI("CameraDialog")
        cmds.windowPref("CameraDialog", removeAll=True)

    cams = cmds.listCameras()

    cmds.window("CameraDialog", maximizeButton = False, minimizeButton = False)
    cmds.columnLayout(adjustableColumn = True, w=100)
    #, margins=9, generalSpacing=9
    cmds.columnLayout(adjustableColumn = True, w=100)
    #, generalSpacing=4
    cmds.text("Pick a camera:", align="left")
    cmds.optionMenu("cameraChoices")
    for cam in cams:
        cmds.menuItem(label = cam)

    cmds.setParent('..')
    cmds.rowLayout( numberOfColumns=2, columnWidth=(50, 50))
    #, adjustableColumn=(1, 2), generalSpacing = 9
    cmds.button("cancel", height=24, command=lambda x:cmds.deleteUI("CameraDialog"))
    cmds.button("confirm", command=lambda x:nameDialog(name, file_path, start_number), height=24)

    cmds.showWindow()

def nameDialog(name, file_path, start_number):

    choiceCam = cmds.optionMenu("cameraChoices", q=True, value=True)
    cmds.deleteUI("CameraDialog")

    result = cmds.promptDialog(
        title = "Name Dialog",
        message = "Please name your image plane:",
        text = name,
        button = ["cancel", "confirm"],
        defaultButton = "confirm",
        cancelButton = "cancel",
        dismissString = "cancel",
    )
    if result == "confirm":
        im_name = cmds.promptDialog(query=True, text=True)
        #if cmds.imggePlane(query=True, name=True)
        if im_name == '':
            im_name = 'noNameImagePlane' 

        plateConfig_file = Path(f"{script_directory}/plateconfig.txt")
        if plateConfig_file.exists():
            with open(plateConfig_file, "r") as f:
                plateConfig = int(f.read().strip())
            if plateConfig == 1:
                createFreeImagePlane(choiceCam, im_name, file_path, start_number)

            elif plateConfig == 2:
                createImgaePlane(choiceCam, im_name, file_path, start_number, sean=True)

            else:
                createImgaePlane(choiceCam, im_name, file_path, start_number)
        else:
                createImgaePlane(choiceCam, im_name, file_path, start_number)
               
def createImgaePlane(choiceCam, im_name, file_path, start_number, sean=False):
    im_name = im_name + "_plate"
    start_number = str(start_number).zfill(4)
    file_path = file_path.replace("%04d", start_number)

    try:
        createdImagePlane = cmds.imagePlane( camera=choiceCam, fileName=file_path, name=im_name, showInAllViews=False, lookThrough=choiceCam)
    except:
        createdImagePlane = cmds.imagePlane( camera=choiceCam, fileName=file_path, name=im_name + "#", showInAllViews=False, lookThrough=choiceCam)

    cmds.setAttr(createdImagePlane[0]+".useFrameExtension", 1)
    cmds.setAttr(createdImagePlane[0]+".displayOnlyIfCurrent", 1)
    cmds.setAttr(createdImagePlane[0]+".fit", 2)
    cmds.setAttr(createdImagePlane[0]+".frameOffset", 0)
    #remove the colourspace attr for non etc, as it relys on the occio.config and lut from in the config
    #or do the colour config properly but icbb
    #cmds.setAttr(createdImagePlane[0]+".colorSpace", "Output - sRGB", type="string")
    #cmds.setAttr(createdImagePlane[0]+".ignoreColorSpaceFileRules", 1)

    #Extending Frame Cache to be long enough! Add an extra 100 frames for just in case!
    shot_length = cmds.playbackOptions(q=1, aet=1) - cmds.playbackOptions(q=1, ast=1)
    cmds.setAttr(createdImagePlane[0]+".frameCache", int(shot_length)+100)

    if sean:
        frame_extension_attribute = f"{createdImagePlane[1]}.frameExtension"
        for source_attribute in (
            cmds.listConnections(
                frame_extension_attribute,
                destination=True,
                plugs=True,
            )
            or ()
        ):
            cmds.disconnectAttr(
                source_attribute,
                frame_extension_attribute,
            )

        shot_length = cmds.playbackOptions(q=1, aet=1) - cmds.playbackOptions(q=1, ast=1)
        cmds.setKeyframe(f"{createdImagePlane[1]}", attribute="frameExtension", time=start_number, value=float(start_number))
        cmds.setKeyframe(f"{createdImagePlane[1]}", attribute="frameExtension", time=(int(start_number) + int(shot_length)), value=(int(start_number) + int(shot_length)))            
        cmds.keyTangent(f"{createdImagePlane[1]}.frameExtension", inTangentType="spline", outTangentType="spline")
        cmds.setInfinity(f"{createdImagePlane[1]}.frameExtension", postInfinite="linear")

    cmds.rename(createdImagePlane[0], im_name)
    try:		
        cmds.select(im_name) 
    except:
        pass
    

# Courtsey of Kev
def createFreeImagePlane(choiceCam, im_name, file_path, start_number):
    im_name = im_name + "_plate"
    start_number = str(start_number).zfill(4)
    file_path = file_path.replace("%04d", start_number)
    # free image plane
    try:
        createdImagePlane = cmds.imagePlane( fileName=file_path, name=im_name )
    except:
        createdImagePlane = cmds.imagePlane( fileName=file_path, name=im_name + "#" )
    # group
    ipGRP = choiceCam + "_ipGRP" 

    if not cmds.objExists(ipGRP):

        cmds.group( empty=True, name= ipGRP)

        try:
                    cmds.parentConstraint(
                        choiceCam,
                        ipGRP,
                        maintainOffset=False,
                        name="refPlane_parentConstraint"
                    )
        except Exception as e:
            om.MGlobal.displayWarning(f"Failed to constrain {ipGRP} to {choiceCam}: {e}")

    mel.eval('catchQuiet(`parent "%s" "%s"`);' % (createdImagePlane[1], ipGRP))
    # Attrs
    cmds.setAttr(f"{createdImagePlane[0]}.useFrameExtension", 1)
    cmds.setAttr(f"{createdImagePlane[0]}.translateX", 0)
    cmds.setAttr(f"{createdImagePlane[0]}.translateY", 0)
    cmds.setAttr(f"{createdImagePlane[0]}.translateZ", -25)
    cmds.setAttr(f"{createdImagePlane[0]}.rotateX", 0)
    cmds.setAttr(f"{createdImagePlane[0]}.rotateY", 0)
    cmds.setAttr(f"{createdImagePlane[0]}.rotateZ", 0)
    cmds.setAttr(f"{createdImagePlane[1]}.frameOffset", 0)
    cmds.addAttr(f"{createdImagePlane[0]}", longName="retime_curve", attributeType="double", defaultValue=0, keyable=True)
    shot_length = cmds.playbackOptions(q=1, aet=1) - cmds.playbackOptions(q=1, ast=1)
    cmds.setKeyframe(f"{createdImagePlane[0]}", attribute="retime_curve", time=start_number, value=float(start_number))
    cmds.setKeyframe(f"{createdImagePlane[0]}", attribute="retime_curve", time=(int(start_number) + int(shot_length)), value=(int(start_number) + int(shot_length)))
    cmds.connectAttr(f"{createdImagePlane[0]}.retime_curve", f"{createdImagePlane[1]}.frameExtension", force=True)
    cmds.keyTangent(f"{createdImagePlane[0]}.retime_curve", inTangentType="spline", outTangentType="spline")
    cmds.setInfinity(f"{createdImagePlane[0]}.retime_curve", postInfinite="linear")
    cmds.setAttr(createdImagePlane[0]+".frameCache", int(shot_length)+100)
    cmds.rename(createdImagePlane[0], im_name)
    try:		
        cmds.select(im_name) 
    except:
        pass

def run(file, media_type):
    global window
    try:
        window.close()  # Close previous window if it exists
    except:
        pass

    window = ReferenceEditor(file)
    window.resize(800, 700)
    window.setWindowTitle("Reference Manager")
    if media_type == 0:
        window.load_image()
    if media_type == 1:
        window.load_video()
        window.show()
    
def flush_cv2():
    target_base = f"{script_directory}/cv2Bundle/cv2"

    # 1. Unload any loaded modules from that path
    print("🔍 Checking loaded modules to unload...")
    to_delete = []
    for name, module in sys.modules.items():
        try:
            module_file = getattr(module, '__file__', '')
            if module_file and target_base in os.path.normpath(module_file):
                to_delete.append(name)
        except Exception:
            continue

    for name in to_delete:
        del sys.modules[name]
        print(f"🗑️ Unloaded module: {name}")

    # 2. Clean sys.path
    print("\n🧼 Cleaning sys.path...")
    original_paths = sys.path[:]
    sys.path = [p for p in sys.path if target_base not in os.path.normpath(p)]
    for removed in set(original_paths) - set(sys.path):
        print(f"❌ Removed from sys.path: {removed}")

    # 3. Clean environment variables (e.g., LD_LIBRARY_PATH)
    print("\n🌐 Cleaning environment variables...")
    for key, val in os.environ.items():
        if isinstance(val, str) and target_base in val:
            parts = val.split(":")
            cleaned = [p for p in parts if target_base not in os.path.normpath(p)]
            os.environ[key] = ":".join(cleaned)
            print(f"🔧 Cleaned {key}")


# To do:
'''
-manager
-context
-make the editor available from the context and manager


-do something about checking the cache settings all the time


fitting the audio
audio scrubbing
'''

#Done
'''
#cleaner cache management +(yeah it's better now- improvemnts would be writing the cache thread in C++ to avoid GIL contention)
-could also cache backwards from the playhead instead of the start of the cache window
-add sean's option
-audio properly?
-close the cmd when converting audio
-memory release
audio volume control
timeline markers
'''


#oou
'''
prompt a dir check
'''

