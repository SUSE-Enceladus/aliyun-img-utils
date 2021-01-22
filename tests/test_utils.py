#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Aliyun img utils tests."""

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

from unittest.mock import patch, Mock

from aliyun_img_utils.aliyun_utils import put_blob, click_progress_callback


@patch('aliyun_img_utils.aliyun_utils.click')
def tests_click_progress_bar(mock_click):
    bar = Mock()
    bar.pos = 0
    mock_click.progressbar.return_value = bar
    click_progress_callback(15, 15)


@patch('aliyun_img_utils.aliyun_utils.oss2')
def test_put_blob(mock_oss2):
    client = Mock()
    callback = Mock()

    mock_oss2.determine_part_size.return_value = 15

    put_blob(
        client,
        'blob.vhd',
        'tests/data/blob.vhd',
        progress_callback=callback
    )
