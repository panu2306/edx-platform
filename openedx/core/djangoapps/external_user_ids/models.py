"""
Models for External User Ids that are sent out of Open edX
"""

import uuid as uuid_tools

from logging import getLogger

from django.contrib.auth.models import User
from django.db import models
from model_utils.models import TimeStampedModel
from simple_history.models import HistoricalRecords


LOGGER = getLogger(__name__)


class ExternalIdType(TimeStampedModel):
    """
    ExternalIdType defines the type (purpose, or expected use) of an external id. A user may have one id that is sent
    to Company A and another that is sent to Company B.

    .. no_pii:
    """
    MICROBACHELORS_COACHING = 'mb_coaching'

    name = models.CharField(max_length=32, blank=False, unique=True, db_index=True)
    description = models.TextField()
    history = HistoricalRecords()


class ExternalId(TimeStampedModel):
    """
    External ids are sent to systems or companies outside of Open edX. This allows us to limit the exposure of any
    given id.

    An external id is linked to an internal id, so that users may be re-identified if the external id is sent
    back to Open edX.

    .. no_pii: We store external_user_id here, but do not consider that PII under OEP-30.
    """
    external_user_id = models.UUIDField(default=uuid_tools.uuid4, editable=False, unique=True)
    external_id_type = models.ForeignKey(ExternalIdType, db_index=True, on_delete=models.CASCADE)
    user = models.ForeignKey(User, db_index=True, on_delete=models.CASCADE)
    history = HistoricalRecords()

    class Meta(object):
        app_label = "external_id"

    @classmethod
    def user_has_external_id(cls, user, type_name):
        """
        Checks if a user has an ExternalId of the type_name provided
        Arguments:
            user: User to search for
            type_name (str): Name of the type of ExternalId
        """
        try:
            type_obj = ExternalIdType.objects.get(name=type_name)
        except ExternalIdType.DoesNotExist:
            LOGGER.info('No external id type of {}'.format(type_name))
            return False
        try:
            external_id = cls.objects.get(
                user=user,
                external_id_type=type_obj
            )
            if external_id:
                return True
        except ExternalId.DoesNotExist:
            return False

    @classmethod
    def add_new_user_id(cls, user, type_name):
        """
        Creates an ExternalId for the User of the type_name provided
        Arguments:
            user: User to create the ID for
            type_name (str): Name of the type of ExternalId
        """
        try:
            type_obj = ExternalIdType.objects.get(name=type_name)
        except ExternalIdType.DoesNotExist:
            LOGGER.info(
                'External Creation failed for user {user}, no external id type of {type}'.format(
                    user=user.id,
                    type=type_name
                )
            )
            return None
        return cls.objects.create(
            user=user,
            external_id_type=type_obj
        )
