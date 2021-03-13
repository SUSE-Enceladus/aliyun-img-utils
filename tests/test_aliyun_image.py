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

import json
import oss2

from unittest.mock import patch, Mock

from pytest import raises

from aliyun_img_utils.aliyun_image import AliyunImage
from aliyun_img_utils.aliyun_exceptions import (
    AliyunException,
    AliyunImageException,
    AliyunImageCreateException,
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

    def test_image_tarball_exists(self):
        client = Mock()
        self.image._bucket_client = client
        assert self.image.image_tarball_exists('blob.qcow2')

        # Not exists
        client.get_object_meta.side_effect = oss2.exceptions.NoSuchKey(
            {}, {}, {}, {}
        )
        assert self.image.image_tarball_exists('blob.qcow2') is False

    def test_delete_image_tarball(self):
        client = Mock()
        response = Mock()
        response.status = 200
        client.delete_object.return_value = response
        self.image._bucket_client = client

        assert self.image.delete_storage_blob('blob.qcow2')

        # Not exists
        response.status = 204
        assert self.image.delete_storage_blob('blob.qcow2') is False

    @patch('aliyun_img_utils.aliyun_image.put_blob')
    def test_upload_image_tarball(self, mock_put_blob):
        callback = Mock()
        client = Mock()
        self.image._bucket_client = client

        assert self.image.upload_image_tarball(
            'tests/data/blob.qcow2',
            page_size=8 * 8 * 1024,
            progress_callback=callback,
            force_replace_image=True
        )

        # File Not Found
        mock_put_blob.side_effect = FileNotFoundError('Not there!')
        with raises(AliyunImageUploadException):
            self.image.upload_image_tarball(
                'tests/data/blob.qcow2',
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
                'tests/data/blob.qcow2',
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
                'tests/data/blob.qcow2',
                page_size=8 * 8 * 1024,
                progress_callback=callback,
                force_replace_image=True
            )

        # Request Error
        mock_put_blob.side_effect = Exception('Failed')
        with raises(AliyunImageUploadException):
            self.image.upload_image_tarball(
                'tests/data/blob.qcow2',
                page_size=8 * 8 * 1024,
                progress_callback=callback,
                force_replace_image=True
            )

    @patch.object(AliyunImage, 'delete_storage_blob')
    @patch.object(AliyunImage, 'get_compute_image')
    def test_delete_compute_image(self, mock_get_image, mock_delete_tarball):
        image = {
            'ImageId': 'm-123',
            'DiskDeviceMappings': {
                'DiskDeviceMapping': [{'ImportOSSObject': 'test-blob'}]
            }
        }
        mock_get_image.side_effect = [
            image,
            AliyunImageException,
            AliyunImageException
        ]

        client = Mock()
        self.image._compute_client = client

        assert self.image.delete_compute_image(
            'test-image',
            delete_blob=True
        )

        # Image not exists
        assert self.image.delete_compute_image(
            'test-image',
            delete_blob=True
        ) is False

    def test_compute_image_exists(self):
        response = json.dumps({'Images': {'Image': [{'image1': 'info'}]}})
        client = Mock()
        client.do_action_with_exception.return_value = response
        self.image._compute_client = client

        assert self.image.image_exists('test-image')

        # Not exists
        client.do_action_with_exception.side_effect = Exception
        assert self.image.image_exists('test-image') is False

    @patch.object(AliyunImage, 'get_compute_image')
    def test_create_compute_image(self, mock_get_image):
        image = {'ImageId': 'm-123'}
        response = json.dumps(image)
        mock_get_image.return_value = image

        client = Mock()
        client.do_action_with_exception.return_value = response
        self.image._compute_client = client

        result = self.image.create_compute_image(
            'test-image',
            'test description',
            'test-blob.qcow2',
            'SLES'
        )
        assert result == 'm-123'

        # Create failure
        client.do_action_with_exception.return_value = Exception
        with raises(AliyunImageCreateException):
            self.image.create_compute_image(
                'test-image',
                'test description',
                'test-blob.qcow2',
                'SLES'
            )

    def test_get_regions(self):
        response = json.dumps({
            'Regions': {'Region': [{'RegionId': 'cn-beijing'}]}
        })
        client = Mock()
        client.do_action_with_exception.return_value = response
        self.image._compute_client = client

        regions = self.image.get_regions()
        assert 'cn-beijing' in regions

        # Failed to get regions
        client.do_action_with_exception.return_value = Exception

        with raises(AliyunException):
            self.image.get_regions()

    def test_bucket_name_var(self):
        client = Mock()
        self.image._bucket_client = client

        self.image.bucket_name = 'bucket2'
        assert self.image._bucket_client is None

    def test_region_var(self):
        client = Mock()
        self.image._bucket_client = client
        self.image._compute_client = client

        self.image.region = 'cn-beijing'
        assert self.image._bucket_client is None
        assert self.image._compute_client is None

    @patch.object(AliyunImage, 'get_regions')
    @patch.object(AliyunImage, 'get_compute_image')
    def test_replicate_image(self, mock_get_image, mock_get_regions):
        image = {'ImageId': 'm-123', 'Description': 'Test image'}
        response = json.dumps(image)
        mock_get_image.return_value = image
        mock_get_regions.return_value = ['cn-shanghai']

        client = Mock()
        client.do_action_with_exception.return_value = response
        self.image._compute_client = client

        self.image.replicate_image('test-image')

        # Replicate failure
        client.do_action_with_exception.side_effect = Exception
        self.image.replicate_image('test-image')

    @patch.object(AliyunImage, 'publish_image')
    @patch.object(AliyunImage, 'get_regions')
    @patch.object(AliyunImage, 'get_compute_image')
    def test_publish_image_to_regions(
        self,
        mock_get_image,
        mock_get_regions,
        mock_publish_image
    ):
        image = {'ImageId': 'm-123'}
        response = json.dumps(image)
        mock_get_image.return_value = image
        mock_get_regions.return_value = ['cn-beijing']

        client = Mock()
        client.do_action_with_exception.return_value = response
        self.image._compute_client = client

        self.image.publish_image_to_regions('test-image', 'VISIBLE')

    @patch.object(AliyunImage, 'get_compute_image')
    def test_publish_image(self, mock_get_image):
        image = {'ImageId': 'm-123'}
        response = json.dumps(image)
        mock_get_image.return_value = image

        client = Mock()
        client.do_action_with_exception.return_value = response
        self.image._compute_client = client

        self.image.publish_image('test-image', 'VISIBLE')

        # Publish failure
        client.do_action_with_exception.side_effect = Exception
        with raises(AliyunImageException):
            self.image.publish_image('test-image', 'VISIBLE')

    @patch.object(AliyunImage, 'deprecate_image')
    @patch.object(AliyunImage, 'get_regions')
    @patch.object(AliyunImage, 'get_compute_image')
    def test_deprecate_image_in_regions(
        self,
        mock_get_image,
        mock_get_regions,
        mock_deprecate_image
    ):
        image = {'ImageId': 'm-123'}
        response = json.dumps(image)
        mock_get_image.return_value = image
        mock_get_regions.return_value = ['cn-beijing']

        client = Mock()
        client.do_action_with_exception.return_value = response
        self.image._compute_client = client

        self.image.deprecate_image_in_regions('test-image')

    @patch.object(AliyunImage, 'get_compute_image')
    def test_deprecate_image(self, mock_get_image):
        image = {'ImageId': 'm-123'}
        response = json.dumps(image)
        mock_get_image.return_value = image

        client = Mock()
        client.do_action_with_exception.return_value = response
        self.image._compute_client = client

        self.image.deprecate_image('test-image')

        # Deprecate failure
        client.do_action_with_exception.side_effect = Exception
        with raises(AliyunImageException):
            self.image.deprecate_image('test-image')

    @patch.object(AliyunImage, 'activate_image')
    @patch.object(AliyunImage, 'get_regions')
    @patch.object(AliyunImage, 'get_compute_image')
    def test_activate_image_in_regions(
        self,
        mock_get_image,
        mock_get_regions,
        mock_activate_image
    ):
        image = {'ImageId': 'm-123'}
        response = json.dumps(image)
        mock_get_image.return_value = image
        mock_get_regions.return_value = ['cn-beijing']

        client = Mock()
        client.do_action_with_exception.return_value = response
        self.image._compute_client = client

        self.image.activate_image_in_regions('test-image')

    @patch.object(AliyunImage, 'get_compute_image')
    def test_activate_image(self, mock_get_image):
        image = {'ImageId': 'm-123'}
        response = json.dumps(image)
        mock_get_image.return_value = image

        client = Mock()
        client.do_action_with_exception.return_value = response
        self.image._compute_client = client

        self.image.activate_image('test-image')

        # Activate failure
        client.do_action_with_exception.side_effect = Exception
        with raises(AliyunImageException):
            self.image.activate_image('test-image')
