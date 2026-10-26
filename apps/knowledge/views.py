import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from drf_spectacular.utils import extend_schema

from apps.sources.models import Source
from apps.roadmap.models import Skill, Topic
from .models import Concept, Evidence, CalculatedMastery, KnowledgeGap, Recommendation
from .serializers import (
    ConceptSerializer,
    EvidenceSerializer,
    RecordEvidenceRequestSerializer,
    SkillKnowledgeResponseSerializer,
    KnowledgeProfileResponseSerializer,
    KnowledgeExtractionResponseSerializer,
    CalculatedMasterySerializer,
    KnowledgeGapSerializer,
    RecommendationSerializer,
    UpdateRecommendationSerializer,
)
from .services import (
    PersonalKnowledgeModelService,
    EvidenceService,
    KnowledgePipeline,
    MasteryEngineService,
    KnowledgeGapService,
    RecommendationService,
)



class KnowledgeIndexView(APIView):
    """Overview endpoint for Knowledge & Personal Knowledge Model module."""
    @extend_schema(summary="Knowledge Module Overview")
    def get(self, request):
        return Response({
            "module": "knowledge",
            "status": "ready",
            "endpoints": {
                "concepts": request.build_absolute_uri("concepts/"),
                "evidence": request.build_absolute_uri("evidence/"),
                "profile": request.build_absolute_uri("profile/"),
            },
        })


class ConceptListView(APIView):
    """List extracted concepts with filtering by mapping status, topic, and skill."""

    @extend_schema(
        summary="List Extracted Concepts",
        responses={200: ConceptSerializer(many=True)},
    )
    def get(self, request):
        qs = Concept.objects.all().prefetch_related("skills", "evidence_items")

        # Filters
        unmapped = request.query_params.get("unmapped")
        if unmapped is not None and unmapped.lower() in ("true", "1"):
            qs = qs.filter(skills__isnull=True, topic__isnull=True)

        skill_id = request.query_params.get("skill_id")
        if skill_id:
            qs = qs.filter(skills__id=skill_id)

        topic_id = request.query_params.get("topic_id")
        if topic_id:
            qs = qs.filter(topic_id=topic_id)

        search = request.query_params.get("search")
        if search:
            qs = qs.filter(name__icontains=search)

        serializer = ConceptSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ConceptDetailView(APIView):
    """View details of a single Concept."""

    @extend_schema(summary="Concept Details", responses={200: ConceptSerializer})
    def get(self, request, pk):
        concept = Concept.objects.filter(id=pk).prefetch_related("skills", "evidence_items").first()
        if not concept:
            raise NotFound(detail=f"Concept {pk} not found")

        serializer = ConceptSerializer(concept)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EvidenceListView(APIView):
    """List or record knowledge evidence items."""

    @extend_schema(
        summary="List Evidence",
        responses={200: EvidenceSerializer(many=True)},
    )
    def get(self, request):
        qs = Evidence.objects.all().select_related("source", "concept", "skill", "topic")

        source_id = request.query_params.get("source_id")
        if source_id:
            qs = qs.filter(source_id=source_id)

        skill_id = request.query_params.get("skill_id")
        if skill_id:
            qs = qs.filter(skill_id=skill_id)

        evidence_type = request.query_params.get("evidence_type")
        if evidence_type:
            qs = qs.filter(evidence_type=evidence_type.lower())

        serializer = EvidenceSerializer(qs[:100], many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Record Knowledge Evidence",
        request=RecordEvidenceRequestSerializer,
        responses={201: EvidenceSerializer},
    )
    def post(self, request):
        serializer = RecordEvidenceRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        skill = None
        if data.get("skill_id"):
            skill = Skill.objects.filter(id=data["skill_id"]).first()
            if not skill:
                raise ValidationError({"skill_id": f"Skill {data['skill_id']} not found"})

        topic = None
        if data.get("topic_id"):
            topic = Topic.objects.filter(id=data["topic_id"]).first()
            if not topic:
                raise ValidationError({"topic_id": f"Topic {data['topic_id']} not found"})

        concept = None
        if data.get("concept_id"):
            concept = Concept.objects.filter(id=data["concept_id"]).first()

        ev_type = data["evidence_type"]
        title = data["title"]
        desc = data.get("description", "")
        weight = data.get("confidence_weight", 1.0)
        raw_data = data.get("raw_data", {})

        if ev_type == Evidence.EvidenceType.DECLARED and topic and not skill:
            evidence = EvidenceService.record_declared_topic_evidence(
                title=title,
                topic=topic,
                note=desc,
                confidence_weight=weight,
            )
            # Propagate declared evidence to constituent skills under this topic
            for sub_skill in topic.skills.all():
                EvidenceService.record_declared_evidence(
                    title=f"{sub_skill.name} (via {topic.name})",
                    skill=sub_skill,
                    note=f"Declared via topic {topic.name} during onboarding",
                    confidence_weight=weight,
                )
                PersonalKnowledgeModelService.recalculate_skill_mastery(sub_skill.id)
            MasteryEngineService.recalculate_topic_mastery(topic.id)
        elif ev_type == Evidence.EvidenceType.DECLARED and skill:
            evidence = EvidenceService.record_declared_evidence(
                title=title,
                skill=skill,
                note=desc,
                confidence_weight=weight,
            )
        elif ev_type == Evidence.EvidenceType.DECLARED and not topic and not skill:
            evidence = EvidenceService._create_evidence(
                evidence_type=Evidence.EvidenceType.DECLARED,
                title=title,
                description=desc or "Self-declared knowledge",
                raw_data={"note": desc},
                confidence_weight=weight,
            )
        elif ev_type == Evidence.EvidenceType.PRACTICAL and skill:
            evidence = EvidenceService.record_practical_evidence(
                title=title,
                skill=skill,
                description=desc,
                raw_data=raw_data,
                confidence_weight=weight,
            )
        elif ev_type == Evidence.EvidenceType.ASSESSMENT and skill:
            score = float(raw_data.get("score", 100))
            max_score = float(raw_data.get("max_score", 100))
            evidence = EvidenceService.record_assessment_evidence(
                title=title,
                skill=skill,
                score=score,
                max_score=max_score,
                confidence_weight=weight,
            )
        else:
            evidence = EvidenceService.record_learning_evidence(
                title=title,
                concept=concept,
                skill=skill,
                topic=topic,
                snippet=desc,
                confidence_weight=weight,
                raw_data=raw_data,
            )

        # Update mastery for skill
        if skill:
            PersonalKnowledgeModelService.recalculate_skill_mastery(skill.id)

        return Response(EvidenceSerializer(evidence).data, status=status.HTTP_201_CREATED)


class SkillKnowledgeDetailView(APIView):
    """Aggregate knowledge metrics, covered concepts, and evidence for a specific Skill."""

    @extend_schema(summary="Skill Knowledge Summary", responses={200: SkillKnowledgeResponseSerializer})
    def get(self, request, pk):
        summary = PersonalKnowledgeModelService.get_skill_summary(pk)
        if not summary:
            raise NotFound(detail=f"Skill {pk} not found")

        data = {
            "skill_id": summary.skill_id,
            "skill_name": summary.skill_name,
            "topic_id": summary.topic_id,
            "topic_name": summary.topic_name,
            "difficulty_level": summary.difficulty_level,
            "total_evidence_count": summary.total_evidence_count,
            "evidence_breakdown": summary.evidence_breakdown,
            "covered_concepts": summary.covered_concepts,
            "last_supported_at": summary.last_supported_at,
            "mastery_score": summary.mastery_score,
            "confidence_score": summary.confidence_score,
            "evidence_items": summary.evidence_items,
        }
        return Response(data, status=status.HTTP_200_OK)


class TopicKnowledgeDetailView(APIView):
    """Summarize knowledge and skills status under a Topic."""

    @extend_schema(summary="Topic Knowledge Summary")
    def get(self, request, pk):
        summary = PersonalKnowledgeModelService.get_topic_summary(pk)
        if not summary:
            raise NotFound(detail=f"Topic {pk} not found")
        return Response(summary, status=status.HTTP_200_OK)


class KnowledgeProfileView(APIView):
    """High-level Personal Knowledge Model summary profile."""

    @extend_schema(summary="Knowledge Model Profile", responses={200: KnowledgeProfileResponseSerializer})
    def get(self, request):
        domain_id = request.query_params.get("domain_id")
        profile = PersonalKnowledgeModelService.get_profile_summary(domain_id=domain_id)

        data = {
            "total_encountered_skills": profile.total_encountered_skills,
            "total_roadmap_skills": profile.total_roadmap_skills,
            "coverage_percentage": profile.coverage_percentage,
            "total_concepts_extracted": profile.total_concepts_extracted,
            "total_evidence_items": profile.total_evidence_items,
            "evidence_by_type": profile.evidence_by_type,
            "encountered_skills": profile.encountered_skills,
        }
        return Response(data, status=status.HTTP_200_OK)


class ExtractSourceKnowledgeView(APIView):
    """Trigger the Knowledge Extraction pipeline for an ingested Source."""

    @extend_schema(
        summary="Extract Knowledge from Source",
        responses={200: KnowledgeExtractionResponseSerializer},
    )
    def post(self, request, pk):
        source = Source.objects.filter(id=pk).first()
        if not source:
            raise NotFound(detail=f"Source {pk} not found")

        result = KnowledgePipeline.process_source(source)
        return Response(result.to_dict(), status=status.HTTP_200_OK)


class RetryKnowledgeExtractionView(APIView):
    """Retry failed knowledge extraction jobs for a Source."""

    @extend_schema(summary="Retry Knowledge Extraction")
    def post(self, request, pk):
        source = Source.objects.filter(id=pk).first()
        if not source:
            raise NotFound(detail=f"Source {pk} not found")

        results = KnowledgePipeline.retry_failed(source_id=pk)
        return Response(
            {
                "source_id": str(pk),
                "retried_jobs_count": len(results),
                "results": [r.to_dict() for r in results],
            },
            status=status.HTTP_200_OK,
        )


class MasteryListView(APIView):
    """List calculated mastery records across skills and topics."""

    @extend_schema(summary="List Calculated Masteries", responses={200: CalculatedMasterySerializer(many=True)})
    def get(self, request):
        qs = CalculatedMastery.objects.all().select_related("skill", "topic", "concept")

        skill_id = request.query_params.get("skill_id")
        if skill_id:
            qs = qs.filter(skill_id=skill_id)

        topic_id = request.query_params.get("topic_id")
        if topic_id:
            qs = qs.filter(topic_id=topic_id)

        level = request.query_params.get("level")
        if level:
            qs = qs.filter(mastery_level=level.lower())

        serializer = CalculatedMasterySerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SkillMasteryView(APIView):
    """View and recalculate mastery for a single Skill."""

    @extend_schema(summary="Get Skill Mastery", responses={200: CalculatedMasterySerializer})
    def get(self, request, pk):
        skill = Skill.objects.filter(id=pk).first()
        if not skill:
            raise NotFound(detail=f"Skill {pk} not found")

        mastery = CalculatedMastery.objects.filter(skill=skill).first()
        if not mastery:
            mastery = MasteryEngineService.recalculate_skill_mastery(skill.id)

        return Response(CalculatedMasterySerializer(mastery).data, status=status.HTTP_200_OK)

    @extend_schema(summary="Recalculate Skill Mastery", responses={200: CalculatedMasterySerializer})
    def post(self, request, pk):
        skill = Skill.objects.filter(id=pk).first()
        if not skill:
            raise NotFound(detail=f"Skill {pk} not found")

        mastery = PersonalKnowledgeModelService.recalculate_skill_mastery(skill.id)
        return Response(CalculatedMasterySerializer(mastery).data, status=status.HTTP_200_OK)


class TopicMasteryView(APIView):
    """View and recalculate mastery for a single Topic."""

    @extend_schema(summary="Get Topic Mastery", responses={200: CalculatedMasterySerializer})
    def get(self, request, pk):
        topic = Topic.objects.filter(id=pk).first()
        if not topic:
            raise NotFound(detail=f"Topic {pk} not found")

        mastery = CalculatedMastery.objects.filter(topic=topic).first()
        if not mastery:
            mastery = MasteryEngineService.recalculate_topic_mastery(topic.id)

        return Response(CalculatedMasterySerializer(mastery).data, status=status.HTTP_200_OK)

    @extend_schema(summary="Recalculate Topic Mastery", responses={200: CalculatedMasterySerializer})
    def post(self, request, pk):
        topic = Topic.objects.filter(id=pk).first()
        if not topic:
            raise NotFound(detail=f"Topic {pk} not found")

        mastery = MasteryEngineService.recalculate_topic_mastery(topic.id)
        return Response(CalculatedMasterySerializer(mastery).data, status=status.HTTP_200_OK)


class KnowledgeCoverageView(APIView):
    """View knowledge coverage across skills, topics, and modalities."""

    @extend_schema(summary="Get Knowledge Coverage Summary")
    def get(self, request):
        domain_id = request.query_params.get("domain_id")
        topic_id = request.query_params.get("topic_id")
        skill_id = request.query_params.get("skill_id")

        if skill_id:
            skill = Skill.objects.filter(id=skill_id).first()
            if not skill:
                raise NotFound(detail=f"Skill {skill_id} not found")
            summary = PersonalKnowledgeModelService.get_skill_summary(skill.id)
            return Response({
                "skill_id": summary.skill_id,
                "skill_name": summary.skill_name,
                "knowledge_coverage": summary.knowledge_coverage,
                "evidence_count": summary.total_evidence_count,
                "evidence_breakdown": summary.evidence_breakdown,
                "mastery_score": summary.mastery_score,
                "mastery_level": summary.mastery_level,
            }, status=status.HTTP_200_OK)

        skills_qs = Skill.objects.select_related("topic").all()
        if topic_id:
            skills_qs = skills_qs.filter(topic_id=topic_id)
        elif domain_id:
            skills_qs = skills_qs.filter(topic__domain_id=domain_id)

        coverage_data = []
        for s in skills_qs:
            mastery = CalculatedMastery.objects.filter(skill=s).first()
            if not mastery:
                mastery = MasteryEngineService.recalculate_skill_mastery(s.id)
            coverage_data.append({
                "skill_id": str(s.id),
                "skill_name": s.name,
                "topic_name": s.topic.name,
                "knowledge_coverage": float(mastery.knowledge_coverage),
                "mastery_score": float(mastery.mastery_score),
                "mastery_level": mastery.mastery_level,
                "evidence_count": mastery.evidence_count,
            })

        avg_coverage = (
            round(sum(c["knowledge_coverage"] for c in coverage_data) / len(coverage_data), 2)
            if coverage_data
            else 0.0
        )

        return Response({
            "total_skills": len(coverage_data),
            "average_coverage": avg_coverage,
            "skills": coverage_data,
        }, status=status.HTTP_200_OK)


class KnowledgeGapListView(APIView):
    """List identified knowledge gaps with filters and trigger re-evaluation."""

    @extend_schema(summary="List Knowledge Gaps", responses={200: KnowledgeGapSerializer(many=True)})
    def get(self, request):
        qs = KnowledgeGap.objects.all().select_related("skill", "topic")

        status_filter = request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter.lower())

        severity = request.query_params.get("severity")
        if severity:
            qs = qs.filter(severity=severity.lower())

        skill_id = request.query_params.get("skill_id")
        if skill_id:
            qs = qs.filter(skill_id=skill_id)

        topic_id = request.query_params.get("topic_id")
        if topic_id:
            qs = qs.filter(topic_id=topic_id)

        serializer = KnowledgeGapSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(summary="Evaluate Knowledge Gaps", responses={200: KnowledgeGapSerializer(many=True)})
    def post(self, request):
        topic_id = request.data.get("topic_id")
        gaps = KnowledgeGapService.evaluate_all_gaps(topic_id=topic_id)
        serializer = KnowledgeGapSerializer(gaps, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RecommendationListView(APIView):
    """List recommendations and trigger new generation."""

    @extend_schema(summary="List Recommendations", responses={200: RecommendationSerializer(many=True)})
    def get(self, request):
        qs = Recommendation.objects.all().select_related("skill", "topic", "source", "assessment", "gap")

        status_filter = request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter.lower())

        priority = request.query_params.get("priority")
        if priority:
            qs = qs.filter(priority=priority.lower())

        action_type = request.query_params.get("action_type")
        if action_type:
            qs = qs.filter(action_type=action_type.lower())

        skill_id = request.query_params.get("skill_id")
        if skill_id:
            qs = qs.filter(skill_id=skill_id)

        serializer = RecommendationSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(summary="Generate Recommendations", responses={200: RecommendationSerializer(many=True)})
    def post(self, request):
        use_llm = request.data.get("use_llm", False)
        recs = RecommendationService.generate_all_recommendations(use_llm=use_llm)
        serializer = RecommendationSerializer(recs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RecommendationDetailView(APIView):
    """View and update recommendation status (completed, dismissed)."""

    @extend_schema(summary="Get Recommendation Detail", responses={200: RecommendationSerializer})
    def get(self, request, pk):
        rec = Recommendation.objects.filter(id=pk).select_related("skill", "topic", "source", "assessment", "gap").first()
        if not rec:
            raise NotFound(detail=f"Recommendation {pk} not found")
        return Response(RecommendationSerializer(rec).data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Update Recommendation Status",
        request=UpdateRecommendationSerializer,
        responses={200: RecommendationSerializer},
    )
    def patch(self, request, pk):
        rec = Recommendation.objects.filter(id=pk).first()
        if not rec:
            raise NotFound(detail=f"Recommendation {pk} not found")

        serializer = UpdateRecommendationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rec.status = serializer.validated_data["status"]
        rec.save(update_fields=["status", "updated_at"])
        return Response(RecommendationSerializer(rec).data, status=status.HTTP_200_OK)


class IntegratedSkillSummaryView(APIView):
    """
    Returns full integrated knowledge flow for a Skill:
    Skill -> Evidence -> Score -> Mastery -> Gap -> Recommendation -> Roadmap Progress
    """

    @extend_schema(summary="Integrated Skill Knowledge Summary")
    def get(self, request, pk):
        summary = PersonalKnowledgeModelService.get_integrated_skill_summary(pk)
        if not summary:
            raise NotFound(detail=f"Skill {pk} not found")
        return Response(summary, status=status.HTTP_200_OK)


class OverallKnowledgeSummaryView(APIView):
    """
    Returns high-level dashboard summary across all skills, including:
    Domain progress, roadmap level progress, and integrated skill snapshots.
    """

    @extend_schema(summary="Overall Knowledge & Roadmap Summary")
    def get(self, request):
        domain_id = request.query_params.get("domain_id")
        summary = PersonalKnowledgeModelService.get_overall_knowledge_summary(domain_id=domain_id)
        return Response(summary, status=status.HTTP_200_OK)


class RecalculateKnowledgeView(APIView):
    """Trigger full recalculation of masteries, coverage, gaps, and recommendations."""

    @extend_schema(summary="Recalculate Derived Knowledge Model")
    def post(self, request):
        domain_id = request.data.get("domain_id")
        result = PersonalKnowledgeModelService.recalculate_all(domain_id=domain_id)
        return Response(result, status=status.HTTP_200_OK)

