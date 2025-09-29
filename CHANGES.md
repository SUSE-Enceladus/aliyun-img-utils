v2.5.0 (2025-09-29)
===================

- Add obs publish github workflow
- Includes a new flag to add nvme support for image create operations
- Fixes possible undefined variable access

v2.4.0 (2025-05-19)
===================

- Add man pages to repo

v2.3.0 (2025-05-16)
===================

- Update spec to build for one version of python
- Add new man page to spec

v2.2.0 (2024-05-28)
===================

- Increase the timeout for wait on image method
- Remove superfluous delete blob option
- Add endpoint for retrieving image share permission
- Update python versions for ci testing
- Migrate spec file to build for python 3.11

v2.1.0 (2022-05-25)
===================

- Consistant error handling in class methods
- Sanitize all HttpErrors

v2.0.0 (2022-02-09)
===================

- Fix delete image bug
- Handle image state flow when waiting for image to be available
- Add a longer wait timeout and make it configurable
- Add available states to the image class
- Search on all states by default when retrieving compute image

Breaking changes

- `--status` replaces `--deprecated` in the image info endpoint

v1.8.0 (2022-01-04)
===================

- Bump the connection timeout for compute client to 180 seconds.

v1.7.1 (2021-12-17)
===================

- Add rpm-macros to build requirements in spec.

v1.7.0 (2021-12-10)
===================

- Log the correct region name when copying image
- Handle KeyError when getting image info

v1.6.0 (2021-10-12)
===================

- Revert deprecation changes
- Image remains available and shared on deprecation. Only the
  deprecation tags are added to the image.

v1.5.0 (2021-10-11)
===================

- Un-share image before deprecation.
- Fix copy image log message.
- Add wait on blob method after upload finishes.

v1.4.0 (2021-07-21)
===================

- Add tags to image during deprecation.

v1.3.0 (2021-07-02)
===================

- Add functions for handing ssh key pairs.

v1.2.0 (2021-06-22)
===================

- Add timeout and accelerated transfer options. 

v1.1.0 (2021-04-07)
===================

- Better handle optional delete of oss blob.
- Add force delete option.
- Add helper method for deleting compute image.
- Cleanup and expand readme with examples.

v1.0.0 (2021-03-15)
===================

- Add functions for replicate, publish and deprecate.

v0.1.0 (2021-03-10)
===================

- Add compute image create and delete functions.
- Rename tarball exists method to be explicit.
- Fix upload progress bar and callback.
- Use f strings.

v0.0.1 (2020-12-02)
===================

- Initial release
