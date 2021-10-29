#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Aliyun img utils cli unit tests."""

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

from unittest.mock import patch, MagicMock

from aliyun_img_utils.aliyun_cli import main
from aliyun_img_utils.aliyun_exceptions import AliyunException
from click.testing import CliRunner


def test_client_help():
    """Confirm aliyun img utils --help is successful."""
    runner = CliRunner()
    result = runner.invoke(main, ['--help'])
    assert result.exit_code == 0
    assert 'The command line interface provides ' \
           'aliyun image utilities' in result.output


def test_print_license():
    runner = CliRunner()
    result = runner.invoke(main, ['--license'])
    assert result.exit_code == 0
    assert result.output == 'GPLv3+\n'


@patch('aliyun_img_utils.aliyun_cli.AliyunImage')
def test_cli_delete_image(mock_img_class):
    image_class = MagicMock()
    mock_img_class.return_value = image_class

    args = [
        'image', 'delete', '--image-name', 'test-image', '--access-key',
        '12345', '--access-secret', '54321', '--region', 'cn-beijing',
        '--bucket-name', 'test-bucket', '--regions', 'cn-shanghai'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args, input='y\n')
    assert result.exit_code == 0


@patch('aliyun_img_utils.aliyun_cli.AliyunImage')
def test_cli_upload_tarball(mock_img_class):
    image_class = MagicMock()
    mock_img_class.return_value = image_class
    image_class.upload_image_tarball.return_value = 'blob_name.vhd'

    args = [
        'image', 'upload', '--blob-name', 'test.vhd', '--access-key',
        '12345', '--access-secret', '54321', '--region', 'cn-beijing',
        '--bucket-name', 'test-bucket', '--image-file', 'tests/data/blob.vhd'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 'Image uploaded' in result.output


@patch('aliyun_img_utils.aliyun_cli.AliyunImage')
def test_cli_create_image(mock_img_class):
    image_class = MagicMock()
    mock_img_class.return_value = image_class
    image_class.create_compute_image.return_value = 'm-123456'

    args = [
        'image', 'create', '--image-name', 'test-image', '--access-key',
        '12345', '--access-secret', '54321', '--region', 'cn-beijing',
        '--bucket-name', 'test-bucket', '--image-description', 'test desc',
        '--platform', 'SLES', '--blob-name', 'test.blob.qcow2', '--disk-size',
        20
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 'Image created with id: m-123456' in result.output


@patch('aliyun_img_utils.aliyun_cli.AliyunImage')
def test_cli_exception(mock_img_class):
    image_class = MagicMock()
    mock_img_class.return_value = image_class
    image_class.upload_image_tarball.side_effect = AliyunException(
        'Failure!'
    )

    args = [
        'image', 'upload', '--blob-name', 'test.vhd', '--access-key',
        '12345', '--access-secret', '54321', '--region', 'cn-beijing',
        '--bucket-name', 'test-bucket', '--image-file', 'tests/data/blob.vhd'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 1
    assert 'Failure!' in result.output


@patch('aliyun_img_utils.aliyun_cli.AliyunImage')
def test_cli_replicate_image(mock_img_class):
    image_class = MagicMock()
    image_class.replicate_image.return_value = {
        'cn-beijing': 'ami-123',
        'cn-shanghai': 'ami-321'
    }
    mock_img_class.return_value = image_class

    args = [
        'image', 'replicate', '--image-name', 'test-image',
        '--regions', 'cn-beijing,cn-shanghai'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 'ami-123' in result.output


@patch('aliyun_img_utils.aliyun_cli.AliyunImage')
def test_cli_publish_image(mock_img_class):
    image_class = MagicMock()
    mock_img_class.return_value = image_class

    args = [
        'image', 'publish', '--image-name', 'test-image',
        '--launch-permission', 'FAKE', '--regions',
        'cn-beijing,cn-shanghai'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 'Image published' in result.output


@patch('aliyun_img_utils.aliyun_cli.AliyunImage')
def test_cli_deprecate_image(mock_img_class):
    image_class = MagicMock()
    mock_img_class.return_value = image_class

    args = [
        'image', 'deprecate', '--image-name', 'test-image',
        '--regions', 'cn-beijing,cn-shanghai'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 'Image deprecated' in result.output


@patch('aliyun_img_utils.aliyun_cli.AliyunImage')
def test_cli_activate_image(mock_img_class):
    image_class = MagicMock()
    mock_img_class.return_value = image_class

    args = [
        'image', 'activate', '--image-name', 'test-image',
        '--regions', 'cn-beijing,cn-shanghai'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 'Image activated' in result.output
