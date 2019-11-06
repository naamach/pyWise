import os
import time
from pywise import calframes, utils
from pywise.keywords import get_key_name, get_key_val
import ccdproc
import numpy as np
from astropy import units as u
import datetime
from pywise.utils import get_config, init_log, close_log, daterange


def reduce_night(year=datetime.date.today().year, month=datetime.date.today().month, day=datetime.date.today().day,
                 telescope="C28", config_file="config.ini"):
    config = get_config(config_file)
    log = init_log(time.strftime("%Y%m%d_%H%M%S", time.gmtime()), config_file)

    t = datetime.date(year, month, day)
    t_str = datetime.date.strftime(t, format="%Y%m%d")

    im_path = config.get("GENERAL", "PATH") + config.get(telescope, "PATH") + t_str + config.get(telescope, "DIR_SUFFIX") + os.sep

    if not os.path.isdir(im_path):
        log.warning(f"Folder {im_path} doesn't exist!")
        return

    log.info(f"""Creating {telescope} master calibration frames for {t_str}...""")
    calframes.create_masters(year, month, day, telescope, log=log, config_file=config_file)

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
            bias_file, dark_file, flat_file = calframes.get_calframes(year, month, day, filt, ccd_str, telescope=telescope,
                                                                      instrument=instrument, log=log, config_file=config_file)
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
                jd = im.header[get_key_name("jd", telescope)]*u.day
                # fix JD for RBI flood delay (C28):
                if telescope == "C28":
                    if im.header[get_key_name("readout", telescope)] == get_key_val("rbi", telescope):
                        jd = jd + get_key_val("rbi_delay", telescope)
                        im.header[get_key_name("jd", telescope)] = jd.to_value()
                        im.header[get_key_name("rbi_delay", telescope)] = "TRUE"
                        im.header.comments[get_key_name("rbi_delay", telescope)] = f"""Corrected JD by {get_key_val("rbi_delay", telescope)} of RBI flood delay."""
                        log.warning(f"""Corrected RBI flood delay of {get_key_val("rbi_delay", telescope)}.""")

                jd = str(jd.to_value()).replace(".", "_")
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


def reduce_nights(d1, d2, telescope="C28", config_file="config.ini"):
    """
    d1 and d2 should be in the format "YYYYMMDD"
    """
    d1 = datetime.datetime.strptime(d1, "%Y%m%d")
    d2 = datetime.datetime.strptime(d2, "%Y%m%d")
    for day in daterange(d1, d2):
        print(day)
        reduce_night(day.year, day.month, day.day, telescope, config_file=config_file)

    return
