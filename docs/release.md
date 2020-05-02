# Release Instructions

This list is supposed to make sure we do not forget any important steps during
release.

1. Check and update issue tracker for issues associated with current milestone

2. Make sure all desired changes are merged with `master`.

3. Create release-prep branch and update CHANGELOG.md with all elements missing

4. Prepare a release on GitHub with: https://github.com/smarr/ReBench/releases/new
   The content is normally just the last part of the CHANGELOG.md

5. Bump the version https://github.com/smarr/ReBench/blob/master/rebench/__init__.py

6. Push the branch, let CI test a last time

7. If everything looks good, merge, and tag the release using the GitHub feature
   If GitHub actions works correctly, it will publish the release on pip.
