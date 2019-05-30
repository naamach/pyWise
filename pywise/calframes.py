import numpy as np
from astropy import units as u
import ccdproc
import os
import datetime
import glob
import logging
from pywise import utils


def create_master_bias(imlist, filename="mbias", save_uncertainty=False, max_num_frames=-1, log=None, **kwargs):
    if log is None:
        log = logging.getLogger(__name__)

    # collect all individual images
    kwargs["imagetyp"] = "BIAS"
    bias_list = []
    for bias in imlist.hdus(**kwargs):
        bias_list.append(ccdproc.CCDData(data=bias.data, unit=u.adu))

    log.debug(f"Bias list contains {len(bias_list)} files.")
    if max_num_frames > 0:
        bias_list[max_num_frames:] = []

    if len(bias_list) > 0:
        biases = ccdproc.Combiner(bias_list, dtype=np.float32)
        master_bias = biases.median_combine()
        if not save_uncertainty:
            master_bias.uncertainty = None
            master_bias.mask = None
        master_bias.write(filename + ".fits", overwrite=True)
        log.info(f"Master bias created and saved in {filename}.fits")
    else:
        master_bias = ccdproc.CCDData(data=[], unit=u.adu)
        log.warning(f"No raw bias frames found for {filename}!")

    return master_bias


def create_master_dark(imlist, bias=[], filename="mdark", save_uncertainty=False, max_num_frames=-1,
                       log=None, **kwargs):
    if log is None:
        log = logging.getLogger(__name__)

    # collect all individual images
    kwargs["imagetyp"] = "DARK"
    dark_list = []
    for dark in imlist.hdus(**kwargs):
        if bias:
            dark = ccdproc.subtract_bias(ccdproc.CCDData(data=dark.data, unit=u.adu, header=dark.header), bias)
        dark_list.append(ccdproc.CCDData(data=dark.data, unit=u.adu, header=dark.header))

    log.debug(f"Dark list contains {len(dark_list)} files.")
    if max_num_frames > 0:
        dark_list[max_num_frames:] = []

    if len(dark_list) > 0:
        darks = ccdproc.Combiner(dark_list, dtype=np.float32)
        # apply exposure-time scaling before combining:
        darks.scaling = [1/dark.header["EXPTIME"] for dark in dark_list]
        master_dark = darks.median_combine()
        if not save_uncertainty:
            master_dark.uncertainty = None
            master_dark.mask = None

        master_dark.header["EXPTIME"] = 1  # [sec]
        master_dark.write(filename + ".fits", overwrite=True)
        log.info(f"Master dark created and saved in {filename}.fits")
    else:
        master_dark = ccdproc.CCDData(data=[], unit=u.adu)
        log.warning(f"No raw dark frames found for {filename}!")

    return master_dark


def create_master_flat(imlist, bias=[], dark=[], filt="", filename="mflat", save_uncertainty=False, is_overwrite=True,
                       max_num_frames=-1, log=None, **kwargs):
    if log is None:
        log = logging.getLogger(__name__)

    if len(filt) == 0:
        if "filter" in imlist.keywords:
            filt_idx = ~imlist.summary["filter"].mask  # images with unmasked filter
            filters = np.unique(imlist.summary[filt_idx]["filter"])
        else:
            log.warning(f"No raw flat frames found for {filename}!")
            return
    else:
        filters = filt

    for filt in filters:
        file_exists = os.path.isfile(filename + "_" + filt + ".fits")
        if file_exists & (not is_overwrite):
            log.debug(f"{filt} master flat exists, skipping.")
            continue

        # collect all individual images
        kwargs["imagetyp"] = "FLAT"
        kwargs["filter"] = filt
        flat_list = []
        for flat in imlist.hdus(**kwargs):
            if bias:
                flat = ccdproc.subtract_bias(ccdproc.CCDData(data=flat.data, unit=u.adu, header=flat.header), bias)
            if dark:
                flat = ccdproc.subtract_dark(flat, dark, exposure_time="EXPTIME", exposure_unit=u.s, scale=True)
            flat_list.append(ccdproc.CCDData(data=flat.data, unit=u.adu, header=flat.header))

        if max_num_frames > 0:
            flat_list[max_num_frames:] = []

        log.debug(f"Flat {filt} list contains {len(flat_list)} files.")
        if len(flat_list) > 0:
            flats = ccdproc.Combiner(flat_list, dtype=np.float32)
            # apply exposure-time scaling before combining:
            flats.scaling = [1 / np.mean(flat) for flat in flat_list]
            master_flat = flats.median_combine()
            if not save_uncertainty:
                master_flat.uncertainty = None
                master_flat.mask = None

            master_flat.header["EXPTIME"] = 1  # [sec]
            master_flat.write(filename + "_" + filt + ".fits", overwrite=True)
            log.info(f"Master flat created and saved in {filename}.fits")
        else:
            log.warning(f"No raw flat frames found for {filename}!")

    return


def create_masters(year=datetime.date.today().year, month=datetime.date.today().month, day=datetime.date.today().day,
                   telescope="C28", log=None, config_file="config.ini"):
    assert(telescope in ["C28", "C18"]), f"Not implemented for {telescope} yet!"

    if log is None:
        log = logging.getLogger(__name__)

    config = utils.get_config(config_file)

    t = datetime.date(year, month, day)
    t_str = datetime.date.strftime(t, format="%Y%m%d")

    im_path = config.get("GENERAL", "PATH") + config.get(telescope, "PATH") + t_str + config.get(telescope, "DIR_SUFFIX")

    if not os.path.isdir(im_path):
        log.warning(f"Folder {im_path} doesn't exist!")
        return

    max_day_shift = config.getint("CAL", "MAX_DAY_SHIFT")
    a = range(-1, -max_day_shift-1, -1)
    b = range(1, max_day_shift+1, 1)
    day_shift = [None]*(len(a)+len(b))
    day_shift[0::2] = a
    day_shift[1::2] = b

    max_num_frames = config.getint("CAL", "MAX_NUM_FRAMES")
    save_uncertainty = config.getboolean("GENERAL", "SAVE_UNCERTAINTY")
    is_overwrite = config.getboolean("CAL", "OVERWRITE")

    cal_archive_path = config.get("CAL", "PATH") + telescope + os.sep
    # create calibration frame folder
    if not os.path.exists(cal_archive_path):
        os.makedirs(cal_archive_path)

    imlist = ccdproc.ImageFileCollection(im_path, keywords='*')

    if len(imlist.files) == 0:
        log.warning(f"No images taken on {t_str}.")
        return

    instrument = imlist.values("instrume", True)[0]  # assuming a single instrument per night
    ccd_shape = utils.get_ccd_shape(imlist, telescope)

    for i in range(len(ccd_shape["x_naxis"])):

        ccd_str = utils.get_ccd_str(ccd_shape, idx=i)
        base_filename = f"_{telescope}_{instrument}_{t_str}_{ccd_str}"
        keys = utils.get_set_from_dict(utils.get_ccd_shape(imlist, telescope, original_keys=True), idx=i)

        # create master bias
        bias_file = f"{cal_archive_path}Bias{base_filename}"
        file_exists = os.path.isfile(bias_file + ".fits")
        if (not file_exists) | (file_exists & is_overwrite):
            bias = create_master_bias(imlist, filename=bias_file, save_uncertainty=save_uncertainty,
                                      max_num_frames=max_num_frames, log=log, **keys)
        else:
            log.debug(f"Master bias exists, skipping.")
            bias = ccdproc.CCDData.read(bias_file + ".fits")

        # if no bias frames were found
        if bias.size == 0:
            # look for an archival master bias
            i = 0
            while (bias.size == 0) and (i < len(day_shift)):
                curr_day = datetime.datetime.strftime(t + datetime.timedelta(days=day_shift[i]), "%Y%m%d")
                filename = glob.glob(f"{cal_archive_path}Bias_{telescope}_{instrument}_{curr_day}_{ccd_str}.fits")
                if filename:
                    bias_file = filename[0]
                    bias = ccdproc.CCDData.read(bias_file)
                else:
                    i += 1

        dark_file = f"{cal_archive_path}Dark{base_filename}"
        file_exists = os.path.isfile(dark_file + ".fits")
        if (not file_exists) | (file_exists & is_overwrite):
            dark = create_master_dark(imlist, bias, filename=dark_file, save_uncertainty=save_uncertainty,
                                      max_num_frames=max_num_frames, log=log, **keys)
        else:
            log.debug(f"Master dark exists, skipping.")
            dark = ccdproc.CCDData.read(dark_file + ".fits")

        if dark.size == 0:
            # look for an archival master dark
            i = 0
            while (dark.size == 0) and (i < len(day_shift)):
                curr_day = datetime.datetime.strftime(t + datetime.timedelta(days=day_shift[i]), "%Y%m%d")
                filename = glob.glob(f"{cal_archive_path}Dark_{telescope}_{instrument}_{curr_day}_{ccd_str}.fits")
                if filename:
                    dark_file = filename[0]
                    dark = ccdproc.CCDData.read(dark_file)
                else:
                    i += 1

        flat_file = f"{cal_archive_path}Flat{base_filename}"
        create_master_flat(imlist, bias, dark, filename=flat_file, save_uncertainty=save_uncertainty,
                           is_overwrite=is_overwrite, max_num_frames=max_num_frames, log=log, **keys)


def get_calframes(year, month, day, filt, ccd_str, telescope="C28", instrument="FLI-PL16801", log=None, config_file="config.ini"):
    if log is None:
        log = logging.getLogger(__name__)

    config = utils.get_config(config_file)

    t = datetime.date(year, month, day)
    t_str = datetime.date.strftime(t, format="%Y%m%d")

    max_day_shift = config.getint("CAL", "MAX_DAY_SHIFT")
    a = range(-1, -max_day_shift-1, -1)
    b = range(1, max_day_shift+1, 1)
    day_shift = [None]*(len(a)+len(b))
    day_shift[0::2] = a
    day_shift[1::2] = b

    cal_archive_path = config.get("CAL", "PATH") + telescope + os.sep

    base_filename = f"_{telescope}_{instrument}_{t_str}_{ccd_str}"

    # find master bias
    bias_file = f"{cal_archive_path}Bias{base_filename}.fits"
    file_exists = os.path.isfile(bias_file)
    if not file_exists:
        bias_file = ""
        # look for an archival master bias
        i = 0
        while (not bias_file) and (i < len(day_shift)):
            curr_day = datetime.date.strftime(t + datetime.timedelta(days=day_shift[i]), "%Y%m%d")
            filename = glob.glob(f"{cal_archive_path}Bias_{telescope}_{instrument}_{curr_day}_{ccd_str}.fits")
            if filename:
                bias_file = filename[0]
            else:
                i += 1
    if not bias_file:
        log.error(f"No master bias was found within {day_shift} days!")

    dark_file = f"{cal_archive_path}Dark{base_filename}.fits"
    file_exists = os.path.isfile(dark_file)
    if not file_exists:
        dark_file = ""
        # look for an archival master dark
        i = 0
        while (not dark_file) and (i < len(day_shift)):
            curr_day = datetime.date.strftime(t + datetime.timedelta(days=day_shift[i]), "%Y%m%d")
            filename = glob.glob(f"{cal_archive_path}Dark_{telescope}_{instrument}_{curr_day}_{ccd_str}.fits")
            if filename:
                dark_file = filename[0]
            else:
                i += 1
    if not dark_file:
        log.error(f"No master dark was found within {day_shift} days!")

    flat_file = f"{cal_archive_path}Flat{base_filename}_{filt}.fits"
    file_exists = os.path.isfile(flat_file)
    if not file_exists:
        flat_file = ""
        # look for an archival master flat
        i = 0
        while (not flat_file) and (i < len(day_shift)):
            curr_day = datetime.date.strftime(t + datetime.timedelta(days=day_shift[i]), "%Y%m%d")
            filename = glob.glob(f"{cal_archive_path}Flat_{telescope}_{instrument}_{curr_day}_{ccd_str}_{filt}.fits")
            if filename:
                flat_file = filename[0]
            else:
                i += 1
    if not flat_file:
        log.error(f"No {filt} master flat was found within {day_shift} days!")

    return bias_file, dark_file, flat_file
