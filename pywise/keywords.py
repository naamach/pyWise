def get_key_name(key, telescope):
    meter = {
        "ra": "RA",
        "dec": "DEC",
        "exptime": "EXPTIME",
        "filter": "FILTER",
        "image_type": "IMAGETYP",
        "light": ["LightFrame", "SCIENCE"],
        "jd": ["JD", "JUL-DATE"],
        "object": "OBJECT",
        "airmass": "AIRMASS",
        "naxis": "NAXIS",
        "x_naxis": "NAXIS1",
        "y_naxis": "NAXIS2",
        "x_bin": "XBINNING",
        "y_bin": "YBINNING",
        "temperature": ["CCD-TEMP", "TEMP1"],
        "telescope": "TELESCOP",
        "instrument": "INSTRUME",
        "gain": "EGAIN",
        "readout_noise": "RDNOISE",
        "flip": "FLIPSTAT",
        "x_subframe": "XORGSUBF",
        "y_subframe": "YORGSUBF",
        "epoch": "EPOCH",
        "ccdsec": "CCDSEC"  # laiwo
    }

    c28 = {
        "ra": "RA",
        "dec": "DEC",
        "exptime": "EXPTIME",
        "readout": "READOUTM",  # 8 MHz (RBI Flood)
        "filter": "FILTER",
        "image_type": "IMAGETYP",
        "light": "LIGHT",
        "jd": "JD",
        "object": "OBJECT",
        "airmass": "AIRMASS",
        "naxis": "NAXIS",
        "x_naxis": "NAXIS1",
        "y_naxis": "NAXIS2",
        "x_bin": "XBINNING",
        "y_bin": "YBINNING",
        "temperature": "CCD-TEMP",
        "telescope": "TELESCOP",
        "instrument": "INSTRUME",
        "gain": "GAIN",
        "readout_noise": "RDNOISE",
        "flip": "FLIPSTAT",
        "x_subframe": "XORGSUBF",
        "y_subframe": "YORGSUBF",
    }

    keys = {
        "1m": meter,
        "C28": c28,
    }

    return keys[telescope][key]


def get_key_val(val, telescope):
    meter = {
        "light": ["LightFrame", "SCIENCE"]
    }

    c28 = {
        "rbi": "8 MHz (RBI Flood)",
        "light": "LIGHT"
    }

    vals = {
        "1m": meter,
        "C28": c28,
    }

    return vals[telescope][val]
