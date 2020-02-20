from opaque_keys.edx.keys import CourseKey
from django.core.cache import cache
from edx_django_utils.cache import RequestCache

from openedx.core.djangoapps.catalog.tests.factories import (
    CourseFactory,
    ProgramFactory,
)
from student.tests.factories import TEST_PASSWORD, CourseEnrollmentFactory, UserFactory
from openedx.core.djangoapps.catalog.cache import PROGRAM_CACHE_KEY_TPL, COURSE_PROGRAMS_CACHE_KEY_TPL
from student.models import CourseEnrollment
from course_modes.models import CourseMode
from openedx.core.djangoapps.external_user_ids.models import ExternalId, ExternalIdType

from openedx.core.djangolib.testing.utils import CacheIsolationTestCase
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

# Tests
# Creating a new enrollment adds an external ID
# A second enrollment in a Program course will not create a second external UUID
# An enrollment in a course that is not part of a non-MB program will not create an external UUID


class MicrobachelorsExternalIDTest(ModuleStoreTestCase, CacheIsolationTestCase):
    ENABLED_CACHES = ['default']

    @classmethod
    def setUpClass(cls):
        super(MicrobachelorsExternalIDTest, cls).setUpClass()

        cls.course_keys = [
            CourseKey.from_string('course-v1:edX+DemoX+Test_Course'),
            CourseKey.from_string('course-v1:edX+DemoX+Another_Test_Course'),
        ]
        cls.course_list = []
        cls.user = UserFactory.create()
        for course_key in cls.course_keys:
            cls.course_list.append(CourseFactory(id=course_key))
        ExternalIdType.objects.create(
            name=ExternalIdType.MICROBACHELORS_COACHING,
            description='test'
        )

    def setUp(self):
        super(MicrobachelorsExternalIDTest, self).setUp()
        RequestCache.clear_all_namespaces()
        self.program = self._create_cached_program()
        self.client.login(username=self.user.username, password=TEST_PASSWORD)

    def _create_cached_program(self):
        """ helper method to create a cached program """
        program = ProgramFactory.create()
        course = program['courses'][0]['course_runs'][0]['key']
        program['type'] = 'MicroBachelors'
        program['type_slug'] = 'microbachelors'

        cache.set(
            COURSE_PROGRAMS_CACHE_KEY_TPL.format(course_run_id=course),
            [program['uuid']],
            None
        )
        cache.set(
            PROGRAM_CACHE_KEY_TPL.format(uuid=program['uuid']),
            program,
            None
        )

        return program

    def test_enroll_mb_create_external_id(self):
        course_run_key = self.program['courses'][0]['course_runs'][0]['key']

        # Enroll user
        enrollment = CourseEnrollment.objects.create(
            course_id=course_run_key,
            user=self.user,
            mode=CourseMode.VERIFIED,
        )
        enrollment.save()
        external_id = ExternalId.objects.get(
            user=self.user
        )
        assert external_id is not None
        assert external_id.external_id_type.name == ExternalIdType.MICROBACHELORS_COACHING
