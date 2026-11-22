import io
import re
from typing import Any, Dict, List, Optional
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable,
)
from reportlab.pdfgen import canvas

from apps.roadmap.models import Topic, Skill
from apps.assessments.models import Question


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and stamp total page count (Page X of Y)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Running header on pages after page 1
        if self._pageNumber > 1:
            self.drawString(40, 755, "Brofessor AI — Technical Interview Cheat Sheet")
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(40, 750, 572, 750)

        # Running footer
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(572, 30, page_str)
        self.drawString(40, 30, "Brofessor Learning & Technical Interview Series • Confidential Preparation Material")
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(40, 40, 572, 40)
        self.restoreState()


class CheatSheetService:
    """
    Generates high-yield, interview-ready cheat sheets for any curriculum Topic.
    Outputs:
    - Structured Markdown (.md)
    - Styled 2-3 page Printable PDF via ReportLab
    """

    TRACK_THEME_COLORS = {
        "swe_foundations": {"primary": "#1d4ed8", "secondary": "#eff6ff", "badge": "#3b82f6"},
        "ai_engineer": {"primary": "#047857", "secondary": "#ecfdf5", "badge": "#10b981"},
        "agentic_ai": {"primary": "#6d28d9", "secondary": "#f5f3ff", "badge": "#8b5cf6"},
        "mlops": {"primary": "#b45309", "secondary": "#fffbeb", "badge": "#f59e0b"},
        "fde": {"primary": "#be123c", "secondary": "#fff1f2", "badge": "#f43f5e"},
    }

    @classmethod
    def get_cheat_sheet_data(cls, topic: Topic) -> Dict[str, Any]:
        """
        Gathers core definitions, high-yield interview questions, pitfalls,
        and code patterns for all skills under a topic.
        """
        skills = list(
            topic.skills.all()
            .prefetch_related("prerequisites", "learning_resources", "assessments")
            .order_by("order", "created_at")
        )

        skill_entries = []
        all_questions = []
        pitfalls = []

        for skill in skills:
            # Parse key concepts
            concepts = []
            if isinstance(skill.key_concepts, list):
                concepts = [str(c) for c in skill.key_concepts if str(c).strip()]
            elif isinstance(skill.key_concepts, str) and skill.key_concepts.strip():
                concepts = [c.strip() for c in skill.key_concepts.split(",") if c.strip()]
            if not concepts:
                concepts = [skill.name]

            # Parse interview relevance or generate high-yield points
            interview_relevance = ""
            if isinstance(skill.interview_relevance, str) and skill.interview_relevance.strip():
                interview_relevance = skill.interview_relevance.strip()

            # Active assessment questions
            questions = list(
                Question.objects.filter(
                    assessment__skill=skill,
                    assessment__is_active=True,
                ).order_by("order", "created_at")[:3]
            )

            for q in questions:
                explanation = ""
                if isinstance(q.distractor_explanations, dict):
                    explanation = q.distractor_explanations.get("correct") or q.distractor_explanations.get("general") or ""
                all_questions.append({
                    "skill_name": skill.name,
                    "prompt": q.prompt,
                    "answer": q.correct_answer or "Comprehensive conceptual mastery required.",
                    "explanation": explanation or q.rubric or "Standard technical interview benchmark question.",
                    "difficulty": q.difficulty_level,
                })

            # Derive default interview question if none cached yet
            if not questions:
                all_questions.append({
                    "skill_name": skill.name,
                    "prompt": f"Explain the core architectural principles, trade-offs, and failure modes of {skill.name}.",
                    "answer": skill.description or f"{skill.name} provides critical foundation in modern software and AI pipelines.",
                    "explanation": f"Interviewers assess deep mental models of {skill.name}, including complexity and scaling edge cases.",
                    "difficulty": skill.difficulty_level,
                })

            # Derive technical pitfalls
            pitfalls.append({
                "skill_name": skill.name,
                "pitfall": f"Overlooking edge cases or scaling bottlenecks in {skill.name}.",
                "fix": f"Always state Big-O space/time trade-offs and verify boundary conditions for {skill.name}.",
            })

            # Resources
            resources = [
                {"title": r.title, "url": r.url, "type": r.resource_type}
                for r in skill.learning_resources.all()[:2]
            ]

            skill_entries.append({
                "id": str(skill.id),
                "name": skill.name,
                "difficulty": skill.difficulty_level,
                "priority": skill.priority,
                "description": skill.description or "",
                "concepts": concepts,
                "interview_relevance": interview_relevance,
                "prerequisites": [p.name for p in skill.prerequisites.all()],
                "resources": resources,
            })

        track_code = topic.track or "swe_foundations"
        track_display = topic.get_track_display() if hasattr(topic, "get_track_display") else track_code.replace("_", " ").title()

        return {
            "topic_id": str(topic.id),
            "topic_name": topic.name,
            "topic_slug": topic.slug,
            "track_code": track_code,
            "track_display": track_display,
            "description": topic.description or "Comprehensive mastery notes and technical interview preparation guide.",
            "skills": skill_entries,
            "skills_count": len(skill_entries),
            "interview_questions": all_questions[:8],
            "pitfalls": pitfalls[:6],
            "generated_at": timezone.now().strftime("%B %d, %Y"),
        }

    @classmethod
    def generate_markdown(cls, topic: Topic) -> str:
        """Renders the cheat sheet as a downloadable GitHub-flavored Markdown document."""
        data = cls.get_cheat_sheet_data(topic)

        lines = []
        lines.append(f"# {data['topic_name']} — Technical Interview Cheat Sheet")
        lines.append("")
        lines.append(f"> **Track**: `{data['track_display']}`  ")
        lines.append(f"> **Domain Focus**: Technical Interview Preparation & Architecture Review  ")
        lines.append(f"> **Generated**: {data['generated_at']} | Brofessor Knowledge Engine  ")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 1. Executive Conceptual Map & High-Yield Summary")
        lines.append("")
        lines.append(f"{data['description']}")
        lines.append("")
        lines.append("| Skill / Core Concept | Difficulty | Priority | Key Terms & Architectural Primitives |")
        lines.append("|:---|:---:|:---:|:---|")

        for s in data["skills"]:
            concepts_str = ", ".join(s["concepts"][:4]) if s["concepts"] else s["name"]
            lines.append(f"| **{s['name']}** | `{s['difficulty']}` | `{s['priority']}` | {concepts_str} |")

        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 2. Core Technical Definitions & Concept Breakdowns")
        lines.append("")

        for s in data["skills"]:
            lines.append(f"### {s['name']}")
            lines.append(f"- **Overview**: {s['description']}")
            if s["prerequisites"]:
                lines.append(f"- **Prerequisites**: {', '.join(s['prerequisites'])}")
            if s["concepts"]:
                lines.append(f"- **Key Concepts**: {', '.join(s['concepts'])}")
            if s["interview_relevance"]:
                lines.append(f"- **Interview Focus**: {s['interview_relevance']}")
            lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("## 3. High-Frequency Technical Interview Questions & Model Answers")
        lines.append("")

        for idx, q in enumerate(data["interview_questions"], 1):
            lines.append(f"#### Q{idx}: {q['prompt']}")
            lines.append(f"**Target Concept**: `{q['skill_name']}` | Level: `{q['difficulty']}`")
            lines.append("")
            lines.append(f"> **Model Answer**:")
            lines.append(f"> {q['answer']}")
            lines.append("")
            lines.append(f"*Evaluation Rubric & Follow-Up Context*: {q['explanation']}")
            lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("## 4. Critical Interview Traps, Common Pitfalls & Anti-Patterns")
        lines.append("")

        for p in data["pitfalls"]:
            lines.append(f"- **Trap ({p['skill_name']})**: {p['pitfall']}")
            lines.append(f"  - **Ideal Answer / Mitigation**: {p['fix']}")

        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 5. Curated Study & Reference Materials")
        lines.append("")

        seen_urls = set()
        for s in data["skills"]:
            for r in s["resources"]:
                if r["url"] not in seen_urls:
                    seen_urls.add(r["url"])
                    lines.append(f"- [{r['title']}]({r['url']}) — *{r['type'].replace('_', ' ').title()}*")

        lines.append("")
        lines.append("---")
        lines.append("*Generated by Brofessor • Continuous Technical Mastery Engine*")
        return "\n".join(lines)

    @classmethod
    def generate_pdf(cls, topic: Topic) -> bytes:
        """Renders the cheat sheet as a publication-ready PDF using ReportLab Platypus."""
        data = cls.get_cheat_sheet_data(topic)
        theme = cls.TRACK_THEME_COLORS.get(data["track_code"], cls.TRACK_THEME_COLORS["swe_foundations"])

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=40,
            rightMargin=40,
            topMargin=45,
            bottomMargin=45,
        )

        styles = getSampleStyleSheet()

        # Custom typography styles
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=colors.HexColor(theme["primary"]),
            spaceAfter=4,
        )

        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#64748b"),
            spaceAfter=12,
        )

        section_heading = ParagraphStyle(
            "SectionHeading",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=colors.HexColor(theme["primary"]),
            spaceBefore=10,
            spaceAfter=6,
        )

        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11.5,
            textColor=colors.HexColor("#1e293b"),
        )

        table_header_style = ParagraphStyle(
            "TableHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=colors.white,
        )

        q_prompt_style = ParagraphStyle(
            "QPrompt",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=3,
        )

        q_answer_style = ParagraphStyle(
            "QAnswer",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#1e293b"),
        )

        pitfall_style = ParagraphStyle(
            "Pitfall",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10.5,
            textColor=colors.HexColor("#334155"),
        )

        story = []

        # Header Block
        story.append(Paragraph(data["topic_name"], title_style))
        track_meta = f"TRACK: {data['track_display'].upper()} • TOPIC INTERVIEW CHEAT SHEET • {data['skills_count']} CORE SKILLS"
        story.append(Paragraph(track_meta, subtitle_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor(theme["primary"]), spaceAfter=10))

        # Executive Overview Summary Box
        overview_text = (
            f"<b>Core Overview:</b> {data['description']}<br/>"
            f"<b>Preparation Target:</b> High-yield interview definitions, trade-offs, architecture questions, and common failure modes."
        )
        overview_table = Table(
            [[Paragraph(overview_text, body_style)]],
            colWidths=[532],
        )
        overview_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(theme["secondary"])),
                ("BORDER", (0, 0), (-1, -1), 0.75, colors.HexColor(theme["badge"])),
                ("PADDING", (0, 0), (-1, -1), 8),
                ("ROUNDEDCORNERS", [4, 4, 4, 4]),
            ])
        )
        story.append(overview_table)
        story.append(Spacer(1, 10))

        # Section 1: Conceptual Map Table
        story.append(Paragraph("1. High-Yield Skill Matrix & Conceptual Map", section_heading))
        table_rows = [
            [
                Paragraph("Skill / Concept", table_header_style),
                Paragraph("Diff", table_header_style),
                Paragraph("Prio", table_header_style),
                Paragraph("Key Primitives & Terms", table_header_style),
            ]
        ]
        for s in data["skills"][:12]:
            concepts_text = ", ".join(s["concepts"][:4]) if s["concepts"] else s["name"]
            table_rows.append([
                Paragraph(f"<b>{s['name']}</b>", body_style),
                Paragraph(s["difficulty"][:3].upper(), body_style),
                Paragraph(s["priority"], body_style),
                Paragraph(concepts_text, body_style),
            ])

        skill_table = Table(table_rows, colWidths=[160, 42, 42, 288])
        skill_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(theme["primary"])),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("PADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ])
        )
        story.append(skill_table)
        story.append(Spacer(1, 12))

        # Section 2: Top Interview Questions & Model Answers
        story.append(Paragraph("2. Top Technical Interview Questions & Model Answers", section_heading))

        for idx, q in enumerate(data["interview_questions"][:5], 1):
            q_box = [
                Paragraph(f"<b>Q{idx}: {q['prompt']}</b>", q_prompt_style),
                Spacer(1, 2),
                Paragraph(f"<b>Answer:</b> {q['answer']}", q_answer_style),
                Spacer(1, 2),
                Paragraph(f"<i>Rubric Context:</i> {q['explanation']}", q_answer_style),
            ]
            q_table = Table([[q_box]], colWidths=[532])
            q_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("LINELEFT", (0, 0), (-1, -1), 2.5, colors.HexColor(theme["primary"])),
                    ("PADDING", (0, 0), (-1, -1), 6),
                ])
            )
            story.append(q_table)
            story.append(Spacer(1, 6))

        story.append(Spacer(1, 6))

        # Section 3: Critical Traps & Common Anti-Patterns
        story.append(Paragraph("3. Common Interview Traps & Pitfalls", section_heading))
        pitfall_rows = []
        for p in data["pitfalls"][:4]:
            pitfall_text = f"<b>Trap ({p['skill_name']}):</b> {p['pitfall']}<br/><b>Key Fix / Edge Case:</b> {p['fix']}"
            pitfall_rows.append([Paragraph(pitfall_text, pitfall_style)])

        pitfall_table = Table(pitfall_rows, colWidths=[532])
        pitfall_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fff1f2")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#fecdd3")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#ffe4e6")),
                ("PADDING", (0, 0), (-1, -1), 5),
            ])
        )
        story.append(pitfall_table)

        doc.build(story, canvasmaker=NumberedCanvas)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
