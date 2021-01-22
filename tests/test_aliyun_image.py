#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Aliyun img utils class tests."""

# Copyright (c) 2021 SUSE LLC. All rights reserved.
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

import oss2

from unittest.mock import patch, Mock

from pytest import raises

from aliyun_img_utils.aliyun_image import AliyunImage
from aliyun_img_utils.aliyun_exceptions import (
    AliyunException,
    AliyunImageUploadException
)


class TestAliyunImage(object):
    """Test Aliyun Image class."""

    def setup(self):
        self.image = AliyunImage(
            '12345',
            '54321',
            'cn-beijing',
            bucket_name='test-bucket'
        )

    @patch('aliyun_img_utils.aliyun_image.get_storage_auth')
    @patch('aliyun_img_utils.aliyun_image.get_storage_bucket_client')
    def test_bucket_client(self, mock_bucket_client, mock_storage_auth):
        client = Mock()
        mock_bucket_client.return_value = client
        assert self.image.bucket_client

        # Server Error
        client.get_bucket_info.side_effect = oss2.exceptions.ServerError(
            'Failed', Mock(), Mock(), {'Message': 'Failed'}
        )
        self.image._bucket_client = None

        with raises(AliyunException):
            assert self.image.bucket_client

        # Request Error
        client.get_bucket_info.side_effect = oss2.exceptions.RequestError(
            'Failed'
        )
        self.image._bucket_client = None

        with raises(AliyunException):
            assert self.image.bucket_client

        # Exception
        client.get_bucket_info.side_effect = Exception('Failed')
        self.image._bucket_client = None

        with raises(AliyunException):
            assert self.image.bucket_client

    def test_image_exists(self):
        client = Mock()
        self.image._bucket_client = client
        assert self.image.image_exists('blob.vhd')

        # Not exists
        client.get_object_meta.side_effect = oss2.exceptions.NoSuchKey(
            {}, {}, {}, {}
        )
        assert self.image.image_exists('blob.vhd') is False

    def test_delete_image_tarball(self):
        client = Mock()
        response = Mock()
        response.status = 200
        client.delete_object.return_value = response
        self.image._bucket_client = client

        assert self.image.delete_image_tarball('blob.vhd')

        # Not exists
        response.status = 204
        assert self.image.delete_image_tarball('blob.vhd') is False

    @patch('aliyun_img_utils.aliyun_image.put_blob')
    def test_upload_image_tarball(self, mock_put_blob):
        callback = Mock()
        client = Mock()
        self.image._bucket_client = client

        assert self.image.upload_image_tarball(
            'tests/data/blob.vhd',
            page_size=8 * 8 * 1024,
            progress_callback=callback,
            force_replace_image=True
        )

        # File Not Found
        mock_put_blob.side_effect = FileNotFoundError('Not there!')
        with raises(AliyunImageUploadException):
            self.image.upload_image_tarball(
                'tests/data/blob.vhd',
                page_size=8 * 8 * 1024,
                progress_callback=callback,
                force_replace_image=True
            )

        # Server Error
        mock_put_blob.side_effect = oss2.exceptions.ServerError(
            'Failed', {}, {}, {'Message': 'Failed'}
        )
        with raises(AliyunImageUploadException):
            self.image.upload_image_tarball(
                'tests/data/blob.vhd',
                page_size=8 * 8 * 1024,
                progress_callback=callback,
                force_replace_image=True
            )

        # Request Error
        mock_put_blob.side_effect = oss2.exceptions.RequestError(
            'Failed'
        )
        with raises(AliyunImageUploadException):
            self.image.upload_image_tarball(
                'tests/data/blob.vhd',
                page_size=8 * 8 * 1024,
                progress_callback=callback,
                force_replace_image=True
            )

        # Request Error
        mock_put_blob.side_effect = Exception('Failed')
        with raises(AliyunImageUploadException):
            self.image.upload_image_tarball(
                'tests/data/blob.vhd',
                page_size=8 * 8 * 1024,
                progress_callback=callback,
                force_replace_image=True
            )
