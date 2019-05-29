import numpy as np


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
