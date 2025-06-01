# Reference Editor for Maya 
The reference editor is a widget to review reference footage and add it to your maya scene as an image plane, faser. It's designed to look and behave similar to RV. It handles cutting the video, cropping and flipping, converting framerates and resolution and managing the files, so you don't have to! Options to export in .jpeg and .png and choose a start frame are available.

## How to install
1. Download the repository and extract files. <br/>
2. Drop dragAndDropInstall.py in Maya. <br/>
3. Restart maya. <br/>
<br/>
<img src="https://github.com/0x45mi/referenceManager/blob/main/demo/referenceEditorInstall.gif" data-canonical-src="https://github.com/0x45mi/referenceManager/blob/main/demo/referenceEditorInstall.gif" width="700" />

For the drop install to work, you will need pip configured correctly in your system PATH and internet access on your machine. <br/>

If the installation fails, you will have to do the last step manually (make cv2 available for the tool), or install pip. <br/>
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
