import os
import re
import platform
import shutil
import subprocess
import maya.cmds as cmds
import maya.mel as mel


def onMayaDroppedPythonFile(*args):
    pass

def install_reference_editor():
    # Get path of this script (the installer)
    # __file__ is available if running from a file
    try:
        script_path = os.path.abspath(__file__)
    except NameError:
        # __file__ not defined (e.g. running in script editor), fallback:
        script_path = cmds.file(q=True, sn=True)
        if not script_path:
            cmds.warning("Cannot determine script location. Please run the installer script from file.")
            return

    repo_source = os.path.dirname(script_path)  # Folder containing this installer script

    repo_name = "referenceEditor"
    # Maya modules dir
    modules_dir = os.path.join(cmds.internalVar(userAppDir=True), "modules")
    target_repo = os.path.join(modules_dir, repo_name)
    mod_file = "referenceEditor.mod"
    mod_path = os.path.join(modules_dir, mod_file)

    # Make sure target folders exist
    os.makedirs(target_repo, exist_ok=True)
    os.makedirs(modules_dir, exist_ok=True)

    # Copy scripts folder
    source_scripts_folder = os.path.join(repo_source, "scripts")
    target_scripts_folder = os.path.join(target_repo, "scripts")
    os.makedirs(target_scripts_folder, exist_ok=True)

    files = [
        "customWidgets.py",
        "MLoadUi_2024.py",
        "performCustomFileDropAction.mel",
        "styleSheet.py",
        "customWidgets_2025.py",
        "MLoadUi_2025.py",
        "performCustomFileDropAction2025.mel",
        "editorSettingsWindow.py",
        "editorSettingsWindow_2025.py"
    ]

    for file_name in files:
        src = os.path.join(source_scripts_folder, file_name)
        dst = os.path.join(target_scripts_folder, file_name)
        if os.path.isfile(src):
            shutil.copy(src, dst)
            print(f"Copied: {src} -> {dst}")
        else:
            cmds.warning(f"Missing file: {src}")

    # Copy mod file
    mod_source = os.path.join(repo_source, mod_file)
    if os.path.isfile(mod_source):
        shutil.copy(mod_source, mod_path)
    else:
        cmds.warning(f"Missing mod file: {mod_source}")

    # Copy userSetup.mel


    directory_path = cmds.internalVar(userAppDir=True)

    for child in os.listdir(directory_path):
        if len(child) == 4 and child.isnumeric():
            if int(child) <= 2024:
                user_setup_source = os.path.join(repo_source, "userSetup.mel")
            else:
                user_setup_source = os.path.join(repo_source, "userSetup_2025.mel")

            user_setup_target = os.path.join(cmds.internalVar(userAppDir=True), child, "scripts")  # User scripts dir
            user_setup_target = os.path.join(user_setup_target, "userSetup.mel")

            if os.path.isfile(user_setup_source):
                shutil.copy(user_setup_source, user_setup_target)
            else:
                cmds.warning(f"Missing userSetup.mel: {user_setup_source}")


    # Create cv2Bundle folder
    cv2_path = os.path.join(target_scripts_folder, "cv2Bundle")
    os.makedirs(cv2_path, exist_ok=True)

    # Install opencv-python into cv2Bundle
    mayapy_path = find_mayapy(min_version=2024)
    cmd = [
        mayapy_path,
        "-m",
        "pip",
        "install",
        "opencv-python",
        "--target",
        cv2_path
    ]
    subprocess.run(cmd, check=True)
    
    cmds.confirmDialog(title="Success", message="referenceEditor Installed Successfully! Please restart Maya", button=["OK"])

def find_mayapy(min_version=2024):

    system = platform.system()
    install_dir = cmds.internalVar(mayaInstallDir=True)

    # 1. Pick base Autodesk directory per OS
    if system == "Windows":
        base_path = os.path.dirname(install_dir)
        exe_name = "mayapy.exe"
    elif system == "Darwin":  # macOS
        base_path = os.path.dirname(os.path.dirname(install_dir))
        exe_name = "mayapy"
    else:  # Linux
        base_path = os.path.dirname(install_dir)
        exe_name = "mayapy"

    if not os.path.exists(base_path):
        return None

    # 2. Collect Maya versions
    versions = []
    for item in os.listdir(base_path):
        match = re.search(r"maya?(\d{4})", item, re.IGNORECASE)
        if match:
            versions.append(int(match.group(1)))

    if not versions:
        return None

    # 3. Filter ≥ 2024 and take lowest
    target_version = next((v for v in sorted(versions) if v >= min_version), None)
    if target_version is None:
        return None

    # 4. Build the path to mayapy
    # Windows: Maya2024/mayapy.exe
    # macOS: maya2024/Maya.app/Contents/bin/mayapy
    # Linux: maya2024/bin/mayapy

    version_folder = next(
        f for f in os.listdir(base_path)
        if re.search(str(target_version), f)
    )

    maya_dir = os.path.join(base_path, version_folder)

    if system == "Darwin":  # macOS
        mayapy_path = os.path.join(maya_dir, "Maya.app", "Contents", "bin", exe_name)
    else:
        mayapy_path = os.path.join(maya_dir, "bin", exe_name)

    return mayapy_path

    
# Run the installer
onMayaDroppedPythonFile()
install_reference_editor()