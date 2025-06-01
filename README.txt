The reference editor is a widget to review reference footage and add it to your maya scene as an image plane, faser. It's designed to look and behave similar to RV. It handles cutting the video, cropping and flipping, converting framerates and resolution and managing the files, so you don't have to! Options to export in .jpeg and .png and choose a start frame are available.

How to use:
1.Drop your video or image into maya's viewport
2.Edit in the widget
3.Follow the dialogs to create the image plane

How to install-
1.Download the repo and extract files
2.Drop the dragAndDropInstall.mel in Maya.

For the drop install to work, you will need pip configured correctly in your system PATH and internet access on your machine. 
If the installation fails, you will have to do the last step manually (make cv2 available for the tool), or install pip:)-
Download prebuilt cv2 and numpy wheels compatible with your system for python3.10 they are available here:
https://pypi.org/project/opencv-python/#files
http://pypi.org/project/numpy/#files
you can extract the files with 7zip, then take all the extracted files to: C:\Users\yourUser\Documents\maya\modules\referenceEditor\scripts\cv2Bundle
For example:
C:\Users\yourUser\Documents\maya\modules\referenceEditor\scripts\cv2Bundle\cv2
C:\Users\yourUser\Documents\maya\modules\referenceEditor\scripts\cv2Bundle\numpy
etc.

Restart maya and drop a video into the viewport

I haven't tested too much yet, but I had a video that didn't show so I'll have to investigate(it did convert and show in maya though).

Top tips- 
Rename the video before dragging it in the viewport, this will make it save with a nice name.

Shortcuts: 
[ -start range
] -end range
, -previous frame
. -next frame
sapce/l/Alt+v/Meta+v -toggle playback
There is also a focus drag on the video to scroll though frames slower if the video is too long, just like RV! 

