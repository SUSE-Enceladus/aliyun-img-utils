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
