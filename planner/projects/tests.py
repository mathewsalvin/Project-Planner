from types import SimpleNamespace
from unittest import TestCase as UnitTestCase
from unittest.mock import patch

from rest_framework.test import APIRequestFactory

from .models import AssignedProjects
from .views import TaskCreateWithAi


class TaskCreateWithAiTests(UnitTestCase):

    def test_generated_tasks_use_assigned_developer_foreign_key(self):
        assigned_project = AssignedProjects(pk=1)
        generated_task = SimpleNamespace(
            title='Implement API',
            description='Build the project API.',
            developer_id=6,
            priority='Medium',
        )

        with (
            patch('projects.views.get_object_or_404', return_value=assigned_project),
            patch('projects.views.generate_tasks', return_value=SimpleNamespace(tasks=[generated_task])),
            patch('projects.views.Task.objects.bulk_create') as bulk_create,
        ):
            request = APIRequestFactory().post('/create-task-ai/example/')
            response = TaskCreateWithAi.as_view()(request, uuid='example')

        self.assertEqual(response.status_code, 200)
        created_tasks = bulk_create.call_args.args[0]
        self.assertEqual(len(created_tasks), 1)
        self.assertEqual(created_tasks[0].assigned_to_id, 6)
