# Reference Editor for Maya 
The reference editor is a widget to review reference footage and add it to your maya scene as an image plane, faser. It's designed to look and behave similar to RV. It handles cutting the video, cropping and flipping, converting framerates and resolution and managing the files, so you don't have to! Options to export in .jpeg and .png and choose a start frame are available.

## How to use it <br/>
1. Drop your video or image into maya's viewport. <br/>
2. Edit in the widget. <br/>
3. Follow the dialogs to create the image plane. <br/>

<img src="https://github.com/0x45mi/referenceManager/blob/main/demo/referenceEditorDemo.gif?raw=true" data-canonical-src="https://github.com/0x45mi/referenceManager/blob/main/demo/referenceEditorDemo.gif?raw=true" width="800" />

### Tour of the UI and shortcuts!
<img src="https://github.com/0x45mi/referenceManager/blob/main/demo/UITour.jpg?raw=true" data-canonical-src="https://github.com/0x45mi/referenceManager/blob/main/demo/UITour.jpg?raw=true" width="800" />
 <br/>


| | Description | Shortcut|
|--------|-------------|---------|
| 1 | Frame step | ,, Arrow Left, ., Arrow Right|
| 2 | Set range start and end | [ ] |
| 3 | Flop | Shift + X |
| 4 | Crop | C |
| 5 | Flip | Shift + Y |
| 6 | Retime | Shift + F |
| 7 | Framerate at which to export the image sequence | |
| 8 | Resolution at which to export the images | |
| 9 | Export format | |
| 10 | Start number of the image sequence | |
| 11 | Reset | |
| 12 | Settings | |
| | Play/pause toggle | L, Alt + V, Space |

+ Focus mode: scroll over the video to scroll through frames more slowly
+ Interactive slider handles
+ If you drop an image in the viewport it will make the image plane for the sequence. Assumes editing has been done elsewhere.

<br/>
SETTINGS WINDOW <br/>
<br/>
<img src="https://github.com/0x45mi/referenceManager/blob/main/demo/settingsTour.jpg?raw=true" data-canonical-src="https://github.com/0x45mi/referenceManager/blob/main/demo/settingsTour.jpg?raw=true" />
 
1. Copy path to clipboard <br/>
2. Edit path to where you save your references <br/>
3. Cache toggle ON/OFF <br/>
4. Reset cache settings to default <br/>
5. Cache size in frames. Maximum number of frames to be held in memory <br/>
6. Decode these many frames ahead of the playhead <br/>
7. Decode these many frames behind the playhead <br/>
8. Create an image plane attached to a camera in Maya <br/>
9. Create a floating image plane in Maya <br/>


## Version compatibility
- Python 3 and pyside2 (Maya 2024)  <br/>
- Python 3 and pysyde6 (Maya 2025/2026) <br/>

-Test log <br/>
Tested in Maya 2024 Windows  <br/>
Tested in Maya 2025 Windows <br/>
Worked in Maya 2022 Linux  <br/>
Worked in Maya 2023 Linux  <br/>
Worked in Maya 2025 Linux  <br/>
Worked in Maya 2026 Windows  <br/>

## How to install
1. Download the repository and extract files. <br/>
2. Drop dragAndDropInstall.py in Maya. <br/>
3. Restart maya. <br/>
<br/>
<img src="https://github.com/0x45mi/referenceManager/blob/main/demo/referenceEditorInstall.gif" data-canonical-src="https://github.com/0x45mi/referenceManager/blob/main/demo/referenceEditorInstall.gif" width="800" />

For the drop install to work, you will need pip configured correctly in your system PATH and internet access on your machine. <br/>

- The plugin requires ffmpeg. Please [install ffmpeg](https://pypi.org/project/ffmpeg/) on your computer.<br/>

### Manual installation
If the installation fails, you will have to do the last step manually (make cv2 available for the tool), or [install pip](https://pip.pypa.io/en/stable/installation/) . <br/>
Download prebuilt cv2 and numpy wheels compatible with your system for python3.10 they are available here: <br/>
https://pypi.org/project/opencv-python/#files <br/>
http://pypi.org/project/numpy/#files <br/>
You can extract the files with 7zip, then take all the extracted files to: <br/>
```
C:\Users\yourUser\Documents\maya\modules\referenceEditor\scripts\cv2Bundle
```
It should look like this: <br/>
C:\Users\yourUser\Documents\maya\modules\referenceEditor\scripts\cv2Bundle\cv2 <br/>
C:\Users\yourUser\Documents\maya\modules\referenceEditor\scripts\cv2Bundle\numpy 
<br/>
Restart maya and drop a video into the viewport to check it's working. <br/>

- The plugin requires ffmpeg. Please [install ffmpeg](https://pypi.org/project/ffmpeg/) on your computer.<br/>

### Uninstall
Delete "referenceEditor.mod" and "referenceEditor" folder from your Maya modules folder. "C:\Users\yourUser\Documents\maya\modules" <br/>
Delete "userSetup.mel" from your maya version scripts folder. "C:\Users\yourUser\Documents\maya\2024\scripts" <br/>

