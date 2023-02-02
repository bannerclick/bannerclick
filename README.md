
BannerClick
=======

BannerClick is a web privacy measurement tool that is built on top of [OpenWPM](https://github.com/openwpm/OpenWPM).
It is designed to detect and interact with cookie banners.
For more details on how BannerClick works please check out [this paper]().


Installation
------------

We implemented BannerClick as a [custom command](https://github.com/openwpm/OpenWPM/blob/master/custom_command.py) in OpenWPM. Therefore, to run BannerClick first you need to install OpenWPM as follows.

The main pre-requisite for OpenWPM is conda. it is an open-source cross-platform package management tool, and can be installed from https://docs.conda.io/en/latest/miniconda.html.


Next, the `install.sh` script will install all the prerequisites in a separate conda environment named openwpm. Note that we customized `install.sh` to install the Firefox binary using the local `firefox-bin.tar.bz2` file instead of downloading it from the server (as Firefox 95 is not available for download anymore).
. To run the install script, run

```bash
./install.sh
```

After running the install script, activate your conda environment by running:

```bash
conda activate openwpm
```

Quick Start
-----------

Running BannerClick is the same as OpenWPM. Check out
[`demo.py`](https://github.com/bannerclick/bannerclick/blob/bannerclick_v0.18.0/demo.py) for an example. This will use the default setting specified in
[`openwpm/config.py::ManagerParams`](https://github.com/bannerclick/bannerclick/blob/bannerclick_v0.18.0/openwpm/config.py#L110) and
[`openwpm/config.py::BrowserParams`](https://github.com/bannerclick/bannerclick/blob/bannerclick_v0.18.0/openwpm/config.py#L71), with the exception of the changes
specified in `demo.py`. As an example the following command will run the bannerclick custom command using 8 headless browsers with 5 repetitions for each domain in the `Tranco5Nov.csv` file.

```bash 
python demo.py --bannerclick --headless --num-browsers 8 --num-repetitions 5 ./bannerclick/input-files/Tranco5Nov.csv
```

Note that it is also possible to run BannerClick as an independent module from OpenWPM. To do this please take a look at the instructions [here](https://github.com/bannerclick/bannerclick/tree/bannerclick_v0.18.0/bannerclick#banner-detection-package).

Configuration
-----------

Aside from the [configuration](https://github.com/openwpm/OpenWPM/blob/master/docs/Configuration.md) for OpenWPM, there are other parameters that can be modified in [`config.py`](https://github.com/bannerclick/bannerclick/blob/bannerclick_v0.18.0/bannerclick/config.py) to configure BannerClick. Each parameter is documented in the file directly. For example, `MOBILE_AGENT` can be set to simulate a mobile agent.
