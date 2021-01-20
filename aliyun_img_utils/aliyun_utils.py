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

import logging
import os
import sys
import yaml

import click
import oss2

from collections import namedtuple, ChainMap
from contextlib import contextmanager


module = sys.modules[__name__]

default_config_dir = os.path.expanduser('~/.config/aliyun_img_utils/')
default_profile = 'default'

defaults = {
    'config_dir': default_config_dir,
    'profile': default_profile,
    'log_level': logging.INFO,
    'no_color': False,
    'region': 'cn-beijing',
    'access_key': None,
    'access_secret': None,
    'bucket_name': None,
}

aliyun_img_utils_config = namedtuple(
    'aliyun_img_utils_config',
    sorted(defaults)
)

progress_bar = None


def get_config(cli_context):
    """
    Process Aliyun Image utils config.

    Use ChainMap to build config values based on
    command line args, config and defaults.
    """
    config_dir = cli_context['config_dir'] or default_config_dir
    profile = cli_context['profile'] or default_profile

    config_values = {}
    config_file_path = os.path.join(config_dir, profile + '.yaml')

    try:
        with open(config_file_path) as config_file:
            config_values = yaml.safe_load(config_file)
    except FileNotFoundError:
        echo_style(
            'Config file: {config_file_path} not found. Using default '
            'configuration values. See `aliyun config setup` for info on '
            'setting up a config file for this profile.'.format(
                config_file_path=config_file_path
            ),
            no_color=True
        )

    cli_values = {
        key: value for key, value in cli_context.items() if value is not None
    }
    data = ChainMap(cli_values, config_values, defaults)

    return aliyun_img_utils_config(**data)


def echo_style(message, no_color, fg='yellow'):
    """
    Echo stylized output to terminal depending on no_color.
    """
    if no_color:
        click.echo(message)
    else:
        click.secho(message, fg=fg)


@contextmanager
def handle_errors(log_level, no_color):
    """
    Context manager to handle exceptions and echo error msg.
    """
    try:
        yield
    except Exception as error:
        if log_level == logging.DEBUG:
            raise

        echo_style(
            "{}: {}".format(type(error).__name__, error),
            no_color,
            fg='red'
        )
        sys.exit(1)


def click_progress_callback(offset, total_size):
    """
    Update the module level progress bar with image upload progress.

    If upload has finished flush stdout with render_finish.
    """
    if not module.progress_bar:
        module.progress_bar = click.progressbar(
            length=total_size,
            label='Uploading image'
        )

    read_size = offset - module.progress_bar.pos
    module.progress_bar.update(read_size)

    if offset >= total_size and module.progress_bar:
        module.progress_bar.render_finish()
        module.progress_bar = None
        return


def get_logger(log_level):
    """
    Return new console logger at provided log level.
    """
    logger = logging.getLogger('aliyun_img_utils')
    logger.setLevel(log_level)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter('%(message)s'))

    logger.addHandler(console_handler)
    return logger


def process_shared_options(context_obj, kwargs):
    """
    Update context with values for shared options.
    """
    context_obj['config_dir'] = kwargs['config_dir']
    context_obj['no_color'] = kwargs['no_color']
    context_obj['log_level'] = kwargs['log_level']
    context_obj['profile'] = kwargs['profile']
    context_obj['region'] = kwargs['region']
    context_obj['access_key'] = kwargs['access_key']
    context_obj['access_secret'] = kwargs['access_secret']
    context_obj['bucket_name'] = kwargs['bucket_name']


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
