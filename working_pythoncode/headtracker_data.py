"""
Handling of headtracker data from DT2 class
author: H. Zhu, M. Heiss
"""


def clean_and_split(line):
    """
    H2 -- clean_and_split
    ===================
    **Formatting of headtracker data output from DT2.**
    """
    strings = str(line)  # everything as a string
    wo_brackets = strings.replace("]", "")  # removes ] brackets
    splitted = wo_brackets.split("[")  # creates LIST with items between [
    return splitted


def string_to_float(s):
    """
    H2 -- string_to_float
    ===================
    **Formatting of headtracker data output from DT2.**
    """
    splitted = s.split(" ")
    coor_float = [float(i) for i in splitted]
    return coor_float


def azimuth_angle(data):
    """
    H2 -- azimuth_angle
    ===================
    **Extraction of azimuthal angle from headtracker data output and
    conversion to defined coordinate system.**
    """
    data_list = clean_and_split(data)  # returns list of string objects
    coor = data_list[3]  # returns the coordinate entry [x y z polar azimuth]
    coor_float = string_to_float(coor)  # converges strings to floats
    azimuth = coor_float[5]  # picks the azimuth angle from the floats

    # Conversion nessesary
    # as Headtracker angle orientation different from the GUI definition
    if azimuth <= 0:
        azimuth = -1*azimuth
    else:
        azimuth = 360 - azimuth

    return azimuth
