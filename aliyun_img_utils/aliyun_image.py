# -*- coding: utf-8 -*-

"""Aliyun image class module."""

# Copyright (c) 2020 SUSE LLC. All rights reserved.
#
# This file is part of aliyun_img_utils. aliyun_img_utils provides an
# api and command line utilities for handling images in the Aliyun Cloud.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import os

import oss2

from aliyun_img_utils.aliyun_exceptions import (
    AliyunException,
    AliyunImageUploadException
)
from aliyun_img_utils.aliyun_utils import (
    get_storage_auth,
    get_storage_bucket_client,
    put_blob
)


class AliyunImage(object):
    """
    Provides methods for handling compute images in Alibaba (Aliyun).
    """

    def __init__(
        self,
        access_key,
        access_secret,
        region,
        bucket_name=None,
        log_level=logging.INFO,
        log_callback=None
    ):
        """Initialize class and setup logging."""
        self.access_key = access_key
        self.access_secret = access_secret
        self._region = region
        self._bucket_name = bucket_name
        self._bucket_client = None

        if log_callback:
            self.log = log_callback
        else:
            self.log = logging.getLogger('aliyun-img-utils')
            self.log.setLevel(log_level)

        try:
            self.log_level = self.log.level
        except AttributeError:
            self.log_level = self.log.logger.level  # LoggerAdapter

    def image_exists(self, blob_name):
        """Return True if image exists in the configured bucket."""
        try:
            self.bucket_client.get_object_meta(blob_name)
        except oss2.exceptions.NoSuchKey:
            return False

        return True

    def delete_image_tarball(self, blob_name):
        """Delete blob if it exists in the configured bucket."""
        response = self.bucket_client.delete_object(blob_name)

        if response.status == 204:
            self.log.debug(
                'Blob {blob_name} not found. '
                'Nothing has been deleted.'.format(
                    blob_name=blob_name
                )
            )
            return False

        return True

    def upload_image_tarball(
        self,
        image_file,
        page_size=None,
        progress_callback=None,
        blob_name=None,
        force_replace_image=False
    ):
        """
        Upload image tarball to the configured bucket.

        Uses multipart upload and will generate blob name
        based on image file path if a name is not provided.
        """
        if not blob_name:
            blob_name = image_file.rsplit(os.sep, maxsplit=1)[-1]

        if self.image_exists(blob_name) and not force_replace_image:
            raise AliyunImageUploadException(
                'Image {blob_name} already exists. To replace an existing '
                'image use force_replace_image option.'.format(
                    blob_name=blob_name
                )
            )
        elif self.image_exists(blob_name) and force_replace_image:
            self.delete_image_tarball(blob_name)

        kwargs = {}

        if page_size:
            kwargs['page_size'] = page_size

        if progress_callback:
            kwargs['progress_callback'] = progress_callback

        try:
            put_blob(self.bucket_client, blob_name, image_file, **kwargs)
        except FileNotFoundError:
            raise AliyunImageUploadException(
                'Image file {image_file} not found. Ensure the path to'
                ' the file is correct.'.format(image_file=image_file)
            )
        except oss2.exceptions.ServerError as error:
            raise AliyunImageUploadException(
                'Unable to upload image: {error}'.format(
                    error=str(error.details['Message'])
                )
            )
        except oss2.exceptions.RequestError:
            raise AliyunImageUploadException(
                'Unable to upload image: Failed to establish a new '
                'connection.'
            )
        except Exception as error:
            raise AliyunImageUploadException(
                'Unable to upload image: {error}'.format(
                    error=str(error)
                )
            )

        return blob_name

    @property
    def bucket_client(self):
        """
        Bucket client property

        Lazy bucket client initialization. Attempts to collect
        bucket info to ensure valid auth before usage.
        """
        if not self.bucket_name:
            raise AliyunException(
                'Image storage methods require a configured bucket name.'
            )

        if not self._bucket_client:
            auth = get_storage_auth(self.access_key, self.access_secret)
            self._bucket_client = get_storage_bucket_client(
                auth,
                self.bucket_name,
                self.region
            )

            try:
                self._bucket_client.get_bucket_info()  # Force eager auth
            except oss2.exceptions.ServerError as error:
                raise AliyunException(
                    'Unable to get bucket client: {error}'.format(
                        error=str(error.details['Message'])
                    )
                )
            except oss2.exceptions.RequestError:
                raise AliyunException(
                    'Unable to get bucket client: Failed to establish a new '
                    'connection. Ensure the bucket name and region are '
                    'correct.'
                )
            except Exception as error:
                raise AliyunException(
                    'Unable to get bucket client: {error}'.format(
                        error=str(error)
                    )
                )

        return self._bucket_client

    @property
    def bucket_name(self):
        """Bucket name property."""
        return self._bucket_name

    @bucket_name.setter
    def bucket_name(self, name):
        """Setter for bucket name."""
        self._bucket_name = name

    @property
    def region(self):
        """Region property."""
        return self._region

    @region.setter
    def region(self, region_name):
        """Setter for region."""
        self._region = region_name
