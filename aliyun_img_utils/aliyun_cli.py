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

import json
import logging
import sys
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
    help='Path to qcow2 image.'
)
@click.option(
    '--page-size',
    type=click.IntRange(min=100 * 1024),
    help='Size of page size chunks for image upload. '
         'Minimum chunk size is 100KB.'
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
    """
    Upload a qcow2 image to a storage bucket in the current region.
    """
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
            f'Image uploaded as {blob_name}',
            config_data.no_color
        )


@click.command()
@click.option(
    '--image-name',
    type=click.STRING,
    required=True,
    help='Name of the newly created compute image.'
)
@click.option(
    '--image-description',
    type=click.STRING,
    required=True,
    help='Description for the newly created image.'
)
@click.option(
    '--platform',
    type=click.STRING,
    required=True,
    help='The distribution of the image operating system.'
)
@click.option(
    '--blob-name',
    type=click.STRING,
    required=True,
    help='Name for the blob in the storage bucket to use '
         'to create the new image.'
)
@click.option(
    '--force-replace-image',
    is_flag=True,
    help='Delete the compute image prior to creation if it already exists.'
)
@click.option(
    '--disk-size',
    type=click.IntRange(min=5),
    help='Size root disk in GB. Default is 20GB.'
)
@add_options(shared_options)
@click.pass_context
def create(
    context,
    image_name,
    image_description,
    platform,
    blob_name,
    force_replace_image,
    disk_size,
    **kwargs
):
    """
    Create a compute image from a qcow2 image in storage.
    """
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

        if disk_size:
            keyword_args['disk_image_size'] = disk_size

        image_id = aliyun_image.create_compute_image(
            image_name,
            image_description,
            blob_name,
            platform,
            **keyword_args
        )

    if config_data.log_level != logging.ERROR:
        echo_style(
            f'Image created with id: {image_id}',
            config_data.no_color
        )


@click.command()
@click.option(
    '--image-name',
    type=click.STRING,
    help='Name of the image to be deleted.',
    required=True
)
@click.option(
    '--delete-blob',
    is_flag=True,
    help='Also delete the image blob from storage bucket.'
)
@add_options(shared_options)
@click.pass_context
def delete(context, image_name, delete_blob, **kwargs):
    """Delete a compute image and optionally the backing qcow2 blob."""
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

        keyword_args = {'delete_blob': delete_blob}

        if click.confirm(f'Are you sure you want to delete {image_name}'):
            deleted = aliyun_image.delete_compute_image(
                image_name,
                **keyword_args
            )
        else:
            sys.exit(0)

    if config_data.log_level != logging.ERROR and deleted:
        echo_style(
            f'Image deleted: {image_name}',
            config_data.no_color
        )
    elif config_data.log_level != logging.ERROR and not deleted:
        echo_style(
            f'Image does not exist: {image_name}',
            config_data.no_color
        )


@click.command()
@click.option(
    '--image-name',
    type=click.STRING,
    help='Name of the image to be copied.',
    required=True
)
@click.option(
    '--regions',
    help='A comma separated list of region ids to '
         'copy the provided image to. If no regions '
         'are provided the image will be copied to all '
         'available regions.'
)
@add_options(shared_options)
@click.pass_context
def replicate(context, image_name, regions, **kwargs):
    """
    Replicate a compute image to a set of regions.

    If no regions are provided the image is replicated to all
    available regions.
    """
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

        keyword_args = {}

        if regions:
            regions = regions.split(',')
            keyword_args['regions'] = regions

        images = aliyun_image.replicate_image(image_name, **keyword_args)

    if config_data.log_level != logging.ERROR:
        echo_style(
            json.dumps(images, indent=2),
            config_data.no_color
        )


@click.command()
@click.option(
    '--image-name',
    type=click.STRING,
    help='Name of the image to be published.',
    required=True
)
@click.option(
    '--launch-permission',
    type=click.STRING,
    help='The launch permission to set for the published image.',
    required=True
)
@click.option(
    '--regions',
    help='A comma separated list of region ids to '
         'publish the provided image in. If no regions '
         'are provided the image will be published in all '
         'available regions.'
)
@add_options(shared_options)
@click.pass_context
def publish(context, image_name, launch_permission, regions, **kwargs):
    """
    Publish a compute image in a set of regions.

    If no regions are provided the image is published to all
    available regions.
    """
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

        keyword_args = {}

        if regions:
            regions = regions.split(',')
            keyword_args['regions'] = regions

        aliyun_image.publish_image_to_regions(
            image_name,
            launch_permission,
            **keyword_args
        )

    if config_data.log_level != logging.ERROR:
        echo_style(
            f'Image published: {image_name}',
            config_data.no_color
        )


@click.command()
@click.option(
    '--image-name',
    type=click.STRING,
    help='Name of the image to be deprecated.',
    required=True
)
@click.option(
    '--regions',
    help='A comma separated list of region ids to '
         'deprecate the provided image in. If no regions '
         'are provided the image will be deprecated in all '
         'available regions.'
)
@add_options(shared_options)
@click.pass_context
def deprecate(context, image_name, regions, **kwargs):
    """
    Deprecate compute in a set of regions.

    If no regions are provided the image is deprecated in all
    available regions.
    """
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

        keyword_args = {}

        if regions:
            regions = regions.split(',')
            keyword_args['regions'] = regions

        aliyun_image.deprecate_image_in_regions(image_name, **keyword_args)

    if config_data.log_level != logging.ERROR:
        echo_style(
            f'Image deprecated: {image_name}',
            config_data.no_color
        )


@click.command()
@click.option(
    '--image-name',
    type=click.STRING,
    help='Name of the image to be activated.',
    required=True
)
@click.option(
    '--regions',
    help='A comma separated list of region ids to '
         'activate the provided image in. If no regions '
         'are provided the image will be activated in all '
         'available regions.'
)
@add_options(shared_options)
@click.pass_context
def activate(context, image_name, regions, **kwargs):
    """
    Activate compute image (make available) in a set of regions.

    If no regions are provided the image is activated in all
    available regions.
    """
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

        keyword_args = {}

        if regions:
            regions = regions.split(',')
            keyword_args['regions'] = regions

        aliyun_image.activate_image_in_regions(image_name, **keyword_args)

    if config_data.log_level != logging.ERROR:
        echo_style(
            f'Image activated: {image_name}',
            config_data.no_color
        )


@click.command()
@click.option(
    '--image-name',
    type=click.STRING,
    help='Name of the image.'
)
@click.option(
    '--image-id',
    type=click.STRING,
    help='ID of the image.'
)
@click.option(
    '--deprecated',
    is_flag=True,
    help='If set the search is filtered on images '
         'in deprecated state.'
)
@add_options(shared_options)
@click.pass_context
def info(context, image_name, image_id, deprecated, **kwargs):
    """
    Get a dictionary of image data for an image based on ID or name.

    If `--deprecated` all images in deprecated state are searched
    otherwise all images in active state are searched.
    """
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

        image_data = aliyun_image.get_compute_image(
            image_name=image_name,
            image_id=image_id,
            is_deprecated=deprecated
        )

    echo_style(
        json.dumps(image_data, indent=2),
        config_data.no_color
    )


image.add_command(activate)
image.add_command(create)
image.add_command(delete)
image.add_command(deprecate)
image.add_command(publish)
image.add_command(replicate)
image.add_command(upload)
image.add_command(info)
main.add_command(image)
