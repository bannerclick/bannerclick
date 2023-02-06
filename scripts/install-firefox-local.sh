#!/bin/bash
set -e
# Use the Unbranded build that corresponds to a specific Firefox version
# To upgrade:
#    1. Go to: https://hg.mozilla.org/releases/mozilla-release/tags.
#    2. Find the commit hash for the Firefox release version you'd like to upgrade to.
#    3. Update the `TAG` variable below to that hash.

# Note this script is **destructive** and will
# remove the existing Firefox in the OpenWPM directory

TAG='5a1a2f3b06c23a27532ba48f9999c59c643f3f36' # FIREFOX_95_0_RELEASE


case "$(uname -s)" in
   Darwin)
     echo 'Your OS is not supported. Aborting'
     exit 1
     ;;
   Linux)
     tar jxf firefox-bin.tar.bz2
     rm -rf firefox-bin
     mv firefox firefox-bin
     ;;
esac

echo 'Firefox succesfully installed'
