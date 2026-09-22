# User hooks for ``zfr package`` upload/publish.
#
# Copy any of these into ``~/.config/zfr/scripts/``, ``chmod +x``, and edit.
# Missing hooks produce a warning from ``zfr package`` when that kind was built.
#
# Expected names:
#   upload_deb / publish_deb
#   upload_rpm / publish_rpm
#   upload_npm / publish_npm
#   upload_vsix / publish_vsix
#
# Local defaults in this directory:
#   upload_deb  → dput -f s1   (repodeb_aptly incoming)
#   upload_rpm  → curl PUT to reporpm_createrepo-c
#   publish_rpm → curl /rescan?sync=1
