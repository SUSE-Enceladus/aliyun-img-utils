# Overview

**aliyun-img-utils** provides a command line utility and API for publishing
images in the Aliyun Cloud. This includes helper functions for uploading
image blobs, creating compute images and replicating/publishing/deprecating/
images across all available regions.

See the [Alibaba docs](https://www.alibabacloud.com/getting-started) to get
more info on the Aliyun cloud.

# Requirements

- oss2
- Click
- PyYAML
- aliyun-python-sdk-core
- aliyun-python-sdk-ecs

# Installation

To install the package on openSUSE and SLES use the following commands as root:

```shell
$ zypper ar http://download.opensuse.org/repositories/Cloud:/Tools/<distribution>
$ zypper refresh
$ zypper in python3-aliyun-img-utils
```

To install from PyPI:

```shell
$ pip install aliyun-img-utils
```

# Configuration

**aliyun-img-utils** can be configured with yaml based profiles. The configuration
directory is `~/.config/aliyun_img_utils` and the default profile is default.yaml
(~/.config/aliyun_img_utils/default.yaml).

The following configration options are available in a configuration profile:

- no_color
- log_level
- region
- access_key
- access_secret
- bucket_name

An example configuration profile may look like:

```yaml
region: cn-beijing
access_key: FakeKEY
access_secret: FAKESecret
bucket_name: smarlow-testing
```

When running any command the profile can be chosen via the *--profile* option.
For example, *aliyun-img-utils image upload --profile production* would pull
configuration from ~/.config/aliyun_img_utils/production.yaml.

# CLI

The CLI is broken into multiple distinct subcommands that handle different
steps of creating and publishing images in the Aliyun cloud framework.

## Image blob upload

The first step is to upload a qcow2 image to a storage bucket. For this
*aliyun-img-utils image upload* is available.

Example:

```shell
$ aliyun-img-utils image upload --image-file ~/Documents/test.qcow2
```

In this example the qcow2 file will be uploaded to the storage bucket configured
for the given profile and the blob will be named test.qcow2. If you want to
override the name of the blob there is a *--blob-name* option.

For more information about the image upload function see the help message:

```shell
$ aliyun-img-utils image upload --help
```

## Compute image create

The next step is to create a compute image from the qcow2 blob. For this
*aliyun-img-utils image create* is available.

Example:

```shell
$ aliyun-img-utils image create --image-name SLES15-SP2-BYOS --image-description "Test image" --platform SUSE --blob-name SLES15-SP2-BYOS.qcow2
```

In this example the qcow2 blob will be used to create the compute image.
for the given profile and the blob will be named test.qcow2. If you want to
override the default (20GB) root disk size there is a *--disk-size* option.

For more information about the image create function see the help message:

```shell
$ aliyun-img-utils image create --help
```

## Replicate (copy) image

Once an image is created in a single region it can be replicated or copied to any other region: *aliyun-img-utils image replicate*.

Example:

```shell
$ aliyun-img-utils image replicate --image-name test-image-v20210303 --regions cn-shanghai
```

In this example the image will be replicated to the cn-shanghai region. If
no regions are provided the image will be replicated to all available regions.

For more information about the image replicate function see the help message:

```shell
$ aliyun-img-utils image replicate --help
```

## Publish image

The image can then be published or shared to other accounts with
*aliyun-img-utils image publish*.

Example:

```shell
$ aliyun-img-utils image publish --image-name test-image-v20210303 --launch-permission EXAMPLE
```

In this example the launch permission for the image will be set to *EXAMPLE*. If
no regions are provided the image will be published in all available regions.

For more information about the image publish function see the help message:

```shell
$ aliyun-img-utils image publish --help
```

## Deprecate image

An image can be set to the deprecated state with *aliyun-img-utils image deprecate*.

Example:

```shell
$ aliyun-img-utils image deprecate --image-name test-image-v20210303
```

As with the other commands, if no regions are provided the image will be deprecated
in all available regions.

For more information about the image deprecate function see the help message:

```shell
$ aliyun-img-utils image deprecate --help
```

## Activate image

An image can be set back to the active state with *aliyun-img-utils image activate*.

Example:

```shell
$ aliyun-img-utils image activate --image-name test-image-v20210303
```

As with the other commands, if no regions are provided the image will be activated
in all available regions.

For more information about the image activate function see the help message:

```shell
$ aliyun-img-utils image activate --help
```

## Get image info

Info about a specific compute image can be retrieved with
*aliyun-img-utils image info*.

Example:

```shell
$ aliyun-img-utils image info --image-name test-image-v20210303
```

The image can be searched by the *--image-name* or *--image-id*. By
default only active images will be searched. To filter deprecated images
there is a *--deprecated* option.

For more information about the image info function see the help message:

```shell
$ aliyun-img-utils image info --help
```

## Delete image

A compute image can be deleted with *aliyun-img-utils image delete*.

Example:

```shell
$ aliyun-img-utils image delete --image-name test-image-v20210303
```

As with the other commands, if no regions are provided the image will be
deleted in all available regions.

For more information about the image delete function see the help message:

```shell
$ aliyun-img-utils image delete --help
```

# API

The AliyunImage class can be instantiated and used as an API from code.
This provides all the same functions as the CLI with a few additional
helpers. For example there are waiter functions which will wait for
a compute image to be created and/or deleted.

To create an instance of AliyunImage you need an *access_key*,
*access_secret*, *region* and *bucket_name*. optionally you can pass
in a Python log object and/or a *log_level*.

```python
aliyun_image = AliyunImage(
    access_key,
    access_secret,
    region,
    bucket_name,
    log_level=log_level,
    log_callback=logger
)
```

## Code examples

With an instance of AliyunImage you can perform any of the image functions
which are available through the CLI.

```python
aliyun_image = AliyunImage(
    'accessKEY',
    'superSECRET',
    'cn-beijing',
    'images
)

# Upload image blob
blob_name = aliyun_image.upload_image_tarball('/path/to/image.qcow2')

# Create compute image
image_id = aliyun_image.create_compute_image(
    'test-image-v20220202',
    'A great image to use.',
    'test_image.qcow2',
    'SUSE'
)

# Delete compute image
# Deletes the image from the current region
deleted = aliyun_image.delete_compute_image('test-image-v20220202')

# Delete compute image in all available regions
aliyun_image.delete_compute_image_in_regions('test-image-v20220202')

# Delete storage blob from current bucket
deleted = aliyun_image.delete_storage_blob('test_image.qcow2')

# Copy image to a single region
image_id = aliyun_image.copy_compute_image(
    'test-image-v20220202',
    'cn-shanghai'
)

# Replicate (copy) image to all available regions
# A dictionary mapping region names to image ids is returned.
images = aliyun_image.replicate_image('test-image-v20220202')

# Publish image in current region
aliyun_image.publish_image('test-image-v20220202', 'EXAMPLE_PERMISSION')

# Publish image in all available regions
aliyun_image.publish_image_to_regions(
    'test-image-v20220202',
    'EXAMPLE_PERMISSION'
)

# Deprecate image in current region
aliyun_image.deprecate_image('test-image-v20220202')

# Deprecate image in all available regions
aliyun_image.deprecate_image_in_regions('test-image-v20220202')

# Activate image in current region
aliyun_image.activate_image('test-image-v20220202')

# Activate image in all available regions
aliyun_image.activate_image_in_regions('test-image-v20220202')

# Wait for image to become available based on image id
aliyun_image.wait_on_compute_image('i-123456789')

# Wait for image to be deleted based on image id
aliyun_image.wait_on_compute_image_delete('i-123456789')

# Return True if the image exists based on image name
exists = aliyun_image.image_exists('test-image-v20220202')

# 
exists = aliyun_image.image_tarball_exists('test_image.qcow2')

# Get image info as a dictionary
image_info = aliyun_image.get_compute_image(image_name='test_image.qcow2')

# Get a list of available regions
regions = aliyun_image.get_regions()
```

The current *region* or *bucket_name* can be changed at any time.

When the *bucket_name* is changed the current *bucket_client* session
is closed. The session will reconnect in a lazy fashion on the next
storage operation.

```python
aliyun_image = AliyunImage(
    'accessKEY',
    'superSECRET',
    'cn-beijing',
    'images
)
exists = aliyun_image.image_tarball_exists('test_image.qcow2')

# Resets the storage bucket client
aliyun_image.bucket_name = 'old-images'

# Storage bucket client connects to the new bucket lazily
exists = aliyun_image.image_tarball_exists('test_image.qcow2')
```

Similarly when the *region* is changed both the *bucket_client* and
the *compute_client* sessions are closed.

```python
aliyun_image = AliyunImage(
    'accessKEY',
    'superSECRET',
    'cn-beijing',
    'images
)
image_info = aliyun_image.get_compute_image(image_name='test_image.qcow2')

# Resets the compute client
aliyun_image.region = 'cn-shanghai'

# Compute client connects to the new region lazily
image_info = aliyun_image.get_compute_image(image_name='test_image.qcow2')
```

# Issues/Enhancements

Please submit issues and requests to
[Github](https://github.com/SUSE-Enceladus/aliyun-img-utils/issues).

# Contributing

Contributions to **aliyun-img-utils** are welcome and encouraged. See
[CONTRIBUTING](https://github.com/SUSE-Enceladus/aliyun-img-utils/blob/master/CONTRIBUTING.md)
for info on getting started.

# License

Copyright (c) 2021 SUSE LLC.

Distributed under the terms of GPL-3.0+ license, see
[LICENSE](https://github.com/SUSE-Enceladus/aliyun-img-utils/blob/master/LICENSE)
for details.
