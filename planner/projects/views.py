from django.shortcuts import get_object_or_404

from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from .models import AssignedProjects, Project

from .serializers import AssignedProjectSerializer, ProjectSerializer

from .serializers import TaskSerializer

from .models import Task

from rest_framework.views import APIView

from rest_framework.response import Response

from planner.utils import generate_tasks

from django.db import transaction

from planner.pagenations import CustomPagenation

# Create your views here.

class ProjectListCreateView(ListCreateAPIView):

    pagination_class = CustomPagenation

    queryset=Project.objects.filter(active_status=True)

    serializer_class= ProjectSerializer


class ProjectRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):

    lookup_field='uuid'

    queryset=Project.objects.filter(active_status=True)

    serializer_class= ProjectSerializer

    def perform_destroy(self,instance):
        
        instance.active_status=False

        instance.save()

class TaskListCreateView(ListCreateAPIView):

    pagination_class = CustomPagenation

    def get_queryset(self):

        project_uuid = self.request.query_params.get('project')

        print(f"Project UUID: {project_uuid}")  # Debugging line to check the value of project_uuid

        if project_uuid:
            return Task.objects.filter(
                assigned_project__uuid=project_uuid
            ).select_related('assigned_project', 'assigned_to')

        return Task.objects.none()

    serializer_class= TaskSerializer

class TaskRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):

    lookup_field = 'uuid'

    queryset = Task.objects.filter(active_status=True).select_related('assigned_project', 'assigned_to')

    serializer_class = TaskSerializer

    def perform_destroy(self, instance):

        instance.active_status = False

        instance.save(update_fields=['active_status', 'updated_at'])
    


class AssignedProjectListCreateView(ListCreateAPIView):

    pagination_class = CustomPagenation

    queryset = AssignedProjects.objects.all().select_related('project', 'coordinator').prefetch_related('developer')

    serializer_class = AssignedProjectSerializer


class AssignedProjectRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):

    lookup_field = 'uuid'

    queryset = AssignedProjects.objects.filter(active_status=True).select_related('project', 'coordinator').prefetch_related('developer')

    serializer_class = AssignedProjectSerializer

    def perform_destroy(self, instance):

        instance.active_status = False

        instance.save(update_fields=['active_status', 'updated_at'])


class TaskCreateWithAi(APIView):

    

    def post(self, request, *args, **kwargs):

        uuid = kwargs.get('uuid')

        assigned_project = get_object_or_404(AssignedProjects, uuid=uuid)

        result = generate_tasks(assigned_project)

        tasks = [Task(title=task.title,
                   description=task.description,
                   assigned_project=assigned_project,
                   assigned_to_id=task.developer_id,
                   priority=task.priority) for task in result.tasks]

        with transaction.atomic():

            Task.objects.bulk_create(tasks)

        data = {'message': 'Tasks assigned successfully.'}

        return Response(data,status=200)

        

        


