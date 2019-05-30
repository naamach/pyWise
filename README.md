# pyWise

Image reduction pipeline for the Wise Observatory.

## Getting started

### Prerequisites

* `python 2.7` or above
* `lxml`
* `configparser`

### Installing

Create and activate a `conda` environment with the necessary modules:
```
$ conda create -n wise lxml configparser
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

To reduce all the images taken by the C28 between 2019 May 29 and May 30, run:

```
$ wise_reduce -f 20190529 -t 20190530 C28
```

General usage:

```
usage: wise_reduce [-h] -f YYYYMMDD [-t YYYYMMDD] {1m,C28,C18}

Reduce Wise Observatory images.

positional arguments:
  {1m,C28,C18}          telescope

optional arguments:
  -h, --help            show this help message and exit
  -f YYYYMMDD, --from YYYYMMDD
                        date to reduce
  -t YYYYMMDD, --to YYYYMMDD
                        optional second date to define a date range to reduce

```

