import io
import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple, Union
from django.utils.text import slugify

from apps.roadmap.models import Domain, Topic, Skill, RoadmapNode, RoadmapProgress

logger = logging.getLogger("brofessor")


class CustomRoadmapImportService:
    """
    Service that processes user-submitted text or documents (PDF, TXT, MD, JSON),
    extracts topics and skills, compares them against the current domain roadmap,
    and idempotently adds only the skills/topics that do not already exist.
    """

    @classmethod
    def extract_text_from_input(cls, text: Optional[str] = None, file_obj: Any = None) -> str:
        """Extract clean text content from direct string input or uploaded file."""
        extracted = ""
        if text and text.strip():
            extracted = text.strip()

        if file_obj:
            filename = getattr(file_obj, "name", "").lower()
            try:
                content_bytes = file_obj.read()
                if hasattr(file_obj, "seek"):
                    file_obj.seek(0)

                if filename.endswith(".pdf"):
                    try:
                        from pypdf import PdfReader
                        reader = PdfReader(io.BytesIO(content_bytes))
                        pdf_parts = [p.extract_text() or "" for p in reader.pages]
                        file_text = "\n".join(pdf_parts)
                    except Exception as e:
                        logger.warning(f"Failed to read PDF with pypdf: {e}")
                        file_text = content_bytes.decode("utf-8", errors="ignore")
                else:
                    file_text = content_bytes.decode("utf-8", errors="ignore")

                if file_text.strip():
                    if extracted:
                        extracted += "\n\n" + file_text.strip()
                    else:
                        extracted = file_text.strip()
            except Exception as e:
                logger.error(f"Error reading uploaded roadmap file: {e}")
                if not extracted:
                    raise ValueError(f"Could not read uploaded file: {str(e)}")

        if not extracted.strip():
            raise ValueError("No roadmap text or readable file content was provided.")

        return extracted.strip()

    @classmethod
    def parse_with_llm(cls, raw_text: str) -> Optional[List[Dict[str, Any]]]:
        """Attempt to parse roadmap hierarchy using the configured LLM provider."""
        try:
            from apps.rag.llm import get_llm_provider
            llm = get_llm_provider()

            prompt = (
                "You are an expert curriculum architect. Analyze the following textual roadmap/syllabus "
                "and extract the structured learning hierarchy of topics and measurable skills.\n"
                "Return ONLY a valid JSON object with the exact schema below, without markdown formatting or commentary:\n"
                "{\n"
                '  "topics": [\n'
                "    {\n"
                '      "name": "Topic Name",\n'
                '      "description": "Short topic description",\n'
                '      "priority": "P0" or "P1" or "P2",\n'
                '      "skills": [\n'
                "        {\n"
                '          "name": "Specific Measurable Skill Name",\n'
                '          "description": "Short description of what the learner will know or build",\n'
                '          "difficulty_level": "beginner" or "intermediate" or "advanced",\n'
                '          "priority": "P0" or "P1" or "P2"\n'
                "        }\n"
                "      ]\n"
                "    }\n"
                "  ]\n"
                "}\n\n"
                f"ROADMAP CONTENT:\n{raw_text[:8000]}"
            )

            resp = llm.generate(prompt=prompt, temperature=0.1)
            content = resp.text.strip()

            # Clean json code block fences if present
            if content.startswith("```"):
                content = re.sub(r"^```(?:json)?\s*", "", content)
                content = re.sub(r"\s*```$", "", content)

            data = json.loads(content)
            if isinstance(data, dict) and "topics" in data and isinstance(data["topics"], list):
                return data["topics"]
        except Exception as e:
            logger.info(f"LLM parsing skipped or failed ({e}); utilizing rule-based parser.")

        return None

    @classmethod
    def parse_with_rules(cls, raw_text: str) -> List[Dict[str, Any]]:
        """
        Robust rule-based parser that handles markdown headings, bullet points,
        colons, and numbered lists into Topics and Skills.
        """
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        topics: List[Dict[str, Any]] = []
        current_topic: Optional[Dict[str, Any]] = None

        for line in lines:
            # Check for Markdown headings: # Topic, ## Topic
            if line.startswith("#"):
                clean_name = re.sub(r"^#+\s*", "", line).strip()
                if clean_name:
                    current_topic = {
                        "name": clean_name,
                        "description": f"Curriculum topic for {clean_name}",
                        "priority": "P1",
                        "skills": [],
                    }
                    topics.append(current_topic)
                continue

            # Check for topic with colon: e.g. "Agentic AI: Function calling, ReAct"
            if ":" in line and not line.startswith(("-", "*", "•")) and len(line.split(":")[0].split()) <= 6:
                parts = line.split(":", 1)
                topic_title = parts[0].strip()
                skill_items = [s.strip() for s in parts[1].split(",") if s.strip()]

                current_topic = {
                    "name": topic_title,
                    "description": f"Curriculum topic for {topic_title}",
                    "priority": "P1",
                    "skills": [],
                }
                topics.append(current_topic)

                for item in skill_items:
                    clean_skill = re.sub(r"^[\d\.\-\*\•\s]+", "", item).strip()
                    if clean_skill:
                        current_topic["skills"].append({
                            "name": clean_skill,
                            "description": f"Skill capability in {clean_skill}",
                            "difficulty_level": "intermediate",
                            "priority": "P1",
                        })
                continue

            # Check for bullet points: -, *, •, 1.
            is_bullet = bool(re.match(r"^[\-\*\•\d+\.]\s+", line))
            if is_bullet:
                clean_skill_name = re.sub(r"^[\-\*\•\d+\.]\s*", "", line).strip()
                if clean_skill_name:
                    if not current_topic:
                        # Create a default topic if none started
                        current_topic = {
                            "name": "Custom Focus Area",
                            "description": "Custom learning pathway",
                            "priority": "P1",
                            "skills": [],
                        }
                        topics.append(current_topic)

                    current_topic["skills"].append({
                        "name": clean_skill_name,
                        "description": f"Learn and master {clean_skill_name}",
                        "difficulty_level": "intermediate",
                        "priority": "P1",
                    })
            else:
                # Standalone line could be a topic or a skill
                if len(line.split()) <= 6 and not current_topic:
                    current_topic = {
                        "name": line,
                        "description": f"Learning topic: {line}",
                        "priority": "P1",
                        "skills": [],
                    }
                    topics.append(current_topic)
                elif current_topic:
                    current_topic["skills"].append({
                        "name": line,
                        "description": f"Skill capability in {line}",
                        "difficulty_level": "intermediate",
                        "priority": "P1",
                    })
                else:
                    current_topic = {
                        "name": "Custom Focus Area",
                        "description": "User requested roadmap",
                        "priority": "P1",
                        "skills": [{
                            "name": line,
                            "description": f"Skill capability in {line}",
                            "difficulty_level": "intermediate",
                            "priority": "P1",
                        }],
                    }
                    topics.append(current_topic)

        # Filter out empty topics
        valid_topics = [t for t in topics if t["skills"]]
        if not valid_topics and topics:
            valid_topics = topics
        return valid_topics

    @classmethod
    def normalize_string(cls, text: str) -> str:
        """Normalize string for robust deduplication comparison."""
        return re.sub(r"[^a-z0-9]", "", text.lower())

    @classmethod
    def import_roadmap(
        cls,
        domain_id: Union[str, Domain],
        text: Optional[str] = None,
        file_obj: Any = None,
    ) -> Dict[str, Any]:
        """
        Main entry point:
        1. Extracts text from input/file.
        2. Parses into topics and skills.
        3. Compares against current domain roadmap.
        4. Adds only missing skills and topics.
        """
        if isinstance(domain_id, Domain):
            domain = domain_id
        else:
            domain = Domain.objects.filter(id=domain_id).first()
            if not domain:
                raise ValueError(f"Domain '{domain_id}' not found.")

        raw_text = cls.extract_text_from_input(text=text, file_obj=file_obj)

        # Parse structure (try LLM first, fallback to rule-based)
        parsed_topics = cls.parse_with_llm(raw_text)
        if not parsed_topics:
            parsed_topics = cls.parse_with_rules(raw_text)

        if not parsed_topics:
            raise ValueError("Could not extract any recognizable topics or skills from the provided input.")

        # Gather existing topics and skills for the domain to prevent duplicates
        existing_topics_qs = domain.get_all_topics() if hasattr(domain, "get_all_topics") else domain.topics.all()
        existing_topic_map: Dict[str, Topic] = {}
        for t in existing_topics_qs:
            existing_topic_map[cls.normalize_string(t.name)] = t
            existing_topic_map[cls.normalize_string(t.slug)] = t

        existing_skills_qs = Skill.objects.filter(topic__in=existing_topics_qs).distinct()
        existing_skill_map: Dict[str, Skill] = {}
        for s in existing_skills_qs:
            existing_skill_map[cls.normalize_string(s.name)] = s
            existing_skill_map[cls.normalize_string(s.slug)] = s

        added_topics = []
        added_skills = []
        existing_skills_found = []

        max_topic_order = existing_topics_qs.count()

        for t_idx, topic_data in enumerate(parsed_topics, start=1):
            topic_name = topic_data.get("name", "").strip()
            if not topic_name:
                continue

            normalized_t_name = cls.normalize_string(topic_name)
            topic = existing_topic_map.get(normalized_t_name)

            if not topic:
                # Create new Topic under this domain
                base_slug = slugify(topic_name) or "custom-topic"
                slug = base_slug
                counter = 1
                while Topic.objects.filter(domain=domain, slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1

                topic = Topic.objects.create(
                    domain=domain,
                    name=topic_name,
                    slug=slug,
                    description=topic_data.get("description", f"User custom topic for {topic_name}"),
                    priority=topic_data.get("priority", "P1"),
                    order=max_topic_order + t_idx,
                )
                existing_topic_map[normalized_t_name] = topic
                existing_topic_map[cls.normalize_string(slug)] = topic
                added_topics.append({
                    "id": str(topic.id),
                    "name": topic.name,
                    "slug": topic.slug,
                    "priority": topic.priority,
                })

            # Process skills for this topic
            max_skill_order = topic.skills.count()
            raw_skills = topic_data.get("skills", [])

            for s_idx, skill_data in enumerate(raw_skills, start=1):
                skill_name = skill_data.get("name", "").strip() if isinstance(skill_data, dict) else str(skill_data).strip()
                if not skill_name:
                    continue

                normalized_s_name = cls.normalize_string(skill_name)

                # Check if skill already exists in this domain
                if normalized_s_name in existing_skill_map:
                    matched_skill = existing_skill_map[normalized_s_name]
                    existing_skills_found.append({
                        "id": str(matched_skill.id),
                        "name": matched_skill.name,
                        "topic_name": matched_skill.topic.name,
                        "status": "already_present",
                    })
                    continue

                # Skill does NOT exist -> Create new skill
                base_slug = slugify(skill_name) or "custom-skill"
                slug = base_slug
                counter = 1
                while Skill.objects.filter(topic=topic, slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1

                desc = skill_data.get("description", "") if isinstance(skill_data, dict) else ""
                diff = skill_data.get("difficulty_level", "intermediate") if isinstance(skill_data, dict) else "intermediate"
                priority = skill_data.get("priority", "P1") if isinstance(skill_data, dict) else "P1"

                new_skill = Skill.objects.create(
                    topic=topic,
                    name=skill_name,
                    slug=slug,
                    description=desc or f"Personalized learning capability: {skill_name}",
                    difficulty_level=diff,
                    priority=priority,
                    order=max_skill_order + s_idx,
                )

                # Ensure RoadmapNode and RoadmapProgress exist for the user
                node, _ = RoadmapNode.objects.get_or_create(
                    skill=new_skill,
                    defaults={
                        "domain": domain,
                        "topic": topic,
                        "order": new_skill.order,
                    },
                )
                RoadmapProgress.objects.get_or_create(
                    node=node,
                    defaults={
                        "status": RoadmapProgress.ProgressStatus.NOT_STARTED,
                        "is_current": False,
                    },
                )

                existing_skill_map[normalized_s_name] = new_skill
                existing_skill_map[cls.normalize_string(slug)] = new_skill

                added_skills.append({
                    "id": str(new_skill.id),
                    "name": new_skill.name,
                    "slug": new_skill.slug,
                    "topic_id": str(topic.id),
                    "topic_name": topic.name,
                    "difficulty_level": new_skill.difficulty_level,
                    "priority": new_skill.priority,
                })

        return {
            "success": True,
            "domain_id": str(domain.id),
            "domain_name": domain.name,
            "added_topics": added_topics,
            "added_skills": added_skills,
            "existing_skills": existing_skills_found,
            "summary": {
                "added_topics_count": len(added_topics),
                "added_skills_count": len(added_skills),
                "existing_skills_count": len(existing_skills_found),
                "total_processed": len(added_skills) + len(existing_skills_found),
            },
        }
