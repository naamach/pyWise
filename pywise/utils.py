import numpy as np
from configparser import ConfigParser
import logging
import os
import datetime


def get_config(config_file="config.ini"):
    config = ConfigParser(inline_comment_prefixes=';')
    config.read(config_file)
    return config


def init_log(filename="log.log", config_file="config.ini"):
    config = get_config(config_file)
    log_path = config.get('LOG', 'PATH')  # log file path
    console_log_level = config.get('LOG', 'CONSOLE_LEVEL')  # logging level
    file_log_level = config.get('LOG', 'FILE_LEVEL')  # logging level

    # create log folder
    if not os.path.exists(log_path):
        os.makedirs(log_path)

    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)

    # console handler
    h = logging.StreamHandler()
    h.setLevel(logging.getLevelName(console_log_level))
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
    h.setFormatter(formatter)
    log.addHandler(h)

    # log file handler
    h = logging.FileHandler(log_path + filename + ".log", "w", encoding=None, delay="true")
    h.setLevel(logging.getLevelName(file_log_level))
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s [%(filename)s:%(lineno)s]: %(message)s", "%Y-%m-%d %H:%M:%S")
    h.setFormatter(formatter)
    log.addHandler(h)

    return log


def close_log(log):
    handlers = list(log.handlers)
    for h in handlers:
        log.removeHandler(h)
        h.flush()
        h.close()


def find_groups(imlist, keys, return_inverse=False):
    """
    sorts imlist to groups according to keys.

    :param imlist: ccdproc.ImageFileCollection
    :param keys: list of keywords
    :param return_inverse: True - return unique indices
    :return: groups by keywords
             idx by group id
    """
    vals = [imlist.values(key) for key in keys]
    if return_inverse:
        groups, idx = np.unique(vals, axis=1, return_inverse=return_inverse)
        return groups, idx
    else:
        groups = np.unique(vals, axis=1)
        return groups


def get_ccd_shape(imlist, telescope, original_keys=False):
    out_keys = ["x_naxis", "y_naxis", "x_subframe", "y_subframe", "x_bin", "y_bin"]
    if telescope in ["1m", "C28", "C18"]:
        keys = ["naxis1", "naxis2", "xorgsubf", "yorgsubf", "xbinning", "ybinning"]
    else:
        raise Exception(f"Not implemented for {telescope} yet!")

    groups = find_groups(imlist, keys)

    if original_keys:
        out_keys = keys

    ccd_shape = {out_keys[i]: groups[i] for i in range(len(out_keys))}

    return ccd_shape


def get_set_from_dict(data, idx=0):

    return {key: val[idx] for key, val in data.items()}


def get_ccd_str(ccd_shape, idx=0):
    # get only a single set of values
    ccd_shape = get_set_from_dict(ccd_shape, idx)

    ccd_str = f"""x{ccd_shape["x_subframe"]}-{ccd_shape["x_naxis"]}_{ccd_shape["x_bin"]}bin""" \
              f"""_y{ccd_shape["y_subframe"]}-{ccd_shape["y_naxis"]}_{ccd_shape["y_bin"]}bin"""
    return ccd_str


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + datetime.timedelta(n)
