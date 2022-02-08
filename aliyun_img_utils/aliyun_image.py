# -*- coding: utf-8 -*-

"""Aliyun image class module."""

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
import os
import time

import oss2

from aliyunsdkcore.client import AcsClient
from aliyunsdkecs.request.v20140526.ImportImageRequest import (
    ImportImageRequest
)
from aliyunsdkecs.request.v20140526.DeleteImageRequest import (
    DeleteImageRequest
)
from aliyunsdkecs.request.v20140526.DescribeImagesRequest import (
    DescribeImagesRequest
)
from aliyunsdkecs.request.v20140526.DescribeRegionsRequest import (
    DescribeRegionsRequest
)
from aliyunsdkecs.request.v20140526.CopyImageRequest import (
    CopyImageRequest
)
from aliyunsdkecs.request.v20140526.ModifyImageSharePermissionRequest import (
    ModifyImageSharePermissionRequest
)
from aliyunsdkecs.request.v20140526.ModifyImageAttributeRequest import (
    ModifyImageAttributeRequest
)
from aliyunsdkecs.request.v20140526.TagResourcesRequest import (
    TagResourcesRequest
)

from aliyun_img_utils.aliyun_exceptions import (
    AliyunException,
    AliyunImageException,
    AliyunImageUploadException,
    AliyunImageCreateException
)
from aliyun_img_utils.aliyun_utils import (
    get_storage_auth,
    get_storage_bucket_client,
    put_blob,
    get_todays_date,
    get_future_date
)


class AliyunImage(object):
    """
    Provides methods for handling compute images in Alibaba (Aliyun).
    """
    IMAGE_STATE_MAP = {
        'Available': 'available',
        'UnAvailable': 'broken',
        'Creating': 'processing',
        'Waiting': 'processing',
        'CreateFailed': 'broken',
        'Deprecated': 'deprecated'
    }
    IMAGE_STATES = IMAGE_STATE_MAP.keys()
    IMAGE_BROKEN_STATES = [
        state for state, category in
        IMAGE_STATE_MAP.items() if category == 'broken'
    ]
    IMAGE_PROCESSING_STATES = [
        state for state, category in
        IMAGE_STATE_MAP.items() if category == 'processing'
    ]

    def __init__(
        self,
        access_key,
        access_secret,
        region,
        bucket_name=None,
        log_level=logging.INFO,
        log_callback=None,
        transfer_acceleration=True,
        timeout=180,
        deprecation_period=6
    ):
        """Initialize class and setup logging."""
        self.access_key = access_key
        self.access_secret = access_secret
        self.transfer_acceleration = transfer_acceleration
        self.timeout = timeout
        self.deprecation_period = deprecation_period
        self._region = region
        self._bucket_name = bucket_name
        self._bucket_client = None
        self._compute_client = None
        self._deprecation_date = None
        self._deletion_date = None

        if log_callback:
            self.log = log_callback
        else:
            self.log = logging.getLogger('aliyun-img-utils')
            self.log.setLevel(log_level)

        try:
            self.log_level = self.log.level
        except AttributeError:
            self.log_level = self.log.logger.level  # LoggerAdapter

    def image_tarball_exists(self, blob_name):
        """Return True if image exists in the configured bucket."""
        try:
            self.bucket_client.get_object_meta(blob_name)
        except oss2.exceptions.NoSuchKey:
            return False

        return True

    def wait_on_blob(self, blob_name):
        """
        Wait for the storage blob to show up in bucket.

        If it doesn't show up in 5 mintues raise exception.
        """
        start = time.time()
        end = start + 300

        while time.time() < end:
            exists = self.image_tarball_exists(blob_name)

            if not exists:
                time.sleep(10)
            else:
                return

        raise AliyunImageException(
            'Blob not available within 5 minutes.'
        )

    def delete_storage_blob(self, blob_name):
        """Delete blob if it exists in the configured bucket."""
        response = self.bucket_client.delete_object(blob_name)

        if response.status == 204:
            self.log.debug(
                f'Blob {blob_name} not found. '
                f'Nothing has been deleted.'
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

        if self.image_tarball_exists(blob_name) and not force_replace_image:
            raise AliyunImageUploadException(
                f'Image {blob_name} already exists. To replace an existing '
                f'image use force_replace_image option.'
            )
        elif self.image_tarball_exists(blob_name) and force_replace_image:
            self.delete_storage_blob(blob_name)

        kwargs = {}

        if page_size:
            kwargs['page_size'] = page_size

        if progress_callback:
            kwargs['progress_callback'] = progress_callback

        try:
            put_blob(self.bucket_client, blob_name, image_file, **kwargs)
        except FileNotFoundError:
            raise AliyunImageUploadException(
                f'Image file {image_file} not found. Ensure the path to'
                f' the file is correct.'
            )
        except oss2.exceptions.ServerError as error:
            raise AliyunImageUploadException(
                f'Unable to upload image: {str(error.details["Message"])}'
            )
        except oss2.exceptions.RequestError:
            raise AliyunImageUploadException(
                'Unable to upload image: Failed to establish a new '
                'connection.'
            )
        except Exception as error:
            raise AliyunImageUploadException(
                f'Unable to upload image: {str(error)}'
            )

        # Blob upload takes time to finish up
        self.wait_on_blob(blob_name)

        return blob_name

    def delete_compute_image(
        self,
        image_name,
        delete_blob=False,
        force=False
    ):
        """
        Delete compute image in current region.

        If delete_blob is True delete the backing storage blob.
        """
        try:
            image = self.get_compute_image(image_name=image_name)
        except AliyunImageException:
            return False

        request = DeleteImageRequest()
        request.set_accept_format('json')
        request.set_ImageId(image['ImageId'])

        if force:
            request.set_Force(force)

        try:
            self.compute_client.do_action_with_exception(request)
        except Exception as error:
            self.log.error(
                f'Unable to delete {image_name} in {self.region}: '
                f'{error}.'
            )
            raise AliyunImageException(
                f'Unable to delete image in {self.region}: {error}.'
            )

        self.wait_on_compute_image_delete(image['ImageId'])
        self.log.info(f'{image["ImageId"]} deleted in {self.region}')

        if delete_blob:
            oss_object = None
            try:
                device = image['DiskDeviceMappings']['DiskDeviceMapping'][0]
                oss_object = device['ImportOSSObject']
            except (IndexError, KeyError):
                pass

            if oss_object:
                self.delete_storage_blob(oss_object)

        return True

    def delete_compute_image_in_regions(
        self,
        image_name,
        delete_blob=False,
        force=False,
        regions=None
    ):
        """
        Delete the compute image based on image name in all regions.

        If a region list is not provided use all available regions.
        """
        if not regions:
            regions = self.get_regions()

        for region in regions:
            self.region = region

            try:
                self.delete_compute_image(
                    image_name,
                    delete_blob=delete_blob,
                    force=force
                )
            except Exception:
                pass

    def get_compute_image(
        self,
        image_name=None,
        image_id=None,
        status=None
    ):
        """
        Return compute image by name and/or id.

        If image is not found raise exception. Name and ID are both
        indices in Aliyun so there should always only be one image
        in the result set.
        """
        if not image_name and not image_id:
            raise AliyunImageException(
                'Image name and/or image ID is required to get image.'
            )

        if not status:
            status = ','.join(self.IMAGE_STATES)

        request = DescribeImagesRequest()
        request.set_Status(status)
        request.set_accept_format('json')

        if image_name:
            request.set_ImageName(image_name)

        if image_id:
            request.set_ImageId(image_id)

        try:
            response = json.loads(
                self.compute_client.do_action_with_exception(request)
            )
        except Exception as error:
            raise AliyunImageException(
                f'Unable to find image: {error}.'
            )

        try:
            image = response['Images']['Image'][0]
        except (KeyError, IndexError):
            raise AliyunImageException(
                'Unable to find image.'
            )

        return image

    def image_exists(self, image_name):
        """Return True if image exists, false otherwise."""
        try:
            self.get_compute_image(image_name=image_name)
        except AliyunImageException:
            return False

        return True

    def wait_on_compute_image_delete(self, image_id):
        """
        Wait for compute image to be deleted.

        If it still exists after 5 minutes raise exception.
        """
        start = time.time()
        end = start + 300

        while time.time() < end:
            try:
                self.get_compute_image(image_id=image_id)
            except AliyunImageException:
                return
            else:
                time.sleep(10)

        raise AliyunImageException(
            'Image not deleted within 5 minutes.'
        )

    def wait_on_compute_image(self, image_id, timeout=1500):
        """
        Wait for the compute image to show up in region.

        If it doesn't show up in 30 mintues raise exception.
        """
        start = time.time()
        end = start + timeout

        while time.time() < end:
            try:
                image = self.get_compute_image(image_id=image_id)
            except AliyunImageException:
                time.sleep(30)

            status = image.get('Status', 'unknown')

            if status in self.IMAGE_BROKEN_STATES:
                raise AliyunImageException(
                    f'Image in a broken state: {status}'
                )
            elif status in self.IMAGE_PROCESSING_STATES:
                time.sleep(30)
            elif status == 'Available':
                return
            elif status == 'Deprecated':
                raise AliyunImageException(
                    'Image status is "Deprecated" and '
                    'expected to be "Available"'
                )
            else:
                raise AliyunImageException(
                    f'Image in an unknown state: {status}'
                )

        raise AliyunImageException(
            'Image not available within 30 minutes.'
        )

    def create_compute_image(
        self,
        image_name,
        image_description,
        blob_name,
        platform,
        os_type='linux',
        arch='x86_64',
        disk_image_size=20,
        force_replace_image=False
    ):
        """
        Create compute image in current region from storage blob.

        If image exists and force replace is True delete the existing
        image before re-creating.
        """
        if force_replace_image and self.image_exists(image_name):
            self.delete_compute_image(image_name)

        request = ImportImageRequest()
        request.set_accept_format('json')
        request.set_DiskDeviceMappings(
            [
                {
                    'OSSBucket': self.bucket_name,
                    'OSSObject': blob_name,
                    'DiskImageSize': disk_image_size
                }
            ]
        )
        request.set_ImageName(image_name)
        request.set_Description(image_description)
        request.set_OSType(os_type)
        request.set_Architecture(arch)
        request.set_Platform(platform)

        try:
            response = json.loads(
                self.compute_client.do_action_with_exception(request)
            )
        except Exception as error:
            raise AliyunImageCreateException(
                f'Unable to create image: {error}.'
            )

        # Image creation is async so wait until image shows up
        self.wait_on_compute_image(response['ImageId'])

        return response['ImageId']

    def copy_compute_image(self, source_image_name, destination_region):
        """
        Copy compute image to specified region.
        """
        image = self.get_compute_image(image_name=source_image_name)

        request = CopyImageRequest()
        request.set_accept_format('json')
        request.set_ImageId(image['ImageId'])
        request.set_DestinationImageName(source_image_name)
        request.set_DestinationDescription(image['Description'])
        request.set_DestinationRegionId(destination_region)

        try:
            response = json.loads(
                self.compute_client.do_action_with_exception(request)
            )
        except Exception as error:
            self.log.error(
                f'Failed to copy {source_image_name} to {destination_region}: '
                f'{error}.'
            )
            raise AliyunImageException(
                f'Failed to copy image: {error}.'
            )

        self.log.info(f'{response["ImageId"]} created in {destination_region}')

        return response['ImageId']

    def replicate_image(self, source_image_name, regions=None):
        """
        Copy the compute image based on image name to all regions.

        If a region list is not provided use all available regions.
        """
        if not regions:
            regions = self.get_regions()

        images = {}
        for region in regions:
            if region == self.region:
                continue

            image_id = None
            try:
                image_id = self.copy_compute_image(source_image_name, region)
                images[region] = image_id
            except Exception:
                images[region] = None

        return images

    def publish_image(self, source_image_name, launch_permission):
        """
        Publish compute image in current region.
        """
        image = self.get_compute_image(image_name=source_image_name)

        request = ModifyImageSharePermissionRequest()
        request.set_accept_format('json')
        request.set_ImageId(image['ImageId'])
        request.set_LaunchPermission(launch_permission)

        try:
            self.compute_client.do_action_with_exception(request)
        except Exception as error:
            self.log.error(
                f'Failed to publish {source_image_name} in {self.region}: '
                f'{error}.'
            )
            raise AliyunImageException(
                f'Failed to publish image: {error}.'
            )

        self.log.info(f'{source_image_name} published in {self.region}')

    def publish_image_to_regions(
        self,
        source_image_name,
        launch_permission,
        regions=None
    ):
        """
        Publish the compute image based on image name in all regions.

        If a region list is not provided use all available regions.
        """
        if not regions:
            regions = self.get_regions()

        for region in regions:
            self.region = region

            try:
                self.publish_image(source_image_name, launch_permission)
            except Exception:
                pass

    def generate_deprecation_tags(self, replacement_image=None):
        """
        Create a list of deprecation tags.

        If the replacement image is provided include Replacement
        image tag.
        """
        tags = [
            {
                'Key': 'Deprecated on',
                'Value': self.deprecation_date
            },
            {
                'Key': 'Removal date',
                'Value': self.deletion_date
            }
        ]

        if replacement_image:
            tags.append(
                {
                    'Key': 'Replacement image',
                    'Value': replacement_image
                }
            )

        return tags

    def deprecate_image(self, source_image_name, replacement_image=None):
        """
        Deprecate compute image in current region.
        """
        image = self.get_compute_image(image_name=source_image_name)
        tags = self.generate_deprecation_tags(replacement_image)

        self.add_image_tags(image['ImageId'], tags)
        self.log.info(f'{source_image_name} deprecated in {self.region}')

    def deprecate_image_in_regions(
        self,
        source_image_name,
        regions=None,
        replacement_image=None
    ):
        """
        Deprecate the compute image based on image name in all regions.

        If a region list is not provided use all available regions.
        """
        if not regions:
            regions = self.get_regions()

        for region in regions:
            self.region = region

            try:
                self.deprecate_image(
                    source_image_name,
                    replacement_image
                )
            except Exception:
                pass

    def activate_image(self, source_image_name):
        """
        Activate compute image in current region.

        Sets the image status to available from a deprecated state.
        """
        image = self.get_compute_image(
            image_name=source_image_name,
            status='Deprecated'
        )

        request = ModifyImageAttributeRequest()
        request.set_accept_format('json')
        request.set_ImageId(image['ImageId'])
        request.set_Status('Available')

        try:
            self.compute_client.do_action_with_exception(request)
        except Exception as error:
            self.log.error(
                f'Failed to activate {source_image_name} in {self.region}: '
                f'{error}.'
            )
            raise AliyunImageException(
                f'Failed to activate image: {error}.'
            )

        self.log.info(f'{source_image_name} activated in {self.region}')

    def activate_image_in_regions(self, source_image_name, regions=None):
        """
        Activate compute image in all regions.

        If a region list is not provided use all available regions.
        """
        if not regions:
            regions = self.get_regions()

        for region in regions:
            self.region = region

            try:
                self.activate_image(source_image_name)
            except Exception:
                pass

    def add_image_tags(self, image_id, tags):
        """
        Add the list of tags to the image.
        """
        request = TagResourcesRequest()
        request.set_accept_format('json')
        request.set_ResourceType('image')
        request.set_ResourceIds([image_id])
        request.set_Tags(tags)

        try:
            self.compute_client.do_action_with_exception(request)
        except Exception as error:
            self.log.error(
                f'Failed to add tags to image {image_id} '
                f'in {self.region}: {error}.'
            )
            raise AliyunImageException(
                f'Failed to add tags to image: {error}.'
            )

        self.log.info(f'Tags added to {image_id} in {self.region}')

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
                self.region,
                self.transfer_acceleration,
                self.timeout
            )

            try:
                self._bucket_client.get_bucket_info()  # Force eager auth
            except oss2.exceptions.ServerError as error:
                raise AliyunException(
                    f'Unable to get bucket client: '
                    f'{str(error.details["Message"])}'
                )
            except oss2.exceptions.RequestError:
                raise AliyunException(
                    'Unable to get bucket client: Failed to establish a new '
                    'connection. Ensure the bucket name and region are '
                    'correct.'
                )
            except Exception as error:
                raise AliyunException(
                    f'Unable to get bucket client: {str(error)}'
                )

        return self._bucket_client

    @property
    def compute_client(self):
        """
        Compute client property.

        Lazy bucket client initialization. Attempts to ...
        """
        if not self._compute_client:
            try:
                self._compute_client = AcsClient(
                    self.access_key,
                    self.access_secret,
                    self.region,
                    connect_timeout=self.timeout
                )
            except Exception as error:
                raise AliyunException(
                    f'Unable to get compute client: {error}'
                )

        return self._compute_client

    def get_regions(self):
        """Return a list of available region ids."""
        request = DescribeRegionsRequest()
        request.set_accept_format('json')

        try:
            response = json.loads(
                self.compute_client.do_action_with_exception(request)
            )
        except Exception as error:
            raise AliyunException(
                f'Unable to get region list: {error}'
            )

        regions = []
        for region in response['Regions']['Region']:
            regions.append(region['RegionId'])

        return regions

    @property
    def bucket_name(self):
        """Bucket name property."""
        return self._bucket_name

    @bucket_name.setter
    def bucket_name(self, name):
        """
        Setter for bucket name.

        Reset affected clients so a new session is created
        """
        self._bucket_name = name
        self._bucket_client = None  # Reset bucket client

    @property
    def region(self):
        """Region property."""
        return self._region

    @region.setter
    def region(self, region_name):
        """
        Setter for region.

        Reset affected clients so a new session is created
        """
        self._region = region_name
        self._bucket_client = None  # Reset bucket client
        self._compute_client = None  # Reset compute client

    @property
    def deprecation_date(self):
        """Lazy deprecate date string property."""
        if not self._deprecation_date:
            self._deprecation_date = get_todays_date()

        return self._deprecation_date

    @property
    def deletion_date(self):
        """Lazy deletion date string property."""
        if not self._deletion_date:
            self._deletion_date = get_future_date(
                months=self.deprecation_period
            )

        return self._deletion_date
