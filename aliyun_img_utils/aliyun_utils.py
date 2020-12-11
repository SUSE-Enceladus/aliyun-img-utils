# -*- coding: utf-8 -*-

"""Aliyun image utils utilities module."""

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

import os

import oss2


def get_storage_auth(access_key, access_secret):
    """Get Aliyun Auth object."""
    return oss2.Auth(access_key, access_secret)


def get_storage_bucket_client(auth, bucket_name, region):
    """Get authenticated storage bucket client."""
    endpoint = 'https://oss-{region}.aliyuncs.com'.format(region=region)
    return oss2.Bucket(auth, endpoint, bucket_name)


def put_blob(
    bucket_client,
    blob_name,
    image_file,
    page_size=8 * 1024 * 1024,
    progress_callback=None
):
    """Upload blob to bucket using multipart uploader."""
    total_size = os.path.getsize(image_file)
    part_size = oss2.determine_part_size(total_size, preferred_size=page_size)
    upload_id = bucket_client.init_multipart_upload(blob_name).upload_id

    with open(image_file, 'rb') as image_obj:
        parts = []
        part_number = 1
        offset = 0

        while offset < total_size:
            size_to_upload = min(part_size, total_size - offset)
            result = bucket_client.upload_part(
                blob_name,
                upload_id,
                part_number,
                oss2.SizedFileAdapter(image_obj, size_to_upload),
                progress_callback=progress_callback
            )
            parts.append(
                oss2.models.PartInfo(
                    part_number,
                    result.etag,
                    size=size_to_upload,
                    part_crc=result.crc
                )
            )

            offset += size_to_upload
            part_number += 1

        if progress_callback:
            progress_callback(offset, total_size)  # Last call to flush buffer

        bucket_client.complete_multipart_upload(blob_name, upload_id, parts)
