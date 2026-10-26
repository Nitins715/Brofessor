from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from drf_spectacular.utils import extend_schema

from apps.roadmap.models import Domain, Topic, Skill, LearningResource, SkillResourceMapping
from .serializers import (
    DomainSerializer,
    TopicSerializer,
    SkillSerializer,
    RoadmapProgressSerializer,
    UpdateSkillProgressSerializer,
    LearningResourceSerializer,
    SkillResourceMappingSerializer,
)
from .services import RoadmapProgressService


class RoadmapIndexView(APIView):
    """Overview endpoint for Roadmap module."""
    @extend_schema(summary="Roadmap Module Overview")
    def get(self, request):
        return Response({
            "module": "roadmap",
            "status": "ready",
            "endpoints": {
                "domains": request.build_absolute_uri("domains/"),
                "topics": request.build_absolute_uri("topics/"),
                "skills": request.build_absolute_uri("skills/"),
                "resources": request.build_absolute_uri("resources/"),
                "hierarchy": request.build_absolute_uri("hierarchy/"),
                "progress": request.build_absolute_uri("progress/"),
                "levels": request.build_absolute_uri("progress/levels/"),
            },
        })


class DomainListView(APIView):
    """List knowledge domains or retrieve active domain."""

    @extend_schema(summary="List Domains", responses={200: DomainSerializer(many=True)})
    def get(self, request):
        active_only = request.query_params.get("active")
        qs = Domain.objects.all().order_by("name")
        if active_only and active_only.lower() in ("true", "1"):
            qs = qs.filter(is_active=True)
        return Response(DomainSerializer(qs, many=True).data, status=status.HTTP_200_OK)


class DomainDetailView(APIView):
    """Retrieve details for a single knowledge domain."""

    @extend_schema(summary="Get Domain Detail", responses={200: DomainSerializer})
    def get(self, request, pk):
        domain = Domain.objects.filter(id=pk).first()
        if not domain:
            raise NotFound(detail=f"Domain {pk} not found")
        return Response(DomainSerializer(domain).data, status=status.HTTP_200_OK)


class SelectActiveDomainView(APIView):
    """Select and activate a Domain as the user's primary roadmap focus."""

    @extend_schema(summary="Select Active Domain", responses={200: DomainSerializer})
    def post(self, request, pk):
        domain = Domain.objects.filter(id=pk).first()
        if not domain:
            raise NotFound(detail=f"Domain {pk} not found")

        # Unselect other domains and select this domain
        Domain.objects.exclude(id=domain.id).update(is_selected=False)
        domain.is_selected = True
        domain.save(update_fields=["is_selected", "updated_at"])

        return Response(DomainSerializer(domain).data, status=status.HTTP_200_OK)


class TopicListView(APIView):
    """List topics under a domain or across all domains, or create a new topic."""

    @extend_schema(summary="List Topics", responses={200: TopicSerializer(many=True)})
    def get(self, request):
        domain_id = request.query_params.get("domain_id")
        qs = Topic.objects.all().select_related("domain").order_by("domain", "order", "name")
        if domain_id:
            from django.db.models import Q
            qs = qs.filter(Q(domain_id=domain_id) | Q(additional_domains__id=domain_id)).distinct()
        return Response(TopicSerializer(qs, many=True).data, status=status.HTTP_200_OK)

    @extend_schema(summary="Create Topic", request=TopicSerializer, responses={201: TopicSerializer})
    def post(self, request):
        data = request.data.copy()
        if "slug" not in data or not data["slug"]:
            from django.utils.text import slugify
            data["slug"] = slugify(data.get("name", "topic"))
        serializer = TopicSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        topic = serializer.save()
        return Response(TopicSerializer(topic).data, status=status.HTTP_201_CREATED)


class TopicDetailView(APIView):
    """Retrieve, update, or delete a specific Topic."""

    @extend_schema(summary="Get Topic Detail", responses={200: TopicSerializer})
    def get(self, request, pk):
        topic = Topic.objects.filter(id=pk).select_related("domain").first()
        if not topic:
            raise NotFound(detail=f"Topic {pk} not found")
        return Response(TopicSerializer(topic).data, status=status.HTTP_200_OK)

    @extend_schema(summary="Update Topic", request=TopicSerializer, responses={200: TopicSerializer})
    def put(self, request, pk):
        topic = Topic.objects.filter(id=pk).first()
        if not topic:
            raise NotFound(detail=f"Topic {pk} not found")
        serializer = TopicSerializer(topic, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        return Response(TopicSerializer(updated).data, status=status.HTTP_200_OK)

    @extend_schema(summary="Partial Update Topic", request=TopicSerializer, responses={200: TopicSerializer})
    def patch(self, request, pk):
        topic = Topic.objects.filter(id=pk).first()
        if not topic:
            raise NotFound(detail=f"Topic {pk} not found")
        serializer = TopicSerializer(topic, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        return Response(TopicSerializer(updated).data, status=status.HTTP_200_OK)

    @extend_schema(summary="Delete Topic", responses={204: None})
    def delete(self, request, pk):
        topic = Topic.objects.filter(id=pk).first()
        if not topic:
            raise NotFound(detail=f"Topic {pk} not found")
        topic.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SkillListView(APIView):
    """List skills with optional filtering by topic or difficulty, or create a new skill."""

    @extend_schema(summary="List Skills", responses={200: SkillSerializer(many=True)})
    def get(self, request):
        topic_id = request.query_params.get("topic_id")
        domain_id = request.query_params.get("domain_id")
        difficulty = request.query_params.get("difficulty")
        search = request.query_params.get("search")

        qs = Skill.objects.all().select_related("topic").order_by("topic", "order", "name")
        if topic_id:
            qs = qs.filter(topic_id=topic_id)
        if domain_id:
            from django.db.models import Q
            qs = qs.filter(Q(topic__domain_id=domain_id) | Q(topic__additional_domains__id=domain_id)).distinct()
        if difficulty:
            qs = qs.filter(difficulty_level=difficulty.lower())
        if search:
            qs = qs.filter(name__icontains=search)

        return Response(SkillSerializer(qs, many=True).data, status=status.HTTP_200_OK)

    @extend_schema(summary="Create Skill", request=SkillSerializer, responses={201: SkillSerializer})
    def post(self, request):
        data = request.data.copy()
        if "slug" not in data or not data["slug"]:
            from django.utils.text import slugify
            data["slug"] = slugify(data.get("name", "skill"))
        serializer = SkillSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        skill = serializer.save()

        # Automatically ensure RoadmapNode and RoadmapProgress exist
        from apps.roadmap.models import RoadmapNode, RoadmapProgress
        node, _ = RoadmapNode.objects.get_or_create(
            skill=skill,
            defaults={
                "domain": skill.topic.domain,
                "topic": skill.topic,
                "order": skill.order,
            },
        )
        RoadmapProgress.objects.get_or_create(
            node=node,
            defaults={"status": RoadmapProgress.ProgressStatus.NOT_STARTED},
        )

        return Response(SkillSerializer(skill).data, status=status.HTTP_201_CREATED)


class SkillDetailView(APIView):
    """Retrieve, update, or delete a specific Skill."""

    @extend_schema(summary="Get Skill Detail", responses={200: SkillSerializer})
    def get(self, request, pk):
        skill = Skill.objects.filter(id=pk).select_related("topic").first()
        if not skill:
            raise NotFound(detail=f"Skill {pk} not found")
        return Response(SkillSerializer(skill).data, status=status.HTTP_200_OK)

    @extend_schema(summary="Update Skill", request=SkillSerializer, responses={200: SkillSerializer})
    def put(self, request, pk):
        skill = Skill.objects.filter(id=pk).first()
        if not skill:
            raise NotFound(detail=f"Skill {pk} not found")
        serializer = SkillSerializer(skill, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        return Response(SkillSerializer(updated).data, status=status.HTTP_200_OK)

    @extend_schema(summary="Partial Update Skill", request=SkillSerializer, responses={200: SkillSerializer})
    def patch(self, request, pk):
        skill = Skill.objects.filter(id=pk).first()
        if not skill:
            raise NotFound(detail=f"Skill {pk} not found")
        serializer = SkillSerializer(skill, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        return Response(SkillSerializer(updated).data, status=status.HTTP_200_OK)

    @extend_schema(summary="Delete Skill", responses={204: None})
    def delete(self, request, pk):
        skill = Skill.objects.filter(id=pk).first()
        if not skill:
            raise NotFound(detail=f"Skill {pk} not found")
        skill.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RoadmapHierarchyView(APIView):
    """
    Returns complete hierarchical roadmap tree:
    Domain -> Topic -> Skill -> Progression Node
    """

    @extend_schema(summary="Get Roadmap Hierarchy")
    def get(self, request):
        domain_id = request.query_params.get("domain_id")
        if domain_id:
            domains = Domain.objects.filter(id=domain_id)
        else:
            selected = Domain.objects.filter(is_selected=True)
            domains = selected if selected.exists() else Domain.objects.all()

        tree = []
        for d in domains:
            topics_data = []
            topics_qs = d.get_all_topics() if hasattr(d, "get_all_topics") else d.topics.all().order_by("order", "name")
            for t in topics_qs:
                skills_data = []
                for s in t.skills.all().order_by("order", "name"):
                    progress_info = RoadmapProgressService.get_skill_progress(s.id)
                    skills_data.append({
                        "id": str(s.id),
                        "name": s.name,
                        "slug": s.slug,
                        "difficulty_level": s.difficulty_level,
                        "priority": s.priority,
                        "progress": progress_info["status"],
                        "progress_percentage": progress_info["progress_percentage"],
                        "is_current": progress_info["is_current"],
                    })

                topics_data.append({
                    "id": str(t.id),
                    "name": t.name,
                    "slug": t.slug,
                    "priority": t.priority,
                    "skills_count": len(skills_data),
                    "skills": skills_data,
                })

            tree.append({
                "id": str(d.id),
                "name": d.name,
                "slug": d.slug,
                "is_selected": d.is_selected,
                "topics_count": len(topics_data),
                "topics": topics_data,
            })

        return Response(tree, status=status.HTTP_200_OK)


class RoadmapProgressOverviewView(APIView):
    """Calculate and retrieve overall curriculum roadmap progress for domain and levels."""

    @extend_schema(summary="Overall Roadmap Progress")
    def get(self, request):
        domain_id = request.query_params.get("domain_id")
        domain_progress = RoadmapProgressService.get_domain_progress(domain_id)
        level_progress = RoadmapProgressService.get_roadmap_level_progress(domain_id)
        return Response({
            "domain_progress": domain_progress,
            "roadmap_level_progress": level_progress,
        }, status=status.HTTP_200_OK)


class SkillProgressView(APIView):
    """View and update curriculum progress for a single Skill."""

    @extend_schema(summary="Get Skill Roadmap Progress")
    def get(self, request, pk):
        try:
            progress = RoadmapProgressService.get_skill_progress(pk)
            return Response(progress, status=status.HTTP_200_OK)
        except ValueError as e:
            raise NotFound(detail=str(e))

    @extend_schema(
        summary="Update Skill Roadmap Progress",
        request=UpdateSkillProgressSerializer,
    )
    def post(self, request, pk):
        serializer = UpdateSkillProgressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            progress = RoadmapProgressService.update_skill_progress(
                skill_id=pk,
                status=data["status"],
                is_current=data.get("is_current", False),
                notes=data.get("notes", ""),
            )
            return Response(RoadmapProgressSerializer(progress).data, status=status.HTTP_200_OK)
        except ValueError as e:
            raise NotFound(detail=str(e))


class TopicProgressView(APIView):
    """View curriculum progress for all skills in a Topic."""

    @extend_schema(summary="Get Topic Roadmap Progress")
    def get(self, request, pk):
        try:
            progress = RoadmapProgressService.get_topic_progress(pk)
            return Response(progress, status=status.HTTP_200_OK)
        except ValueError as e:
            raise NotFound(detail=str(e))


class DomainProgressView(APIView):
    """View curriculum progress for all topics in a Domain."""

    @extend_schema(summary="Get Domain Roadmap Progress")
    def get(self, request, pk):
        progress = RoadmapProgressService.get_domain_progress(domain_id=pk)
        return Response(progress, status=status.HTTP_200_OK)


class RoadmapLevelProgressView(APIView):
    """View curriculum progress broken down by Roadmap difficulty levels."""

    @extend_schema(summary="Get Roadmap Level Progress")
    def get(self, request):
        domain_id = request.query_params.get("domain_id")
        progress = RoadmapProgressService.get_roadmap_level_progress(domain_id=domain_id)
        return Response(progress, status=status.HTTP_200_OK)


class ImportCustomRoadmapView(APIView):
    """
    Import custom text or uploaded syllabus/roadmap document.
    Extracts topics and skills, compares with current domain roadmap,
    and adds only skills that are not already present.
    """
    from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @extend_schema(summary="Import Custom Roadmap Text or File")
    def post(self, request):
        from .custom_roadmap_service import CustomRoadmapImportService
        domain_id = request.data.get("domain_id")
        if not domain_id:
            selected_domain = Domain.objects.filter(is_selected=True).first() or Domain.objects.first()
            if not selected_domain:
                return Response({"error": "No domain found"}, status=status.HTTP_400_BAD_REQUEST)
            domain_id = str(selected_domain.id)

        text = request.data.get("text", "")
        file_obj = request.FILES.get("file")

        try:
            result = CustomRoadmapImportService.import_roadmap(
                domain_id=domain_id,
                text=text,
                file_obj=file_obj,
            )
            return Response(result, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Import failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SkillResourceListView(APIView):
    """Retrieve or attach external learning resources mapped to a specific Skill."""

    @extend_schema(summary="Get Skill External Learning Resources", responses={200: SkillResourceMappingSerializer(many=True)})
    def get(self, request, pk):
        skill = Skill.objects.filter(id=pk).first()
        if not skill:
            raise NotFound(detail=f"Skill {pk} not found")

        verified_only = request.query_params.get("verified_only", "true").lower() in ("true", "1")
        grouped = request.query_params.get("grouped", "false").lower() in ("true", "1")
        resource_type = request.query_params.get("type")

        mappings_qs = skill.resource_mappings.all().select_related("resource").order_by("-is_primary", "order", "resource__title")
        if verified_only:
            mappings_qs = mappings_qs.filter(resource__verification_status=LearningResource.VerificationStatus.VERIFIED)
        if resource_type:
            mappings_qs = mappings_qs.filter(resource__resource_type=resource_type)

        if grouped:
            groups = {
                LearningResource.ResourceType.PRIMARY: [],
                LearningResource.ResourceType.OFFICIAL_DOCS: [],
                LearningResource.ResourceType.PRACTICE: [],
                LearningResource.ResourceType.VIDEO: [],
            }
            for m in mappings_qs:
                t = m.resource.resource_type
                if t not in groups:
                    groups[t] = []
                groups[t].append(SkillResourceMappingSerializer(m).data)
            return Response(groups, status=status.HTTP_200_OK)

        return Response(SkillResourceMappingSerializer(mappings_qs, many=True).data, status=status.HTTP_200_OK)

    @extend_schema(summary="Attach Resource to Skill", request=SkillResourceMappingSerializer, responses={201: SkillResourceMappingSerializer})
    def post(self, request, pk):
        skill = Skill.objects.filter(id=pk).first()
        if not skill:
            raise NotFound(detail=f"Skill {pk} not found")

        data = request.data.copy()
        data["skill_id"] = str(skill.id)
        serializer = SkillResourceMappingSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        mapping = serializer.save(skill=skill)
        return Response(SkillResourceMappingSerializer(mapping).data, status=status.HTTP_201_CREATED)


class LearningResourceListView(APIView):
    """List, filter, and create external learning resources."""

    @extend_schema(summary="List Learning Resources", responses={200: LearningResourceSerializer(many=True)})
    def get(self, request):
        qs = LearningResource.objects.all().order_by("source", "title")
        search = request.query_params.get("search")
        resource_type = request.query_params.get("type")
        source = request.query_params.get("source")
        status_param = request.query_params.get("status")

        if search:
            from django.db.models import Q
            qs = qs.filter(Q(title__icontains=search) | Q(description__icontains=search) | Q(source__icontains=search))
        if resource_type:
            qs = qs.filter(resource_type=resource_type)
        if source:
            qs = qs.filter(source__iexact=source)
        if status_param:
            qs = qs.filter(verification_status=status_param)

        return Response(LearningResourceSerializer(qs, many=True).data, status=status.HTTP_200_OK)

    @extend_schema(summary="Create Learning Resource", request=LearningResourceSerializer, responses={201: LearningResourceSerializer})
    def post(self, request):
        serializer = LearningResourceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        resource = serializer.save()
        return Response(LearningResourceSerializer(resource).data, status=status.HTTP_201_CREATED)


class LearningResourceDetailView(APIView):
    """Retrieve, update, or delete a single learning resource."""

    @extend_schema(summary="Get Learning Resource Detail", responses={200: LearningResourceSerializer})
    def get(self, request, pk):
        resource = LearningResource.objects.filter(id=pk).first()
        if not resource:
            raise NotFound(detail=f"LearningResource {pk} not found")
        return Response(LearningResourceSerializer(resource).data, status=status.HTTP_200_OK)

    @extend_schema(summary="Update Learning Resource", request=LearningResourceSerializer, responses={200: LearningResourceSerializer})
    def put(self, request, pk):
        resource = LearningResource.objects.filter(id=pk).first()
        if not resource:
            raise NotFound(detail=f"LearningResource {pk} not found")
        serializer = LearningResourceSerializer(resource, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        return Response(LearningResourceSerializer(updated).data, status=status.HTTP_200_OK)

    @extend_schema(summary="Partial Update Learning Resource", request=LearningResourceSerializer, responses={200: LearningResourceSerializer})
    def patch(self, request, pk):
        resource = LearningResource.objects.filter(id=pk).first()
        if not resource:
            raise NotFound(detail=f"LearningResource {pk} not found")
        serializer = LearningResourceSerializer(resource, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        return Response(LearningResourceSerializer(updated).data, status=status.HTTP_200_OK)

    @extend_schema(summary="Delete Learning Resource", responses={204: None})
    def delete(self, request, pk):
        resource = LearningResource.objects.filter(id=pk).first()
        if not resource:
            raise NotFound(detail=f"LearningResource {pk} not found")
        resource.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


