# -*- coding: utf-8 -*-

"""Aliyun image utils cli module."""

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

import logging
import click

from aliyun_img_utils.aliyun_image import AliyunImage
from aliyun_img_utils.aliyun_utils import (
    get_config,
    echo_style,
    handle_errors,
    process_shared_options,
    get_logger,
    click_progress_callback
)


shared_options = [
    click.option(
        '-C',
        '--config-dir',
        type=click.Path(exists=True),
        help='Aliyun Image utils config directory to use. Default: '
             '~/.config/aliyun_img_utils/'
    ),
    click.option(
        '--profile',
        help='The configuration profile to use. Expected to match '
             'a config file in config directory. Example: production, '
             'for ~/.config/aliyun_img_utils/production.yaml. The default '
             'value is default: ~/.config/aliyun_img_utils/default.yaml'
    ),
    click.option(
        '--no-color',
        is_flag=True,
        help='Remove ANSI color and styling from output.'
    ),
    click.option(
        '--verbose',
        'log_level',
        flag_value=logging.DEBUG,
        help='Display debug level logging to console.'
    ),
    click.option(
        '--info',
        'log_level',
        flag_value=logging.INFO,
        default=True,
        help='Display logging info to console. (Default)'
    ),
    click.option(
        '--quiet',
        'log_level',
        flag_value=logging.ERROR,
        help='Display only errors to console.'
    ),
    click.option(
        '--access-key',
        type=click.STRING,
        help='Access key used for authentication of requests.'
    ),
    click.option(
        '--access-secret',
        type=click.STRING,
        help='Access secret used for authentication of requests.'
    ),
    click.option(
        '--bucket-name',
        type=click.STRING,
        help='Storage bucket to store uploaded images.'
    ),
    click.option(
        '--region',
        type=click.STRING,
        help='The region to use for the image requests.'
    )
]


def add_options(options):
    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func
    return _add_options


def print_license(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo('GPLv3+')
    ctx.exit()


def abort_if_false(ctx, param, value):
    if not value:
        ctx.abort()


@click.group()
@click.version_option()
@click.option(
    '--license',
    is_flag=True,
    callback=print_license,
    expose_value=False,
    is_eager=True,
    help='Show license information.'
)
@click.pass_context
def main(context):
    """
    The command line interface provides aliyun image utilities.

    This includes uploading image tarballs and
    creating/publishing/deprecating framework images.
    """
    if context.obj is None:
        context.obj = {}


@click.group()
def image():
    """
    Image commands.
    """


@click.command()
@click.option(
    '--image-file',
    type=click.Path(exists=True),
    required=True,
    help='Path to image tarball.'
)
@click.option(
    '--page-size',
    type=click.IntRange(min=1048576),
    help='Size of page size chunks for image upload. '
         'Minimum chunk size is 1MB.'
)
@click.option(
    '--blob-name',
    type=click.STRING,
    help='Name to use for blob in the storage bucket. By default '
         'the filename from image file will be used.'
)
@click.option(
    '--force-replace-image',
    is_flag=True,
    help='Delete the image prior to upload if it already exists.'
)
@add_options(shared_options)
@click.pass_context
def upload(
    context,
    image_file,
    page_size,
    blob_name,
    force_replace_image,
    **kwargs
):
    process_shared_options(context.obj, kwargs)
    config_data = get_config(context.obj)
    logger = get_logger(config_data.log_level)

    with handle_errors(config_data.log_level, config_data.no_color):
        aliyun_image = AliyunImage(
            config_data.access_key,
            config_data.access_secret,
            config_data.region,
            config_data.bucket_name,
            log_level=config_data.log_level,
            log_callback=logger
        )

        keyword_args = {
            'force_replace_image': force_replace_image
        }

        if page_size:
            keyword_args['page_size'] = page_size

        if blob_name:
            keyword_args['blob_name'] = blob_name

        if config_data.log_level != logging.ERROR:
            keyword_args['progress_callback'] = click_progress_callback

        blob_name = aliyun_image.upload_image_tarball(
            image_file,
            **keyword_args
        )

    if config_data.log_level != logging.ERROR:
        echo_style(
            'Image uploaded as {blob_name}'.format(blob_name=blob_name),
            config_data.no_color
        )


@click.command()
@click.option(
    '--blob-name',
    type=click.STRING,
    help='Name of the blob in the storage bucket. '
         'To be deleted.',
    required=True
)
@add_options(shared_options)
@click.pass_context
def delete(context, blob_name, **kwargs):
    process_shared_options(context.obj, kwargs)
    config_data = get_config(context.obj)
    logger = get_logger(config_data.log_level)

    with handle_errors(config_data.log_level, config_data.no_color):
        aliyun_image = AliyunImage(
            config_data.access_key,
            config_data.access_secret,
            config_data.region,
            config_data.bucket_name,
            log_level=config_data.log_level,
            log_callback=logger
        )

        keyword_args = {'blob_name': blob_name}

        if config_data.log_level != logging.ERROR:
            keyword_args['progress_callback'] = click_progress_callback

        deleted = aliyun_image.delete_image_tarball(blob_name, **keyword_args)

    if config_data.log_level != logging.ERROR and deleted:
        echo_style(
            'Image deleted: {blob_name}'.format(blob_name=blob_name),
            config_data.no_color
        )
    elif config_data.log_level != logging.ERROR and not deleted:
        echo_style(
            'Image does not exist: {blob_name}'.format(blob_name=blob_name),
            config_data.no_color
        )


image.add_command(delete)
image.add_command(upload)
main.add_command(image)
