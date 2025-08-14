### Author: Loran Knol

Scripts to pull and parse BiAffect data from the Synapse servers.

## Reading material

Some sources to orient yourself. No need to read everything in these sources, just as far as you find useful.

- Synapse client tutorials: https://python-docs.synapse.org/en/stable/tutorials/home/
- Pandas User Guide: https://pandas.pydata.org/docs/user_guide/index.html
- Tips on how to do good Python documentation: https://realpython.com/documenting-python-code
- Optional: Numpy User Guide (I'd just look at some of the fundamentals so you understand indexing with numpy arrays): https://numpy.org/doc/stable/user/index.html
- Optional: If you want to do actual analysis, you can find some R scripts on the [Github repo](https://github.com/Valkje/clear3-ica) associated with my first paper. For now I'd just leave that for later, though :)

## Requirements

I used Python 3.10.15. Other versions might work equally fine, though.

You will need these Python packages: `tqdm pandas synapseclient`.
`synapseclient` is only available via pip.

## Pull scripts

`pull.py` and `parse.py` form a pair that allow you to get the data for a subset of the participants using their health codes. To make the selection quickly, `pull.py` makes use of a Synapse File View, which essentially gives an overview of all BiAffect files in the Test Study Project ucMft. You will need download access to both the File View and the Test Study Project to be able to make use of this script. Alternatively, you could create your own File View on Synapse. After this, `pull.py` downloads the data and creates a file `hc_df.parquet` that specifies which file belongs to which health code (participant).

`parse.py` then parses this data into two Pandas data frames, one for all the key presses and one for the accelerometer data. The frames are saved to `dat_kp.parquet` and `dat_acc.parquet`, respectively.

Because the BiAffect data consists of so many small files, `pull.py` can be a bit inefficient in terms of download speed. `pull_all.py` sacrifices local storage for a more efficient downloading procedure, which means you pull the entire Test Study Project (at the time of writing, 7 Feb 2025, about 4GB). It also saves a pickle file called `entities.pkl`, which is a large (>100MB) list of metadata about all the project files (i.e., the list consists of Synapse [`File`](https://python-docs.synapse.org/reference/file/) objects), including their health codes.

The parsing counterpart to `pull_all.py` has not been fully fleshed out, but usable code can be found in `parse_selectively.ipynb`. It uses some of the functions found in `parse.py`. 

## Preprocessing scripts

I added the R preprocessing script I used for Alex's data, `preproc_alex.R`. Note that this specific script might not work for any of the BiAffect data collected before BiAffect 3 – let me know if you'd like to have that version too. For BiAffect 3, it should pretty much be plug and play.

To use the script, install the following dependencies:

```r
install.packages(c(
  "gsignal",
  "dplyr",
  "stringr",
  "lubridate"
))
```

I also recommend installing `arrow` so you can read and write parquet files:

```r
install.packages("arrow")
```

(On Windows and Mac this is pretty quick, but on Linux it takes about a million years. Check out the [install page](https://arrow.apache.org/docs/r/articles/install.html) if you want to speed things up.)

Then you can use the script's functions like so:

```r
library(arrow)

source("preproc_alex.R")

# Read data
raw_acc <- read_parquet("path/to/raw_acc.parquet")
raw_kp <- read_parquet("path/to/raw_kp.parquet")

# Preprocess accelerometer data
dat_acc <- preproc_acc(raw_acc)

# Preprocess key press data
ls <- preproc_kp(raw_kp, dat_acc)
dat_kp <- ls$dat_kp # Key-press-level data
dat_ses <- ls$dat_ses # Session-level data

# Write preprocessed data to file
write_parquet(dat_acc, "path/to/dat_acc.parquet")
write_parquet(dat_kp, "path/to/dat_kp.parquet")
write_parquet(dat_ses, "path/to/dat_ses.parquet")
```

## Recommendations

`pull.py` is most useful if you only want to pull a small amount of data. Otherwise, I recommend using `pull_all.py`. The initial pull might be very time-consuming (in my case, where I had to pull everything to a European server, several hours), but subsequent pulls will be much faster. You might also want to unify `parse.py` and `parse_selectively.ipynb`. `parse.py` contains useful parsing functions but as a standalone script it currently does not work with the `entities.pkl` file produced by `pull_all.py`. `parse_selectively.ipynb` does have that capability, but it would be good to convert that to a plain Python script to make it more accessible to those not working with Jupyter Notebooks.

In all of this, userfriendliness is most crucial to the rest of the BiAffect team, so pay attention to [good commenting and documentation](https://realpython.com/documenting-python-code). You might find Python's [argparse](https://docs.python.org/3/library/argparse.html) module helpful in designing the scripts' command line argument interfaces.

Adjacent to this, while creating pulling and parsing scripts you might be making some assumptions about the structure of the data and what different file annotations mean (more on those below). Make sure to write down those assumptions and make them available with the code documentation. You could even go one step further and write tests that raise a warning or throw an error when your assumptions are violated. Making mistakes is natural, but if something is wrong with processing, we'd still rather find out as early as possible!

## Caveats

Some of the things I ran into while writing these scripts:
- Synapse files have bits of metadata called _annotations_ attached to them. These annotations are crucial to determine, among other things, the participant health code (i.e., their ID). However, they can also be misleading. For example, the `createdOn` annotation seems to refer to when a file was uploaded to Synapse, and **not** to when that file was created by BiAffect on the participant device. Similarly, the date folder a file is in does not mean that the file's session was also recorded on that day. This means that making a selection of files for parsing based on any of the date annotations could lead to missing some data.
- There have been periods in the past where some BiAffect sessions were uploaded twice. This means that there are files with the same name, but stored in different (date) folders. When parsing, make sure to keep only one of those copies, because otherwise this could lead to duplicate data entries that could affect downstream analyses.
