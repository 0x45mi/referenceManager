import os
import shutil
import subprocess
import maya.cmds as cmds
import maya.mel as mel

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
        "performCustomFileDropAction2025.mel"
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
    subprocess.run(["pip", "install", "--target=" + cv2_path, "opencv-python"], check=True)

    cmds.confirmDialog(title="Success", message="referenceEditor Installed Successfully! Please restart Maya", button=["OK"])

# Run the installer
install_reference_editor()
