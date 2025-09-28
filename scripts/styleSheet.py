def button_style():
    return """
        QPushButton {
            border-style: outset;
            border-width: 1px;
            border-color: black;
            background: qlineargradient(
                x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 rgba(56, 56, 56, 255),
                stop: 0.25 rgba(50, 50, 50, 255),
                stop: 0.5 rgba(32, 32, 32, 255),
                stop: 0.75 rgba(30, 30, 30, 255),
                stop: 1 rgba(30, 30, 30, 255)
            );
        }

        QPushButton:hover {
            color: rgba(255, 255, 255, 220); /* Brighter text */
            background: qlineargradient(
                x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 rgba(80, 80, 80, 255), /* Brighter gray */
                stop: 0.25 rgba(75, 75, 75, 255),
                stop: 0.5 rgba(60, 60, 60, 255),
                stop: 0.75 rgba(50, 50, 50, 255),
                stop: 1 rgba(45, 45, 45, 255)
            );
        }

        QPushButton:pressed {
            color: rgba(255, 255, 255, 240); /* Even brighter text */
            background: qlineargradient(
                x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 rgba(100, 100, 100, 255), /* Brighter gray */
                stop: 0.25 rgba(90, 90, 90, 255),
                stop: 0.5 rgba(80, 80, 80, 255),
                stop: 0.75 rgba(70, 70, 70, 255),
                stop: 1 rgba(60, 60, 60, 255)
            );
        }
    """

def Play_forwards_style():
    return """
        QPushButton {
            border-radius: 5px;
        }
    """

def Step_one_frame_backwards_style():
    return """
        QPushButton {
            border-top-left-radius: 5px;
            border-bottom-left-radius: 5px;
        }
    """

def Step_one_frame_forwards_style():
    return """
        QPushButton {
            border-left: None;
            border-top-right-radius: 5px;
            border-bottom-right-radius: 5px;
        }
    """

def Set_range_start_style():
    return """
        QPushButton {
            border-top-left-radius: 5px;
            border-bottom-left-radius: 5px;
        }
    """

def Set_range_end_style():
    return """
        QPushButton {
            border-left: None;
            border-top-right-radius: 5px;
            border-bottom-right-radius: 5px;
        }
    """

def Flop_style():
    return """
        QPushButton {
            border-top-left-radius: 4px;
            border-bottom-left-radius: 4px;
        }
    """

def Flip_style():
    return """
        QPushButton {
            border-left: None;
        }
    """

def Crop_style():
    return """
        QPushButton {
            border-left: None;
        }
    """

def Timer_style():
    return """
        QPushButton {
            border-left: None;
            border-top-right-radius: 4px;
            border-bottom-right-radius: 4px;
        }
    """

def Dark_style():
    return """ 

        background-color: rgba(17, 17, 17, 255);    
        border: none;            
        color: rgba(169, 169, 169, 255);
        font-size: 11px;
        border-color: rgba(33, 33, 33, 255);                                   
    """

def Light_style():
    return """

        background-color: rgba(33, 33, 33, 255);    
        border: none;            
        color: rgba(169, 169, 169, 255);
        font-size: 11px;
        border-color: rgba(33, 33, 33, 255);             
    """

def Dark_button_style():
    return """
        QPushButton {
            background-color: #202020;
            border: 1px solid #555555;
            border-radius: 5px;
            color: #aaaaaa;
            font-size: 11.5px;
            padding: 5px 10px;
        }

        QPushButton:hover {
            background-color: #333333;
            border-color: #888888;
            color: #ffffff;
        }

        QPushButton:pressed {
            background-color: #111111;
            border-color: #555555;
            color: #cccccc;
        }

        QPushButton:focus {
            outline: none;
        }
    """

def Black_line_edit_style():
    return """
            background-color: black;    
            border: none;            
            color: white;
            font-size: 16px                                                
        """

def Help_line_style():
    return """
            background-color: #212121;
            border: none;
            color: rgba(169, 169, 169, 255);
        """

def maya_button_style():
    return """
        QPushButton {
            border-style: outset;
            border-width: 1px;
            border-radius: 4px;
            border-color: #111111;
            background: qlineargradient(
                x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 rgba(65, 65, 65, 255),
                stop: 0.15 rgba(47, 47, 47, 255),
                stop: 1 rgba(40, 40, 40, 255)
            );
        }

        QPushButton:hover {
            color: rgba(255, 255, 255, 220); /* Brighter text */
            background: qlineargradient(
                x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 rgba(80, 80, 80, 255), /* Brighter gray */
                stop: 0.25 rgba(75, 75, 75, 255),
                stop: 0.5 rgba(60, 60, 60, 255),
                stop: 0.75 rgba(50, 50, 50, 255),
                stop: 1 rgba(45, 45, 45, 255)
            );
        }

        QPushButton:pressed {
            color: rgba(255, 255, 255, 240); /* Even brighter text */
            background: qlineargradient(
                x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 rgba(100, 100, 100, 255), /* Brighter gray */
                stop: 0.25 rgba(90, 90, 90, 255),
                stop: 0.5 rgba(80, 80, 80, 255),
                stop: 0.75 rgba(70, 70, 70, 255),
                stop: 1 rgba(60, 60, 60, 255)
            );
        }
    """

def Light_button_style():
    return """
        QPushButton {
            border-style: outset;
            border-width: 0px;
            border-radius: 3px;
            border-color: #212121;
            background-color: #313131; 

        }

        QPushButton:hover {
            color: rgba(255, 255, 255, 220); /* Brighter text */
            background: qlineargradient(
                x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 rgba(80, 80, 80, 255), /* Brighter gray */
                stop: 0.25 rgba(75, 75, 75, 255),
                stop: 0.5 rgba(60, 60, 60, 255),
                stop: 0.75 rgba(50, 50, 50, 255),
                stop: 1 rgba(45, 45, 45, 255)
            );
        }

        QPushButton:pressed {
            color: rgba(255, 255, 255, 240); /* Even brighter text */
            background: qlineargradient(
                x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 rgba(100, 100, 100, 255), /* Brighter gray */
                stop: 0.25 rgba(90, 90, 90, 255),
                stop: 0.5 rgba(80, 80, 80, 255),
                stop: 0.75 rgba(70, 70, 70, 255),
                stop: 1 rgba(60, 60, 60, 255)
            );
        }
    """