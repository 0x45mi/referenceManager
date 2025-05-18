The reference editor is a widget to review reference footage and add it to your maya scene as an image plane, faser. It's designed to look and behave similar to RV. It handles cutting the video, cropping and flipping, converting framerates and resolution and managing the files, so you don't have to! Options to export in .jpeg and .png and choose a start frame are available.

How to use:
1.Drop your video or image into maya's viewport
2.Edit in the widget
3.Follow the dialogs to create the image plane

How to install-
I will make this better at some point, but for now:
1.Download the repo and extract files
2.Move the referenceManager-main folder to you scripts folder, it should look like this: C:\Users\yourUser\Documents\maya\2024\scripts\referenceManager-main\scripts
3.Take the referenceEditor.mod and put it in maya's module folder: C:\Users\emimo\Documents\maya\modules\referenceEditor.mod
4.Open referenceEditor.mod and edit the module so it points to the right place: + ReferenceEditor 1.0 C:/Users/yourUser/Documents/maya/2024/scripts/referenceManager-main
5.Take userSetup.mel and put in the scripts folder: C:\Users\yourUse\Documents\maya\2024\scripts\userSetup.mel
6.In the scripts folder, make a folder called cv2Bundle. Then pip install cv2-python into that folder. 
In a terminal, the command is: pip install target="C:/Users/yourUser/Documents/maya/2024/scripts/referenceManager-main/scripts/cv2Bundle" opencv-python

It should work now! Very simple I know, sorry about that I pinky promise I will make it better at some point, just not today.
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

