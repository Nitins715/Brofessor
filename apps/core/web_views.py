"""Web UI views for Brofessor Personal Knowledge System.

Django template-driven views connecting frontend to the existing backend services and models.
"""

import json
import os
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.conf import settings
from django.utils.text import slugify
from django.core.management import call_command
from django.db.models import Avg, Count, Q

from apps.accounts.models import User
from apps.roadmap.models import Domain, Topic, Skill, RoadmapNode, RoadmapProgress, LearningResource, SkillResourceMapping
from apps.roadmap.services import RoadmapProgressService
from apps.knowledge.models import Evidence, CalculatedMastery, KnowledgeGap, Recommendation, Concept
from apps.knowledge.services import (
    PersonalKnowledgeModelService,
    MasteryEngineService,
    KnowledgeGapService,
    RecommendationService,
)
from apps.sources.models import Source, Document, DocumentChunk
from apps.assessments.models import Assessment, Attempt, Question, Answer
from apps.assessments.services.assessment_engine import AssessmentEngineService
from apps.assessments.services.sequential_generator import SequentialQuestionGenerationService
from apps.rag.models import Conversation, Message
from apps.sources.views import dispatch_ingestion


def get_or_create_local_user():
    """Ensure a default local developer user exists for single-user local app."""
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        user = User.objects.filter(username="brofessor").first()
    if not user:
        user = User.objects.create_user(
            username="brofessor",
            email="local@brofessor.ai",
            password="brofessor-local-dev-password",
        )
    return user


class LandingOrDashboardView(View):
    """Root view: redirects authenticated users to dashboard or onboarding, or renders landing."""
    def get(self, request):
        if request.user.is_authenticated:
            has_domain = Domain.objects.filter(is_selected=True).exists()
            has_evidence = Evidence.objects.exists()
            if not has_domain and not has_evidence:
                return redirect("web-onboarding")
            return redirect("web-dashboard")

        return render(
            request,
            "pages/landing.html",
            {
                "db_engine": settings.DATABASES["default"]["ENGINE"].split(".")[-1],
                "default_username": "brofessor",
                "data_dir": str(getattr(settings, "DATA_DIR", "/data")),
            },
        )


class WebLoginView(View):
    """Local workspace entry without password friction."""
    def get(self, request):
        if not request.user.is_authenticated:
            user = get_or_create_local_user()
            login(request, user)
        has_domain = Domain.objects.filter(is_selected=True).exists()
        if not has_domain:
            return redirect("web-onboarding")
        return redirect("web-dashboard")

    def post(self, request):
        username = request.POST.get("username", "").strip() or "brofessor"
        user = User.objects.filter(username=username).first()
        if not user:
            user = get_or_create_local_user()
        login(request, user)
        messages.success(request, f"Welcome to your local workspace, {user.username}!")
        has_domain = Domain.objects.filter(is_selected=True).exists()
        if not has_domain:
            return redirect("web-onboarding")
        return redirect("web-dashboard")


class WebDevLoginView(View):
    """Direct entry into local workspace."""
    def post(self, request):
        user = get_or_create_local_user()
        login(request, user)
        messages.success(request, f"Welcome to your local workspace, {user.username}!")
        has_domain = Domain.objects.filter(is_selected=True).exists()
        has_evidence = Evidence.objects.exists()
        if not has_domain and not has_evidence:
            return redirect("web-onboarding")
        return redirect("web-dashboard")

    def get(self, request):
        return self.post(request)


class WebLogoutView(View):
    """Sign out the current user and return to landing."""
    def post(self, request):
        logout(request)
        messages.info(request, "Signed out of local workspace session.")
        return redirect("web-landing")

    def get(self, request):
        logout(request)
        return redirect("web-landing")




class OnboardingView(View):
    """Flagship 5-step conversational onboarding flow."""
    def get(self, request):
        if not request.user.is_authenticated:
            user = get_or_create_local_user()
            login(request, user)

        if Domain.objects.count() == 0:
            call_command("seed_roadmap")

        domains = Domain.objects.filter(is_active=True).prefetch_related("topics")
        active_domain = Domain.objects.filter(is_selected=True).first()

        context = {
            "current_nav": "onboarding",
            "domains": domains,
            "active_domain": active_domain or domains.first(),
        }
        return render(request, "pages/onboarding.html", context)


class CreateCustomDomainAjaxView(View):
    """AJAX helper for creating a custom domain during onboarding."""
    def post(self, request):
        try:
            data = json.loads(request.body.decode("utf-8"))
        except Exception:
            data = request.POST

        name = data.get("name", "").strip()
        desc = data.get("description", "").strip()

        if not name:
            return JsonResponse({"success": False, "error": "Domain name is required."}, status=400)

        slug = slugify(name)
        base_slug = slug
        counter = 1
        while Domain.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        Domain.objects.update(is_selected=False)
        domain = Domain.objects.create(
            name=name,
            slug=slug,
            description=desc,
            is_active=True,
            is_selected=True,
        )

        return JsonResponse({
            "success": True,
            "domain": {
                "id": str(domain.id),
                "name": domain.name,
                "slug": domain.slug,
                "description": domain.description,
            }
        })


class DashboardView(LoginRequiredMixin, View):
    """Main dashboard dynamically reflecting user's actual Personal Knowledge Model."""
    login_url = "/login/"

    def get(self, request):
        active_domain = Domain.objects.filter(is_selected=True).first() or Domain.objects.first()

        # Check empty state: user has no evidence and no sources
        evidence_count = Evidence.objects.count()
        sources_count = Source.objects.count()
        is_empty_state = (evidence_count == 0 and sources_count == 0)

        # 1. Overview metrics
        avg_mastery_res = CalculatedMastery.objects.aggregate(avg=Avg("mastery_score"))
        overall_knowledge_score = round(avg_mastery_res["avg"] or 0, 1)

        domain_progress_info = {"progress_percentage": 0.0, "completed_skills": 0, "total_skills": 0}
        if active_domain:
            domain_progress_info = RoadmapProgressService.get_domain_progress(active_domain.id)

        # Mastery summary by level
        mastery_summary = {
            "expert": CalculatedMastery.objects.filter(mastery_level="expert").count(),
            "advanced": CalculatedMastery.objects.filter(mastery_level="advanced").count(),
            "intermediate": CalculatedMastery.objects.filter(mastery_level="intermediate").count(),
            "beginner": CalculatedMastery.objects.filter(mastery_level="beginner").count(),
        }

        # 2. Topics analytics (topics covered vs total)
        topics_list = list(active_domain.get_all_topics()) if active_domain else list(Topic.objects.all())
        total_topics_count = len(topics_list)
        topics_analytics = []
        topics_covered_count = 0

        for t in topics_list:
            t_skills = list(t.skills.all())
            t_skill_count = len(t_skills)
            if t_skill_count == 0:
                topics_analytics.append({
                    "id": str(t.id),
                    "name": t.name,
                    "priority": t.priority,
                    "priority_label": t.get_priority_display(),
                    "total_skills": 0,
                    "completed_skills": 0,
                    "in_progress_skills": 0,
                    "percentage": 0,
                    "is_covered": False,
                    "status": "Not Started",
                })
                continue

            t_progresses = RoadmapProgress.objects.filter(node__skill__in=t_skills)
            t_completed = t_progresses.filter(
                status__in=[RoadmapProgress.ProgressStatus.COMPLETED, RoadmapProgress.ProgressStatus.MASTERED]
            ).count()
            t_in_progress = t_progresses.filter(status=RoadmapProgress.ProgressStatus.IN_PROGRESS).count()

            is_covered = (t_completed > 0 or t_in_progress > 0)
            if is_covered:
                topics_covered_count += 1

            pct = round((t_completed / t_skill_count) * 100, 1)
            status_text = "Mastered" if t_completed == t_skill_count else ("In Progress" if is_covered else "Not Started")

            topics_analytics.append({
                "id": str(t.id),
                "name": t.name,
                "priority": t.priority,
                "priority_label": t.get_priority_display(),
                "total_skills": t_skill_count,
                "completed_skills": t_completed,
                "in_progress_skills": t_in_progress,
                "percentage": int(pct),
                "is_covered": is_covered,
                "status": status_text,
            })

        topics_coverage_percentage = round((topics_covered_count / total_topics_count) * 100, 1) if total_topics_count > 0 else 0

        # 3. Skill set breakdown analytics
        domain_skills = Skill.objects.filter(topic__in=topics_list) if active_domain else Skill.objects.all()
        total_domain_skills = domain_skills.count()

        skill_progresses = RoadmapProgress.objects.filter(node__skill__in=domain_skills)
        skills_mastered_count = skill_progresses.filter(status=RoadmapProgress.ProgressStatus.MASTERED).count()
        skills_completed_count = skill_progresses.filter(status=RoadmapProgress.ProgressStatus.COMPLETED).count()
        skills_in_progress_count = skill_progresses.filter(status=RoadmapProgress.ProgressStatus.IN_PROGRESS).count()
        skills_not_started_count = max(0, total_domain_skills - (skills_mastered_count + skills_completed_count + skills_in_progress_count))

        skills_analytics = {
            "total": total_domain_skills,
            "mastered": skills_mastered_count,
            "completed": skills_completed_count,
            "in_progress": skills_in_progress_count,
            "not_started": skills_not_started_count,
            "mastered_pct": round((skills_mastered_count / total_domain_skills) * 100, 1) if total_domain_skills > 0 else 0,
            "completed_pct": round((skills_completed_count / total_domain_skills) * 100, 1) if total_domain_skills > 0 else 0,
            "in_progress_pct": round((skills_in_progress_count / total_domain_skills) * 100, 1) if total_domain_skills > 0 else 0,
            "not_started_pct": round((skills_not_started_count / total_domain_skills) * 100, 1) if total_domain_skills > 0 else 0,
        }

        # 4. Past performance & assessment analytics
        user_attempts = Attempt.objects.filter(completed_at__isnull=False).select_related(
            "assessment", "assessment__skill", "assessment__topic"
        ).order_by("-completed_at")
        total_attempts = user_attempts.count()
        passed_attempts = user_attempts.filter(passed=True).count()
        avg_score_res = user_attempts.aggregate(avg=Avg("score"))
        avg_score = round(avg_score_res["avg"] or 0, 1)
        pass_rate = round((passed_attempts / total_attempts) * 100, 1) if total_attempts > 0 else 0

        recent_attempts = []
        for att in user_attempts[:5]:
            recent_attempts.append({
                "id": str(att.id),
                "title": att.assessment.title,
                "topic_name": att.assessment.topic.name if att.assessment.topic else (att.assessment.skill.topic.name if att.assessment.skill else "General"),
                "difficulty": att.assessment.get_difficulty_level_display(),
                "score": float(att.score or 0),
                "passed": att.passed,
                "completed_at": att.completed_at,
                "feedback": att.feedback[:120] if att.feedback else "",
            })

        performance_analytics = {
            "total_attempts": total_attempts,
            "passed_attempts": passed_attempts,
            "avg_score": avg_score,
            "pass_rate": pass_rate,
            "recent_attempts": recent_attempts,
        }

        # 5. Current focus
        # Recommend skill/topic from highest priority recommendation or current active node
        current_focus = None
        top_rec = Recommendation.objects.filter(status=Recommendation.Status.PENDING).order_by("-priority", "-created_at").first()
        if top_rec and top_rec.skill:
            current_focus = {
                "skill": top_rec.skill,
                "topic": top_rec.skill.topic,
                "reason": top_rec.title,
                "action_type": top_rec.action_type,
            }
        else:
            # Fallback to current roadmap progress node
            curr_progress = RoadmapProgress.objects.filter(is_current=True).select_related("node__skill__topic").first()
            if not curr_progress and active_domain:
                curr_progress = RoadmapProgress.objects.filter(
                    node__domain=active_domain,
                    status__in=[RoadmapProgress.ProgressStatus.IN_PROGRESS, RoadmapProgress.ProgressStatus.NOT_STARTED]
                ).select_related("node__skill__topic").first()

            if curr_progress:
                current_focus = {
                    "skill": curr_progress.node.skill,
                    "topic": curr_progress.node.skill.topic,
                    "reason": f"Next curriculum objective in {curr_progress.node.topic.name}",
                    "action_type": "study",
                }

        # 6. Skills overview (display important skills with name, mastery level, progress %, visual indicator)
        skills_overview = []
        target_skills = Skill.objects.all().select_related("topic")
        if active_domain:
            target_skills = target_skills.filter(topic__domain=active_domain)

        for skill in target_skills[:8]:
            mastery = CalculatedMastery.objects.filter(skill=skill).first()
            progress = RoadmapProgress.objects.filter(node__skill=skill).first()
            score = float(mastery.mastery_score) if mastery else 0.0
            level = mastery.mastery_level.capitalize() if mastery else "Beginner"

            skills_overview.append({
                "id": str(skill.id),
                "name": skill.name,
                "topic_name": skill.topic.name,
                "mastery_level": level,
                "percentage": int(score),
                "status": progress.status if progress else "not_started",
            })

        # Sort skills by percentage descending
        skills_overview.sort(key=lambda s: s["percentage"], reverse=True)

        # 7. Knowledge gaps (most important current gaps)
        top_gaps = KnowledgeGap.objects.filter(status=KnowledgeGap.Status.ACTIVE).select_related("skill", "topic").order_by("-severity", "-identified_at")[:4]

        # 8. Recent activity (unified feed of sources, assessments, and evidence updates)
        recent_activity = []
        for src in Source.objects.all().order_by("-created_at")[:3]:
            recent_activity.append({
                "type": "source",
                "badge": src.source_type.upper(),
                "title": f"Source added: {src.name}",
                "timestamp": src.created_at,
                "status": src.status,
                "url": f"/sources/{src.id}/",
            })
        for att in Attempt.objects.filter(completed_at__isnull=False).select_related("assessment").order_by("-completed_at")[:3]:
            recent_activity.append({
                "type": "assessment",
                "badge": "ASSESSMENT",
                "title": f"Assessment completed: {att.assessment.title} ({att.score}%)",
                "timestamp": att.completed_at,
                "status": "passed" if att.passed else "review",
                "url": "/assessments/",
            })
        for ev in Evidence.objects.all().select_related("skill").order_by("-recorded_at")[:3]:
            recent_activity.append({
                "type": "evidence",
                "badge": ev.evidence_type.upper(),
                "title": f"Evidence recorded: {ev.title}",
                "timestamp": ev.recorded_at,
                "status": "recorded",
                "url": "/knowledge/",
            })
        recent_activity.sort(key=lambda a: a["timestamp"] or "", reverse=True)
        recent_activity = recent_activity[:6]

        # 9. Recommended next action (one clear action with primary action button)
        recommended_action = None
        if top_rec:
            recommended_action = {
                "title": top_rec.title,
                "description": top_rec.description,
                "action_text": "Continue Learning",
                "action_url": f"/knowledge/skills/{top_rec.skill.id}/" if top_rec.skill else "/assessments/",
            }
        elif current_focus:
            recommended_action = {
                "title": f"Work on {current_focus['skill'].name}",
                "description": f"Target key concepts in {current_focus['topic'].name} to raise your curriculum mastery.",
                "action_text": "Explore Skill",
                "action_url": f"/knowledge/skills/{current_focus['skill'].id}/",
            }
        elif active_domain:
            first_skill = Skill.objects.filter(topic__domain=active_domain).first()
            if first_skill:
                recommended_action = {
                    "title": f"Start learning {first_skill.name}",
                    "description": "Establish your initial knowledge baseline with evidence and diagnostics.",
                    "action_text": "Begin Skill",
                    "action_url": f"/knowledge/skills/{first_skill.id}/",
                }

        # 10. Recommendations list
        top_recommendations = Recommendation.objects.filter(status=Recommendation.Status.PENDING).select_related("skill", "topic", "assessment", "source").order_by("-created_at")[:2]

        context = {
            "current_nav": "dashboard",
            "active_domain": active_domain,
            "is_empty_state": is_empty_state,
            "overall_knowledge_score": overall_knowledge_score,
            "domain_progress": domain_progress_info,
            "mastery_summary": mastery_summary,
            "topics_analytics": topics_analytics,
            "topics_covered_count": topics_covered_count,
            "total_topics_count": total_topics_count,
            "topics_coverage_percentage": topics_coverage_percentage,
            "skills_analytics": skills_analytics,
            "performance_analytics": performance_analytics,
            "current_focus": current_focus,
            "skills_overview": skills_overview,
            "top_gaps": top_gaps,
            "recent_activity": recent_activity,
            "recommended_action": recommended_action,
            "top_recommendations": top_recommendations,
            "evidence_count": evidence_count,
            "sources_count": sources_count,
            "gaps_count": KnowledgeGap.objects.filter(status=KnowledgeGap.Status.ACTIVE).count(),
        }
        return render(request, "pages/dashboard.html", context)


class RoadmapView(LoginRequiredMixin, View):
    """Hierarchical curriculum tree for knowledge domains (Domain -> Topic -> Skill)."""
    login_url = "/login/"

    def get(self, request):
        domain_id = request.GET.get("domain_id")
        if domain_id:
            domain = Domain.objects.filter(id=domain_id, is_active=True).first()
            if domain:
                Domain.objects.exclude(id=domain.id).update(is_selected=False)
                domain.is_selected = True
                domain.save(update_fields=["is_selected", "updated_at"])
                active_domain = domain
            else:
                active_domain = Domain.objects.filter(is_selected=True).first() or Domain.objects.first()
        else:
            active_domain = Domain.objects.filter(is_selected=True).first() or Domain.objects.first()

        domains = Domain.objects.filter(is_active=True)

        topics_data = []
        domain_progress_pct = 0.0

        if active_domain:
            dom_prog = RoadmapProgressService.get_domain_progress(active_domain.id)
            domain_progress_pct = dom_prog.get("progress_percentage", 0.0)

            topics_qs = active_domain.get_all_topics() if hasattr(active_domain, "get_all_topics") else active_domain.topics.all().order_by("order", "name")
            for topic in topics_qs:
                topic_skills_data = []
                for skill in topic.skills.all().order_by("order", "name"):
                    progress_info = RoadmapProgressService.get_skill_progress(skill.id)
                    mastery = CalculatedMastery.objects.filter(skill=skill).first()
                    mastery_score = float(mastery.mastery_score) if mastery else 0.0
                    mastery_level = mastery.mastery_level if mastery else "beginner"

                    topic_skills_data.append({
                        "id": str(skill.id),
                        "name": skill.name,
                        "slug": skill.slug,
                        "description": skill.description,
                        "difficulty_level": skill.difficulty_level,
                        "priority": skill.priority,
                        "learning_objectives": skill.learning_objectives,
                        "key_concepts": skill.key_concepts,
                        "interview_relevance": skill.interview_relevance,
                        # Roadmap completion workflow status
                        "progress_status": progress_info["status"],
                        "progress_percentage": progress_info["progress_percentage"],
                        "is_current": progress_info["is_current"],
                        # Actual demonstrated mastery
                        "mastery_score": mastery_score,
                        "mastery_level": mastery_level,
                    })

                topics_data.append({
                    "id": str(topic.id),
                    "name": topic.name,
                    "description": topic.description,
                    "order": topic.order,
                    "priority": topic.priority,
                    "learning_objectives": topic.learning_objectives,
                    "skills_count": len(topic_skills_data),
                    "skills": topic_skills_data,
                })

        context = {
            "current_nav": "roadmap",
            "domains": domains,
            "active_domain": active_domain,
            "domain_progress_pct": domain_progress_pct,
            "topics_data": topics_data,
        }
        return render(request, "pages/roadmap.html", context)


class RoadmapSkillStatusAjaxView(LoginRequiredMixin, View):
    """Toggle or update roadmap completion status for a skill."""
    login_url = "/login/"

    def post(self, request, pk):
        try:
            data = json.loads(request.body.decode("utf-8"))
        except Exception:
            data = request.POST

        new_status = data.get("status")
        if not new_status or new_status not in [c[0] for c in RoadmapProgress.ProgressStatus.choices]:
            return JsonResponse({"success": False, "error": "Invalid status value"}, status=400)

        try:
            progress = RoadmapProgressService.update_skill_progress(
                skill_id=pk,
                status=new_status,
                is_current=data.get("is_current", False),
            )
            return JsonResponse({
                "success": True,
                "status": progress.status,
                "progress_percentage": RoadmapProgressService.get_skill_progress(pk)["progress_percentage"],
            })
        except ValueError as e:
            return JsonResponse({"success": False, "error": str(e)}, status=404)


class KnowledgeView(LoginRequiredMixin, View):
    """Personal Knowledge Model view with filtering by domain, topic, skill, and mastery level."""
    login_url = "/login/"

    def get(self, request):
        active_domain = Domain.objects.filter(is_selected=True).first() or Domain.objects.first()

        # Query Filters
        topic_id = request.GET.get("topic_id")
        mastery_filter = request.GET.get("mastery_level")
        search_query = request.GET.get("q", "").strip()

        skills_qs = Skill.objects.all().select_related("topic", "topic__domain")
        if active_domain:
            domain_topics = active_domain.get_all_topics()
            skills_qs = skills_qs.filter(topic__in=domain_topics)
        if topic_id:
            skills_qs = skills_qs.filter(topic_id=topic_id)
        if search_query:
            skills_qs = skills_qs.filter(Q(name__icontains=search_query) | Q(description__icontains=search_query))

        skills_data = []
        for skill in skills_qs:
            mastery = CalculatedMastery.objects.filter(skill=skill).first()
            mastery_score = float(mastery.mastery_score) if mastery else 0.0
            mastery_level = mastery.mastery_level if mastery else "unrated"

            if mastery_filter and mastery_filter != "all":
                if mastery_filter == "unrated" and mastery:
                    continue
                elif mastery_filter != "unrated" and (not mastery or mastery.mastery_level != mastery_filter):
                    continue

            # Evidence counts breakdown
            ev_qs = Evidence.objects.filter(skill=skill)
            sources_count = ev_qs.filter(source__isnull=False).values("source").distinct().count()
            assessments_count = ev_qs.filter(evidence_type=Evidence.EvidenceType.ASSESSMENT).count()
            projects_count = ev_qs.filter(evidence_type=Evidence.EvidenceType.PRACTICAL).count()

            # Assessment trend: recent 3 attempt scores
            trend_scores = list(
                Attempt.objects.filter(assessment__skill=skill, completed_at__isnull=False)
                .order_by("completed_at")
                .values_list("score", flat=True)
            )[-3:]
            trend_display = " → ".join([f"{int(s)}%" for s in trend_scores]) if trend_scores else None

            skills_data.append({
                "id": str(skill.id),
                "name": skill.name,
                "topic_name": skill.topic.name,
                "domain_name": skill.topic.domain.name,
                "difficulty_level": skill.difficulty_level,
                "mastery_score": int(mastery_score),
                "mastery_level": mastery_level,
                "sources_count": sources_count,
                "assessments_count": assessments_count,
                "projects_count": projects_count,
                "trend_display": trend_display,
            })

        # Available filters for UI
        domains = Domain.objects.filter(is_active=True)
        topics = active_domain.get_all_topics() if active_domain else Topic.objects.all()

        context = {
            "current_nav": "knowledge",
            "active_domain": active_domain,
            "domains": domains,
            "topics": topics,
            "selected_domain_id": str(active_domain.id) if active_domain else None,
            "selected_topic_id": topic_id,
            "selected_mastery": mastery_filter or "all",
            "search_query": search_query,
            "skills_data": skills_data,
            "total_skills_count": len(skills_data),
        }
        return render(request, "pages/knowledge.html", context)


class SkillDetailView(LoginRequiredMixin, View):
    """Detailed view for an individual skill's knowledge model state."""
    login_url = "/login/"

    def get(self, request, pk):
        skill = get_object_or_404(Skill.objects.select_related("topic", "topic__domain"), pk=pk)

        # 1. Calculated mastery
        mastery = CalculatedMastery.objects.filter(skill=skill).first()

        # 2. Concepts linked to this skill
        concepts = skill.concepts.all().prefetch_related("evidence_items")

        # 3. Evidence items supporting this skill (expandable cards)
        evidence_items = Evidence.objects.filter(skill=skill).select_related("source", "concept").order_by("-recorded_at")

        # 4. Sources linked to this skill
        sources = Source.objects.filter(evidence_items__skill=skill).distinct()

        # 5. Assessment history
        assessment_attempts = Attempt.objects.filter(assessment__skill=skill, completed_at__isnull=False).select_related("assessment").order_by("-completed_at")

        # 6. Knowledge gaps
        gaps = KnowledgeGap.objects.filter(skill=skill, status=KnowledgeGap.Status.ACTIVE)

        # 7. Recommendations
        recommendations = Recommendation.objects.filter(skill=skill, status=Recommendation.Status.PENDING)

        # 8. Roadmap progress
        progress_info = RoadmapProgressService.get_skill_progress(skill.id)

        # 9. Direct assessment for this skill
        skill_assessment = Assessment.objects.filter(skill=skill, is_active=True).first()

        # 10. External Learning Resources (verified, grouped, separate from assessments/mastery)
        resource_mappings = (
            skill.resource_mappings
            .filter(resource__verification_status=LearningResource.VerificationStatus.VERIFIED)
            .select_related("resource")
            .order_by("-is_primary", "order", "resource__title")
        )
        grouped_resources = {
            "primary": [m for m in resource_mappings if m.resource.resource_type == LearningResource.ResourceType.PRIMARY],
            "official_docs": [m for m in resource_mappings if m.resource.resource_type == LearningResource.ResourceType.OFFICIAL_DOCS],
            "practice": [m for m in resource_mappings if m.resource.resource_type == LearningResource.ResourceType.PRACTICE],
            "video": [m for m in resource_mappings if m.resource.resource_type == LearningResource.ResourceType.VIDEO],
        }
        total_verified_resources = len(resource_mappings)

        context = {
            "current_nav": "knowledge",
            "skill": skill,
            "mastery": mastery,
            "concepts": concepts,
            "evidence_items": evidence_items,
            "sources": sources,
            "assessment_attempts": assessment_attempts,
            "gaps": gaps,
            "recommendations": recommendations,
            "progress_info": progress_info,
            "skill_assessment": skill_assessment,
            "resource_mappings": resource_mappings,
            "grouped_resources": grouped_resources,
            "total_verified_resources": total_verified_resources,
        }
        return render(request, "pages/skill_detail.html", context)


class SourcesView(LoginRequiredMixin, View):
    """Knowledge library listing with tabs and prominent Add Source action."""
    login_url = "/login/"

    def get(self, request):
        active_domain = Domain.objects.filter(is_selected=True).first() or Domain.objects.first()
        active_tab = request.GET.get("tab", "all").lower()

        sources_qs = Source.objects.all().prefetch_related("documents", "evidence_items").order_by("-created_at")

        if active_tab == "pdf":
            sources_qs = sources_qs.filter(source_type=Source.SourceType.PDF)
        elif active_tab == "article":
            sources_qs = sources_qs.filter(source_type=Source.SourceType.ARTICLE)
        elif active_tab == "youtube":
            sources_qs = sources_qs.filter(source_type=Source.SourceType.YOUTUBE)
        elif active_tab == "note":
            sources_qs = sources_qs.filter(source_type=Source.SourceType.NOTE)
        elif active_tab == "project":
            sources_qs = sources_qs.filter(source_type__in=[Source.SourceType.GITHUB, "manual"])

        sources_list = []
        for src in sources_qs:
            # Related skills
            skills = Skill.objects.filter(evidence_items__source=src).distinct()[:3]
            # Contribution
            doc = src.documents.first()
            chunk_count = doc.chunks.count() if doc else 0
            ev_count = src.evidence_items.count()

            sources_list.append({
                "id": str(src.id),
                "name": src.name,
                "source_type": src.source_type,
                "created_at": src.created_at,
                "status": src.status,
                "uri": src.uri,
                "file_path": src.file_path,
                "skills": skills,
                "chunk_count": chunk_count,
                "evidence_count": ev_count,
            })

        # Counts by type for tab badges
        type_counts = {
            "all": Source.objects.count(),
            "pdf": Source.objects.filter(source_type=Source.SourceType.PDF).count(),
            "article": Source.objects.filter(source_type=Source.SourceType.ARTICLE).count(),
            "youtube": Source.objects.filter(source_type=Source.SourceType.YOUTUBE).count(),
            "note": Source.objects.filter(source_type=Source.SourceType.NOTE).count(),
            "project": Source.objects.filter(source_type__in=[Source.SourceType.GITHUB, "manual"]).count(),
        }

        context = {
            "current_nav": "sources",
            "active_domain": active_domain,
            "active_tab": active_tab,
            "sources": sources_list,
            "type_counts": type_counts,
        }
        return render(request, "pages/sources.html", context)


class SourceDetailView(LoginRequiredMixin, View):
    """Detailed view for an individual knowledge source."""
    login_url = "/login/"

    def get(self, request, pk):
        source = get_object_or_404(Source, pk=pk)

        document = source.documents.first()
        chunks = document.chunks.all().order_by("chunk_index") if document else []

        # Related concepts
        concepts = Concept.objects.filter(evidence_items__source=source).distinct()

        # Related skills and topics
        skills = Skill.objects.filter(evidence_items__source=source).select_related("topic").distinct()
        topics = Topic.objects.filter(skills__in=skills).distinct()

        # Knowledge evidence
        evidence_items = source.evidence_items.all().order_by("-recorded_at")

        context = {
            "current_nav": "sources",
            "source": source,
            "document": document,
            "chunks": chunks,
            "concepts": concepts,
            "skills": skills,
            "topics": topics,
            "evidence_items": evidence_items,
        }
        return render(request, "pages/source_detail.html", context)


class SourceRetryView(LoginRequiredMixin, View):
    """Retry ingestion for a failed source."""
    login_url = "/login/"

    def post(self, request, pk):
        source = get_object_or_404(Source, pk=pk)
        source.status = Source.ProcessingStatus.PENDING
        source.error_message = ""
        source.save(update_fields=["status", "error_message", "updated_at"])

        dispatch_ingestion(source, run_async=False)
        messages.success(request, f"Processing retried for '{source.name}'.")
        return redirect("web-source-detail", pk=pk)


class SourceDeleteView(LoginRequiredMixin, View):
    """Delete a knowledge source and all its related documents and chunks."""
    login_url = "/login/"

    def post(self, request, pk):
        source = get_object_or_404(Source, pk=pk)
        source_name = source.name
        source.delete()
        messages.success(request, f"Source '{source_name}' was successfully deleted.")
        return redirect("web-sources")


class AssessmentsView(LoginRequiredMixin, View):
    """Diagnostic assessments listing with trends, attempts history, and test launcher."""
    login_url = "/login/"

    def get(self, request):
        active_domain = Domain.objects.filter(is_selected=True).first() or Domain.objects.first()
        assessments_qs = Assessment.objects.filter(is_active=True).select_related("skill", "topic").prefetch_related("questions", "attempts").order_by("-created_at")
        past_attempts = Attempt.objects.filter(completed_at__isnull=False).select_related("assessment", "assessment__skill").order_by("-completed_at")

        if active_domain:
            domain_topics = active_domain.get_all_topics()
            assessments_qs = assessments_qs.filter(Q(skill__topic__in=domain_topics) | Q(topic__in=domain_topics))
            past_attempts = past_attempts.filter(Q(assessment__skill__topic__in=domain_topics) | Q(assessment__topic__in=domain_topics))

        past_attempts = past_attempts[:25]

        assessments_data = []
        for a in assessments_qs:
            attempts_list = list(a.attempts.filter(completed_at__isnull=False).order_by("-completed_at"))
            latest_attempt = attempts_list[0] if attempts_list else None
            prev_attempt = attempts_list[1] if len(attempts_list) > 1 else None

            latest_score = float(latest_attempt.score) if (latest_attempt and latest_attempt.score is not None) else None

            # Calculate trend
            if latest_attempt and prev_attempt and latest_attempt.score is not None and prev_attempt.score is not None:
                diff = float(latest_attempt.score) - float(prev_attempt.score)
                if diff > 1.0:
                    trend = "improving"
                elif diff < -1.0:
                    trend = "declining"
                else:
                    trend = "consistent"
            elif latest_attempt:
                trend = "consistent"
            else:
                trend = "new"

            skill_name = a.skill.name if a.skill else (a.topic.name if a.topic else None)

            assessments_data.append({
                "id": str(a.id),
                "title": a.title,
                "description": a.description,
                "difficulty_level": a.difficulty_level,
                "passing_score": float(a.passing_score),
                "skill_name": skill_name,
                "questions_count": a.questions.count(),
                "attempts_count": len(attempts_list),
                "latest_score": latest_score,
                "trend": trend,
            })

        available_skills = []
        if active_domain:
            domain_topics = active_domain.get_all_topics()
            available_skills = list(Skill.objects.filter(topic__in=domain_topics).select_related("topic").order_by("topic__order", "order"))
        else:
            available_skills = list(Skill.objects.all().select_related("topic")[:50])

        context = {
            "current_nav": "assessments",
            "active_domain": active_domain,
            "assessments_data": assessments_data,
            "available_skills": available_skills,
            "past_attempts": past_attempts,
        }
        return render(request, "pages/assessments.html", context)


class StartSkillAssessmentView(LoginRequiredMixin, View):
    """Initializes or opens an on-demand assessment for a given skill and difficulty."""
    login_url = "/login/"

    def get(self, request, skill_id):
        skill = get_object_or_404(Skill, pk=skill_id)
        difficulty = request.GET.get("difficulty", "easy")
        assessment = SequentialQuestionGenerationService.get_or_create_skill_assessment(
            skill=skill,
            difficulty_level=difficulty,
        )
        return redirect("web-assessment-take", pk=assessment.id)

    def post(self, request):
        skill_id = request.POST.get("skill_id")
        skill = get_object_or_404(Skill, pk=skill_id)
        difficulty = request.POST.get("difficulty", "easy")
        assessment = SequentialQuestionGenerationService.get_or_create_skill_assessment(
            skill=skill,
            difficulty_level=difficulty,
        )
        return redirect("web-assessment-take", pk=assessment.id)


class AssessmentTakeView(LoginRequiredMixin, View):
    """Focused one-question-at-a-time interactive test runner."""
    login_url = "/login/"

    def get(self, request, pk):
        assessment = get_object_or_404(
            Assessment.objects.select_related("skill", "topic", "skill__topic", "skill__topic__domain").prefetch_related("questions"),
            pk=pk
        )

        # Check for uncompleted active attempt or create a new attempt
        attempt = Attempt.objects.filter(assessment=assessment, completed_at__isnull=True).order_by("-started_at").first()
        if not attempt:
            attempt = AssessmentEngineService.start_attempt(assessment_id=assessment.id)

        questions = list(assessment.questions.all().order_by("order"))

        # Pre-load existing answers for this attempt if resuming
        answers_dict = {
            str(a.question_id): {
                "user_response": a.user_response,
                "is_correct": a.is_correct,
                "feedback": a.feedback,
                "response_time_seconds": a.response_time_seconds,
            }
            for a in attempt.answers.all()
        }

        questions_data = [
            {
                "id": str(q.id),
                "order": q.order,
                "question_type": q.question_type,
                "concept": q.concept or "",
                "prompt": q.prompt,
                "options": q.options or [],
                "points": q.points,
            }
            for q in questions
        ]

        context = {
            "assessment": assessment,
            "attempt": attempt,
            "skill": assessment.skill,
            "difficulty": assessment.difficulty_level,
            "target_questions_count": assessment.target_questions_count or 10,
            "pills_range": range(1, (assessment.target_questions_count or 10) + 1),
            "questions_count": len(questions_data),
            "questions_json": questions_data,
            "questions_json_escaped": json.dumps(questions_data),
            "initial_answers_json": json.dumps(answers_dict),
        }
        return render(request, "pages/assessment_take.html", context)


class AssessmentResultView(LoginRequiredMixin, View):
    """Comprehensive post-assessment performance evaluation and knowledge calibration."""
    login_url = "/login/"

    def get(self, request, attempt_id):
        attempt = get_object_or_404(
            Attempt.objects.select_related("assessment", "assessment__skill", "assessment__topic", "assessment__skill__topic__domain"),
            pk=attempt_id
        )

        # Finalize attempt if not yet completed
        if not attempt.completed_at:
            AssessmentEngineService.complete_attempt(attempt_id=attempt.id)
            attempt.refresh_from_db()

        assessment = attempt.assessment
        skill = assessment.skill
        target_count = assessment.target_questions_count or 10
        questions = list(assessment.questions.filter(order__lte=target_count).order_by("order"))
        answers_map = {a.question_id: a for a in attempt.answers.select_related("question").all()}

        answers_breakdown = []
        strong_areas = []
        weak_areas = []

        for q in questions:
            ans = answers_map.get(q.id)
            is_correct = ans.is_correct if ans else False
            accuracy = ans.accuracy if ans else 0.0
            score_awarded = float(ans.score_awarded) if ans else 0.0
            user_response = ans.user_response if ans else ""
            feedback = ans.feedback if ans else ""
            concept_name = q.concept or (skill.name if skill else "General")

            # Rubric explanation extraction
            rubric_exp = ""
            if isinstance(q.rubric, dict):
                rubric_exp = q.rubric.get("explanation") or q.rubric.get("key_points") or ""
                if isinstance(rubric_exp, list):
                    rubric_exp = "; ".join(str(item) for item in rubric_exp)

            item = {
                "order": q.order,
                "prompt": q.prompt,
                "concept": concept_name,
                "question_type": q.question_type.upper(),
                "user_response": user_response,
                "correct_answer": q.correct_answer,
                "rubric_explanation": rubric_exp,
                "score_awarded": score_awarded,
                "points_possible": q.points,
                "accuracy_pct": int(round(accuracy * 100)),
                "is_correct": is_correct,
                "feedback": feedback,
            }
            answers_breakdown.append(item)

            if is_correct or accuracy >= 0.8:
                strong_areas.append({
                    "title": f"Q{q.order} [{concept_name}]: {q.prompt[:55]}...",
                    "description": f"Mastered with {int(round(accuracy * 100))}% accuracy.",
                })
            else:
                weak_areas.append({
                    "title": f"Q{q.order} [{concept_name}]: {q.prompt[:55]}...",
                    "description": feedback or "Scored below passing benchmark.",
                })

        # Calibrated skill connection
        skill_mastery = None
        if skill:
            skill_mastery = CalculatedMastery.objects.filter(skill=skill).first()

        # Recommended curated learning resources
        verified_resources = []
        if skill:
            verified_resources = list(skill.get_verified_resource_mappings())

        # Next difficulty progression
        curr_diff = (assessment.difficulty_level or "easy").lower().strip()
        next_difficulty = None
        if attempt.passed:
            if curr_diff in ("easy", "basic", "beginner"):
                next_difficulty = "medium"
            elif curr_diff in ("medium", "intermediate"):
                next_difficulty = "hard"

        # Next skill progression
        next_skill = None
        if skill:
            domain_to_check = topic.domain if topic else None
            next_skill = skill.get_next_skill(domain=domain_to_check)

        # Recommended actions
        recommended_actions = []
        if skill:
            pending_recs = Recommendation.objects.filter(skill=skill, status=Recommendation.Status.PENDING)[:2]
            recommended_actions.extend(list(pending_recs))

        if not recommended_actions:
            if not attempt.passed:
                recommended_actions.append({
                    "title": f"Revise {skill.name if skill else 'curriculum'}",
                    "description": f"Focus especially on weak concepts: {', '.join(attempt.weak_concepts) if attempt.weak_concepts else 'fundamental definitions'}.",
                    "priority": "high",
                    "action_type": "revise_topic",
                    "skill": skill,
                })
                recommended_actions.append({
                    "title": f"Retake {assessment.title}",
                    "description": "Re-calibrate your mastery score by retaking this diagnostic assessment.",
                    "priority": "medium",
                    "action_type": "reassess_skill",
                    "assessment": assessment,
                    "skill": skill,
                })
            else:
                if next_difficulty:
                    recommended_actions.append({
                        "title": f"Advance to {next_difficulty.capitalize()} Assessment",
                        "description": f"You mastered {curr_diff.capitalize()}! Challenge yourself with {next_difficulty.capitalize()} questions.",
                        "priority": "high",
                        "action_type": "advance_difficulty",
                        "skill": skill,
                    })
                elif next_skill:
                    recommended_actions.append({
                        "title": f"Proceed to Next Skill: {next_skill.name}",
                        "description": f"Continue your roadmap progression to {next_skill.name}.",
                        "priority": "high",
                        "action_type": "next_skill",
                        "skill": next_skill,
                    })

        correct_count = sum(1 for item in answers_breakdown if item["is_correct"])
        total_q = len(answers_breakdown)
        accuracy_pct = int(round((correct_count / total_q * 100))) if total_q > 0 else 0

        context = {
            "attempt": attempt,
            "assessment": assessment,
            "answers_breakdown": answers_breakdown,
            "accuracy_percentage": accuracy_pct,
            "correct_count": correct_count,
            "total_questions_count": total_q,
            "concept_scores": attempt.concept_scores,
            "weak_concepts": attempt.weak_concepts,
            "verified_resources": verified_resources,
            "next_difficulty": next_difficulty,
            "next_skill": next_skill,
            "strong_areas": strong_areas,
            "weak_areas": weak_areas,
            "skill_mastery": skill_mastery,
            "recommended_actions": recommended_actions,
        }
        return render(request, "pages/assessment_result.html", context)


class ChatView(LoginRequiredMixin, View):
    """RAG AI Chat assistant interface with session history and skill context pre-fill."""
    login_url = "/login/"

    def get(self, request):
        active_domain = Domain.objects.filter(is_selected=True).first() or Domain.objects.first()
        conversations = Conversation.objects.all().prefetch_related("messages").order_by("-updated_at")[:30]

        skill_id = request.GET.get("skill_id")
        context_name = request.GET.get("context", "")

        context_skill = None
        if skill_id:
            context_skill = Skill.objects.filter(id=skill_id).first()
            if context_skill and not context_name:
                context_name = context_skill.name

        active_conv_id = request.GET.get("conversation_id", "")

        context = {
            "current_nav": "chat",
            "active_domain": active_domain,
            "conversations": conversations,
            "context_skill_id": str(context_skill.id) if context_skill else (skill_id or ""),
            "context_skill_name": context_name,
            "active_conversation_id": active_conv_id,
        }
        return render(request, "pages/chat.html", context)


class KnowledgeGraphView(LoginRequiredMixin, View):
    """
    Personal Performance Knowledge Graph & Question Memory View:
    1. Need-to-Learn Queue: Diagnostic questions answered incorrectly, queued for re-testing.
    2. Mastered Graph: Questions answered correctly and retained.
    3. Retains roadmap gaps and recommendations for curriculum alignment.
    """
    login_url = "/login/"

    def get(self, request):
        from apps.knowledge.services.knowledge_graph import KnowledgeGraphService

        active_domain = Domain.objects.filter(is_selected=True).first() or Domain.objects.first()
        active_tab = request.GET.get("tab", "")

        # 1. Performance Memory Data
        knowledge_stats = KnowledgeGraphService.get_user_knowledge_stats(domain=active_domain)
        need_to_learn_items = KnowledgeGraphService.get_need_to_learn_queue(domain=active_domain)
        mastered_items = KnowledgeGraphService.get_mastered_nodes(domain=active_domain)

        if not active_tab:
            active_tab = "need_to_learn" if need_to_learn_items else "mastered"

        # 2. Existing Gap & Recommendation data for backward compatibility
        gaps_qs = KnowledgeGap.objects.filter(status=KnowledgeGap.Status.ACTIVE).select_related("skill", "topic").prefetch_related("recommendations").order_by("-identified_at")

        if active_domain:
            domain_topics = active_domain.get_all_topics()
            gaps_qs = gaps_qs.filter(Q(skill__topic__in=domain_topics) | Q(topic__in=domain_topics))

        high_gaps = []
        medium_gaps = []
        low_gaps = []

        for gap in gaps_qs:
            assessment = None
            if gap.skill:
                assessment = gap.skill.assessments.filter(is_active=True).first()

            ev_count = 0
            if gap.skill:
                ev_count = gap.skill.evidence_items.count()
            elif gap.topic:
                ev_count = gap.topic.evidence_items.count()

            gap_data = {
                "id": str(gap.id),
                "title": gap.title,
                "description": gap.description,
                "severity": gap.severity,
                "current_level": gap.current_level,
                "current_score": float(gap.current_score),
                "target_score": float(gap.target_score),
                "skill": gap.skill,
                "topic": gap.topic,
                "assessment_id": str(assessment.id) if assessment else None,
                "evidence_count": ev_count,
            }

            if gap.severity in [KnowledgeGap.Severity.CRITICAL, KnowledgeGap.Severity.HIGH]:
                high_gaps.append(gap_data)
            elif gap.severity == KnowledgeGap.Severity.MEDIUM:
                medium_gaps.append(gap_data)
            else:
                low_gaps.append(gap_data)

        recommendations = Recommendation.objects.filter(status=Recommendation.Status.PENDING).select_related("skill", "topic", "assessment", "source").order_by("-created_at")[:6]

        context = {
            "current_nav": "knowledge_graph",
            "active_tab": active_tab,
            "active_domain": active_domain,
            "knowledge_stats": knowledge_stats,
            "need_to_learn_items": need_to_learn_items,
            "mastered_items": mastered_items,
            "high_gaps": high_gaps,
            "medium_gaps": medium_gaps,
            "low_gaps": low_gaps,
            "total_gaps_count": len(high_gaps) + len(medium_gaps) + len(low_gaps),
            "high_gaps_count": len(high_gaps),
            "recommendations": recommendations,
        }
        return render(request, "pages/gaps.html", context)


KnowledgeGapsView = KnowledgeGraphView


class SettingsView(LoginRequiredMixin, View):
    """System preferences and runtime configuration."""
    login_url = "/login/"

    def get(self, request):
        from apps.rag.llm import get_system_ai_config
        active_domain = Domain.objects.filter(is_selected=True).first() or Domain.objects.first()
        ai_cfg = get_system_ai_config()
        context = {
            "current_nav": "settings",
            "active_domain": active_domain,
            "db_engine": settings.DATABASES["default"]["ENGINE"].split(".")[-1],
            "data_dir": str(getattr(settings, "DATA_DIR", "/data")),
            "db_name": str(settings.DATABASES["default"]["NAME"]),
            "local_user": request.user,
            "ai_config": ai_cfg,
        }
        return render(request, "pages/settings.html", context)

    def post(self, request):
        action = request.POST.get("action", "")

        if action == "save_ai":
            from apps.rag.llm import save_system_ai_config
            gemini_key = request.POST.get("gemini_api_key", "").strip()
            gemini_model = request.POST.get("gemini_model", "gemini-1.5-flash").strip()
            ollama_url = request.POST.get("ollama_base_url", "").strip()
            ollama_model = request.POST.get("ollama_model", "llama3.2").strip()

            is_docker = os.getenv("DOCKER_CONTAINER") == "1" or os.path.exists("/.dockerenv")
            default_ollama = "http://host.docker.internal:11434" if is_docker else "http://127.0.0.1:11434"
            updates = {
                "llm_provider": "auto",
                "gemini_api_key": gemini_key,
                "gemini_model": gemini_model or "gemini-1.5-flash",
                "ollama_base_url": ollama_url or default_ollama,
                "ollama_model": ollama_model or "llama3.2",
            }
            save_system_ai_config(updates)
            if gemini_key:
                status_msg = f"Cloud (Gemini: {gemini_model or 'gemini-1.5-flash'}) active by default for all tasks, with Local (Ollama) fallback."
            else:
                status_msg = f"Local model (Ollama: {ollama_model or 'llama3.2'}) active for all tasks."
            messages.success(request, f"AI configuration saved. {status_msg}")
            return redirect("web-settings")

        new_username = request.POST.get("username", "").strip()
        if new_username and new_username != request.user.username:
            request.user.username = new_username
            request.user.save(update_fields=["username"])
            messages.success(request, f"Workspace user renamed to '{new_username}'.")

        return redirect("web-settings")




class ReseedRoadmapView(LoginRequiredMixin, View):
    """POST trigger to reseed standard curriculum roadmap."""
    login_url = "/login/"

    def post(self, request):
        call_command("seed_roadmap")
        messages.success(request, "Curriculum roadmap and benchmark assessments re-seeded successfully!")
        return redirect("web-settings")


class SelectActiveDomainView(LoginRequiredMixin, View):
    """Switch active domain globally and redirect back to previous page."""
    login_url = "/login/"

    def post(self, request):
        domain_id = request.POST.get("domain_id")
        return self._set_domain(request, domain_id)

    def get(self, request, pk=None):
        domain_id = pk or request.GET.get("domain_id")
        return self._set_domain(request, domain_id)

    def _set_domain(self, request, domain_id):
        domain = Domain.objects.filter(id=domain_id, is_active=True).first()
        if domain:
            Domain.objects.exclude(id=domain.id).update(is_selected=False)
            domain.is_selected = True
            domain.save(update_fields=["is_selected", "updated_at"])
            messages.success(request, f"Active domain switched to: {domain.name}")

        next_url = request.POST.get("next") or request.GET.get("next") or request.META.get("HTTP_REFERER") or "/dashboard/"
        return redirect(next_url)

