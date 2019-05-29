from configparser import ConfigParser
import os
import logging
import time
from pywise import calframes, utils
from pywise.keywords import get_key_name, get_key_val
import ccdproc
import numpy as np
from astropy import units as u
import datetime

config = ConfigParser(inline_comment_prefixes=';')
config.read('config.ini')


def init_log(filename="log.log"):
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


def reduce_night(year=datetime.date.today().year, month=datetime.date.today().month, day=datetime.date.today().day, telescope="C28"):
    log = init_log(time.strftime("%Y%m%d_%H%M%S", time.gmtime()))

    t = datetime.date(year, month, day)
    t_str = datetime.date.strftime(t, format="%Y%m%d")

    im_path = config.get("GENERAL", "PATH") + config.get(telescope, "PATH") + t_str + config.get(telescope, "DIR_SUFFIX") + os.sep

    if not os.path.isdir(im_path):
        log.warning(f"Folder {im_path} doesn't exist!")
        return

    log.info(f"""Creating {telescope} master calibration frames for {t_str}...""")
    calframes.create_masters(year, month, day, telescope, log=log)

    imlist = ccdproc.ImageFileCollection(im_path, keywords='*')
    files = imlist.files_filtered(imagetyp="LIGHT")
    if len(files.tolist()) == 0:
        log.warning(f"No science frames in {t_str}.")
        return

    imlist = ccdproc.ImageFileCollection(im_path, keywords='*', filenames=files.tolist())

    save_uncertainty = config.getboolean("GENERAL", "SAVE_UNCERTAINTY")
    is_overwrite = config.getboolean("GENERAL", "OVERWRITE")

    instrument = imlist.values("instrume", True)[0]
    ccd_shape = utils.get_ccd_shape(imlist, telescope)

    reduced_path = im_path + config.get("GENERAL", "REDUCED_DIR") + os.sep
    # create reduced folder
    if not os.path.exists(reduced_path):
        os.makedirs(reduced_path)

    log.debug(f"""ccd_shape length {len(ccd_shape["x_naxis"])}""")
    for i in range(len(ccd_shape["x_naxis"])):
        ccd_set = utils.get_set_from_dict(ccd_shape, i)
        ccd_str = utils.get_ccd_str(ccd_shape, idx=i)
        filters = np.unique(imlist.summary["filter"])
        log.debug(f"{filters}")
        for filt in filters:
            bias_file, dark_file, flat_file = calframes.get_calframes(year, month, day, filt, ccd_str, telescope=telescope, instrument=instrument, log=log)
            if (not bias_file) or (not dark_file) or (not flat_file):
                log.warning(f"No calibration frames found, skipping.")
                continue

            bias = ccdproc.CCDData.read(bias_file)
            dark = ccdproc.CCDData.read(dark_file)
            flat = ccdproc.CCDData.read(flat_file)

            kwargs = dict()
            kwargs[get_key_name("image_type", telescope)] = get_key_val("light", telescope)
            kwargs[get_key_name("filter", telescope)] = filt
            kwargs[get_key_name("x_naxis", telescope)] = ccd_set["x_naxis"]
            kwargs[get_key_name("y_naxis", telescope)] = ccd_set["y_naxis"]
            kwargs[get_key_name("x_subframe", telescope)] = ccd_set["x_subframe"]
            kwargs[get_key_name("y_subframe", telescope)] = ccd_set["y_subframe"]
            kwargs[get_key_name("x_bin", telescope)] = ccd_set["x_bin"]
            kwargs[get_key_name("y_bin", telescope)] = ccd_set["y_bin"]

            for im, filename in imlist.hdus(return_fname=True, **kwargs):
                log.debug(f"{filename}")

                obj = im.header[get_key_name("object", telescope)]
                jd = str(im.header[get_key_name("jd", telescope)]).replace(".", "_")
                filename = f"{obj}_{jd}_{filt}_{telescope}"

                file_exists = os.path.isfile(reduced_path + filename + ".fits")
                if (not file_exists) | (file_exists & is_overwrite):
                    im.data = im.data.astype("float32")
                    im = ccdproc.subtract_bias(ccdproc.CCDData(data=im.data, unit=u.adu, header=im.header), bias,
                                               add_keyword=ccdproc.Keyword("DEBIAS", value=bias_file.split(os.sep)[-1]))
                    im = ccdproc.subtract_dark(im, dark, exposure_time=get_key_name("exptime", telescope), exposure_unit=u.s,
                                               scale=True, add_keyword=ccdproc.Keyword("DEDARK", value=dark_file.split(os.sep)[-1]))
                    im = ccdproc.flat_correct(im, flat, add_keyword=ccdproc.Keyword("DEFLAT", value=flat_file.split(os.sep)[-1]))
                    if not save_uncertainty:
                        im.uncertainty = None
                        im.mask = None
                    im.data = im.data.astype('float32')
                    im.write(reduced_path + filename + ".fits", overwrite=True)

    close_log(log)

    return
