#!/bin/bash
set -e
# Use the Unbranded build that corresponds to a specific Firefox version
# To upgrade:
#    1. Go to: https://hg.mozilla.org/releases/mozilla-release/tags.
#    2. Find the commit hash for the Firefox release version you'd like to upgrade to.
#    3. Update the `TAG` variable below to that hash.

# Note this script is **destructive** and will
# remove the existing Firefox in the OpenWPM directory

TAG='8b7f7fd1873f56a4d755ea1fdcf46cbb18f9af27' # FIREFOX_121_0_RELEASE


case "$(uname -s)" in
   Darwin)
     echo 'Your OS is not supported. Aborting'
     exit 1
     ;;
   Linux)
     rm -rf firefox-bin
     tar jxf firefox-bin.tar.bz2
     ;;
esac

echo 'Firefox succesfully installed'


