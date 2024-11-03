import maya.cmds as cmds
import os

def browse_directory(directory_field):
    directory = cmds.fileDialog2(fileMode=3, dialogStyle=2)
    if directory:
        cmds.textField(directory_field, edit=True, text=directory[0])

def perform_playblast(selected_cameras, output_directory, format_option, resolution_option, custom_width, custom_height, quality, prefix):
    if not selected_cameras:
        cmds.warning("Please select at least one camera.")
        return

    start_time = cmds.playbackOptions(query=True, min=True)
    end_time = cmds.playbackOptions(query=True, max=True)

    for camera_transform in selected_cameras:
        camera_shape = cmds.listRelatives(camera_transform, children=True, type='camera')[0]
        camera_name = camera_transform.split('|')[-1].replace('Shape', '')

        output_file = os.path.join(output_directory, f"{prefix}_{camera_name}")
        cmds.lookThru(camera_shape)

        playblast_args = {
            'format': format_option,
            'filename': output_file,
            'clearCache': True,
            'viewer': False,
            'showOrnaments': True,
            'fp': 4,
            'percent': 100,
            'forceOverwrite': True,
            'startTime': start_time,
            'endTime': end_time,
            'quality': quality,
            'compression': 'H.264'
        }

        if resolution_option == "Custom":
            playblast_args['width'] = custom_width
            playblast_args['height'] = custom_height
        else:
            render_settings = (cmds.getAttr("defaultResolution.width"), cmds.getAttr("defaultResolution.height"))
            playblast_args['width'], playblast_args['height'] = render_settings

        try:
            cmds.playblast(**playblast_args)
            print(f"Playblast created for {camera_name}: {output_file}")
        except Exception as e:
            cmds.warning(f"Failed to create playblast for {camera_name}: {str(e)}")

def refresh_camera_list(camera_list):
    all_cameras = cmds.ls(type="camera", long=True)
    camera_transforms = [cmds.listRelatives(cam, parent=True)[0] for cam in all_cameras]
    cmds.textScrollList(camera_list, edit=True, removeAll=True)
    cmds.textScrollList(camera_list, edit=True, append=camera_transforms)

def display_selected_cameras(camera_list):
    selected_cameras = cmds.textScrollList(camera_list, query=True, selectItem=True)
    if not selected_cameras:
        cmds.warning("Please select at least one camera.")
        return

    if cmds.columnLayout("cameraRenameLayout", exists=True):
        cmds.deleteUI("cameraRenameLayout")

    cmds.columnLayout("cameraRenameLayout", adjustableColumn=True, parent="cameraRenameSection")
    for camera in selected_cameras:
        cmds.rowLayout(numberOfColumns=2, adjustableColumn=2)
        cmds.text(label=f"{camera}: ")
        cmds.textField(f"{camera}_renameField", placeholderText="New name here")
        cmds.setParent("..")

def apply_rename(camera_list):
    selected_cameras = cmds.textScrollList(camera_list, query=True, selectItem=True)
    for camera in selected_cameras:
        new_name = cmds.textField(f"{camera}_renameField", query=True, text=True)
        if new_name:
            try:
                cmds.rename(camera, new_name)
                print(f"Camera {camera} renamed to {new_name}")
            except Exception as e:
                cmds.warning(f"Failed to rename {camera}: {str(e)}")
    
    refresh_camera_list(camera_list)

def save_settings(directory, prefix, format_option, resolution_option, custom_width, custom_height, quality):
    cmds.optionVar(sv=("outputDirectory", directory))
    cmds.optionVar(sv=("prefix", prefix))
    cmds.optionVar(sv=("formatOption", format_option))
    cmds.optionVar(sv=("resolutionOption", resolution_option))
    cmds.optionVar(iv=("customWidth", custom_width))
    cmds.optionVar(iv=("customHeight", custom_height))
    cmds.optionVar(iv=("quality", quality))

def load_settings():
    return [
        cmds.optionVar(q="outputDirectory"),
        cmds.optionVar(q="prefix"),
        cmds.optionVar(q="formatOption"),
        cmds.optionVar(q="resolutionOption"),
        cmds.optionVar(q="customWidth"),
        cmds.optionVar(q="customHeight"),
        cmds.optionVar(q="quality"),
    ]

def create_playblast_ui():
    if cmds.window("playblastUI", exists=True):
        cmds.deleteUI("playblastUI")
    
    window = cmds.window("playblastUI", title="Playblast Multiple Camera", widthHeight=(400, 600), sizeable=True)
    cmds.columnLayout(adjustableColumn=True)
    
    # Load saved settings
    output_directory, prefix, format_option, resolution_option, custom_width, custom_height, quality = load_settings()

    # Camera selection section
    cmds.text(label=" Camera selection:")
    all_cameras = cmds.ls(type="camera", long=True)
    camera_transforms = [cmds.listRelatives(cam, parent=True)[0] for cam in all_cameras]
    camera_list = cmds.textScrollList(numberOfRows=8, allowMultiSelection=True, append=camera_transforms)

    cmds.separator(height=10, style='none')  # Spacer

    # Output directory section
    cmds.text(label=" Output Directory:")
    directory_field = cmds.textField(text=output_directory if output_directory else os.path.expanduser("~/Desktop"), width=200)
    cmds.button(label="Browse", command=lambda x: browse_directory(directory_field))

    cmds.separator(height=10, style='none')  # Spacer

    # Prefix section
    cmds.text(label=" Prefix for Clips:")
    prefix_field = cmds.textField("prefixField", text=prefix if prefix else "", placeholderText="Enter prefix here", width=200)

    cmds.separator(height=10, style='none')  # Spacer

    # Playblast format and quality section
    cmds.rowLayout(numberOfColumns=4, adjustableColumn=2)
    cmds.text(label=" Select Format:")
    format_menu = cmds.optionMenu()
    cmds.menuItem(label="qt")
    cmds.menuItem(label="avi")
    if format_option:
        cmds.optionMenu(format_menu, edit=True, value=format_option)
    
    cmds.text(label=" Quality (0-100):")
    quality_field = cmds.textField("qualityField", text=str(quality) if quality else "100", width=50)
    cmds.setParent("..")

    cmds.separator(height=10, style='none')  # Spacer

    # Resolution section
    cmds.text(label=" Resolution:")
    resolution_menu = cmds.optionMenu()
    cmds.menuItem(label="Render Settings")
    cmds.menuItem(label="Custom")
    if resolution_option:
        cmds.optionMenu(resolution_menu, edit=True, value=resolution_option)

    custom_width_field = cmds.textField("customWidth", text=str(custom_width) if custom_width else "", placeholderText="Width", width=100)
    custom_height_field = cmds.textField("customHeight", text=str(custom_height) if custom_height else "", placeholderText="Height", width=100)

    cmds.separator(height=10, style='none')  # Spacer
    
    # Display rename fields
    cmds.button(label="Show Rename Fields", command=lambda x: display_selected_cameras(camera_list))

    # Section for rename fields
    cmds.columnLayout("cameraRenameSection", adjustableColumn=True)

    cmds.separator(height=10, style='none')  # Spacer

    # Rename apply button
    cmds.button(label="Apply Rename", command=lambda x: apply_rename(camera_list))
    
    cmds.separator(height=10, style='none')  # Spacer

    # Playblast button
    cmds.button(label="Playblast", command=lambda x: perform_playblast(
        cmds.textScrollList(camera_list, query=True, selectItem=True),
        cmds.textField(directory_field, query=True, text=True),
        cmds.optionMenu(format_menu, query=True, value=True),
        cmds.optionMenu(resolution_menu, query=True, value=True),
        int(cmds.textField(custom_width_field, query=True, text=True)) if cmds.optionMenu(resolution_menu, query=True, value=True) == "Custom" else None,
        int(cmds.textField(custom_height_field, query=True, text=True)) if cmds.optionMenu(resolution_menu, query=True, value=True) == "Custom" else None,
        int(cmds.textField(quality_field, query=True, text=True)),
        cmds.textField(prefix_field, query=True, text=True)
    ))

    cmds.separator(height=10, style='none')  # Spacer

    # Save and Reset Settings buttons in the same row
    cmds.rowLayout(numberOfColumns=2, adjustableColumn=1, columnWidth2=(190, 190), columnAlign2=("center", "center"))
    cmds.button(label="Save Settings", command=lambda x: save_settings(
        cmds.textField(directory_field, query=True, text=True),
        cmds.textField(prefix_field, query=True, text=True),
        cmds.optionMenu(format_menu, query=True, value=True),
        cmds.optionMenu(resolution_menu, query=True, value=True),
        cmds.textField(custom_width_field, query=True, text=True),
        cmds.textField(custom_height_field, query=True, text=True),
        cmds.textField(quality_field, query=True, text=True)
    ))
    cmds.button(label="Reset Settings", command=lambda x: reset_settings(
        prefix_field, format_menu, resolution_menu, custom_width_field, custom_height_field, quality_field
    ))
    cmds.setParent("..")

    cmds.separator(height=10, style='none')  # Spacer
    
    # Add this to the bottom of the UI layout to display version and author
    cmds.separator(height=10, style='none')  # Spacer
    cmds.text(label="Version 1.0.0", align='center')
    cmds.text(label="Author: Ai", align='center')

    cmds.showWindow(window)

# Create the UI
create_playblast_ui()