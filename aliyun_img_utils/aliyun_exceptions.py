# -*- coding: utf-8 -*-

"""Aliyun image utils exceptions module."""

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


class AliyunException(Exception):
    """Generic exception for the aliyun_img_utils package."""


class AliyunImageException(AliyunException):
    """Exception for Aliyun image processes."""


class AliyunImageUploadException(AliyunImageException):
    """Exception for Aliyun image upload processes."""


class AliyunImageCreateException(AliyunImageException):
    """Exception for Aliyun image create processes."""
