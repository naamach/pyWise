# pyWise

Image reduction pipeline for the Wise Observatory.

## Getting started

### Prerequisites

* `python 3.6` or above
* `astropy`
* `configparser`
* `ccdproc`
* `numpy`

### Installing

Create and activate a `conda` environment with the necessary modules:
```
$ conda create -n wise astropy configparser ccdproc numpy python=3.7.1
$ source activate wise
```
Install the `pyWise` package:
```
$ pip install git+https://github.com/naamach/pywise.git
```

### Upgrading
To upgrade `pyWise` run:
```
$ pip install git+https://github.com/naamach/pywise.git --upgrade
```

### The configuration file

Finally, you will have to provide `pyWise` with the configuration file.
To do so, you will need to have a `config.ini` file in the working directory (the directory from which you run the script).
The file should look like that (see `config.ini.example` in the main directory):

```
; config.ini
[LOG]
PATH = /path/to/log/
CONSOLE_LEVEL = INFO ; DEBUG, INFO, WARNING, ERROR, CRITICAL
FILE_LEVEL = DEBUG ; DEBUG, INFO, WARNING, ERROR, CRITICAL

[GENERAL]
PATH = /path/to/images/
SAVE_UNCERTAINTY = False ; True - save uncertainty to FITS file
OVERWRITE = True ; True - overwrite previously-reduced frames
REDUCED_DIR = reduced ; reduced subfolder name

[CAL]
MAX_DAY_SHIFT = 14 ; maximal number of days away to look for missing calibration frames
PATH = /path/to/calibration_frames/  ; calibration frame archive
OVERWRITE = False ; True - overwrite previously-created master calibration frames
MAX_NUM_FRAMES = -1 ; maximal number of frames to combine (to solve memory problems; has to be an integer, -1 = unlimited)

[C28]
PATH = C28backup/ ; C28 subfolder name
DIR_SUFFIX = c28  ; nightly folder name suffix

[C18]
PATH = C18backup/ ; C18 subfolder name
DIR_SUFFIX = c18  ; nightly folder name suffix
```

## Using `pyWise`

### Copying the images

First, you need to download the images from `mizpe-bck`, and save them locally to the folder defined in the `PATH` parameter under `GENERAL` in the `config.ini` file.
`pyWise` assumes a folder hierarchy similar to that of `mizpe-bck`, where there is a separate folder for each night for each telescope:

```
mizpe-bck
   |
   |-----20190531
   |-----20190601
   |
   |-----C18backup
            |
            |-----20190531c18
	    |-----20190601c18
   |
   |-----C28backup
            |
            |-----20190531c28
	    |-----20190601c28

```
You should copy the relevant nightly folder to your computer using a similar structure.

### Directly from `python`

To reduce, for example, the images taken by the C28 telescope on 2019 May 29, run:

```
from pywise import wise
wise.reduce_night(2019, 5, 29, "C28")
```

### Using the `wise_reduce` command

To reduce, for example, the images taken by the C28 telescope on 2019 May 29, run in the terminal, while the relevant python environment is activated:

```
$ wise_reduce -f 20190529 C28
```

This is assuming the `config.ini` file is in the current folder. Otherwise you can specify the path to the config file:

```
$ wise_reduce -f 20190529 -c /path/to/config.ini C28
```

To reduce all the images taken by the C28 between 2019 May 29 and May 30, run:

```
$ wise_reduce -f 20190529 -t 20190530 -c /path/to/config.ini C28
```

General usage:

```
usage: wise_reduce [-h] -f YYYYMMDD [-t YYYYMMDD] [-c config_file]
                   {1m,C28,C18}

Reduce Wise Observatory images.

positional arguments:
  {1m,C28,C18}          telescope

optional arguments:
  -h, --help            show this help message and exit
  -f YYYYMMDD, --from YYYYMMDD
                        date to reduce
  -t YYYYMMDD, --to YYYYMMDD
                        optional second date to define a date range to reduce
  -c config_file, --config config_file
                        path to config.ini file (default: config.ini)
```

## Outline of `pywise.wise.reduce_night`

1. Get a list of images from the date and telescope requested (the path to the image folder is defined in the `config.ini` file).
1. Create master calibration frames (bias, dark, flat) for this night (if raw calibration frames exist), and save them to the calibration frame archive (defined in `config.ini`). The function takes into account the telescope, instrument, binning, subframe, and filter used.
1. For each science image, find the nearest available relevant calibration frames, subtract bias, subtract dark, and correct flat field.
1. Save the reduced image to the reduced image subfolder, in the format `<object>_<JD>_<filter>_<telescope>.fits`.
