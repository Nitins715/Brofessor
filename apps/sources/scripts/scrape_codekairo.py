"""
Scraper script to collect full computer science fundamentals notes from codekairo.com/notes
for DBMS, OS, Computer Networks (CN), and Object-Oriented Programming (OOPS).
Generates both structured Markdown files and professional PDFs using ReportLab.
"""
import os
import re
import sys
import time
import requests
from bs4 import BeautifulSoup
from html import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    KeepTogether,
    Preformatted,
    HRFlowable,
    PageBreak,
)
from reportlab.pdfgen import canvas

BASE_URL = "https://codekairo.com"

SUBJECTS = {
    "DBMS": {
        "title": "Database Management Systems (DBMS)",
        "slug": "dbms",
        "description": "Complete interview and exam preparation notes covering ER models, relational keys, normalization, SQL, transactions, ACID properties, concurrency control, B+ trees, and NoSQL.",
        "modules": [
            "/notes/dbms/introduction-to-dbms",
            "/notes/dbms/er-model",
            "/notes/dbms/keys-in-dbms",
            "/notes/dbms/functional-dependencies",
            "/notes/dbms/normalization",
            "/notes/dbms/sql-basics",
            "/notes/dbms/sql-joins",
            "/notes/dbms/sql-aggregation-and-subqueries",
            "/notes/dbms/transactions-and-acid",
            "/notes/dbms/concurrency-control",
            "/notes/dbms/indexing-and-b-plus-trees",
            "/notes/dbms/sql-vs-nosql",
        ],
    },
    "OS": {
        "title": "Operating Systems (OS)",
        "slug": "operating-systems",
        "description": "Complete operating systems curriculum covering processes, threads, CPU scheduling algorithms, process synchronization, classic deadlocks, inter-process communication, paging, virtual memory, and file systems.",
        "modules": [
            "/notes/operating-systems/introduction-to-operating-systems",
            "/notes/operating-systems/processes-and-threads",
            "/notes/operating-systems/cpu-scheduling",
            "/notes/operating-systems/process-synchronization",
            "/notes/operating-systems/classic-synchronization-problems",
            "/notes/operating-systems/deadlocks",
            "/notes/operating-systems/inter-process-communication",
            "/notes/operating-systems/memory-management",
            "/notes/operating-systems/virtual-memory",
            "/notes/operating-systems/page-replacement-algorithms",
            "/notes/operating-systems/disk-scheduling",
            "/notes/operating-systems/file-systems",
        ],
    },
    "CN": {
        "title": "Computer Networks (CN)",
        "slug": "computer-networks",
        "description": "Complete computer networking guide covering OSI vs TCP/IP models, Data Link framing, IP addressing, subnetting, routing algorithms, TCP vs UDP, DNS resolution, HTTP/HTTPS, NAT/DHCP, and network security fundamentals.",
        "modules": [
            "/notes/computer-networks/introduction-to-computer-networks",
            "/notes/computer-networks/osi-model",
            "/notes/computer-networks/tcp-ip-model",
            "/notes/computer-networks/data-link-layer",
            "/notes/computer-networks/ip-addressing-and-subnetting",
            "/notes/computer-networks/routing-algorithms",
            "/notes/computer-networks/tcp-and-udp",
            "/notes/computer-networks/dns",
            "/notes/computer-networks/http-and-https",
            "/notes/computer-networks/nat-dhcp-and-ports",
            "/notes/computer-networks/network-security-basics",
            "/notes/computer-networks/what-happens-when-you-type-a-url",
        ],
    },
    "OOPS": {
        "title": "Object-Oriented Programming (OOPS)",
        "slug": "oop",
        "description": "Comprehensive Object-Oriented Programming and Design guide covering Classes, Objects, Encapsulation, Abstraction, Inheritance, Polymorphism, SOLID principles, GoF design patterns, Composition, and Exception Handling.",
        "modules": [
            "/notes/oop/introduction-to-oop",
            "/notes/oop/classes-and-objects",
            "/notes/oop/encapsulation",
            "/notes/oop/abstraction",
            "/notes/oop/inheritance",
            "/notes/oop/polymorphism",
            "/notes/oop/solid-principles",
            "/notes/oop/design-patterns",
            "/notes/oop/association-aggregation-composition",
            "/notes/oop/object-equality-and-copying",
            "/notes/oop/exception-handling",
        ],
    },
}

class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and print 'Page X of Y' in footer."""
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
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#71717A"))
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "Brofessor Curated Knowledge Pack — CodeKairo Notes")
            self.setStrokeColor(colors.HexColor("#E4E4E7"))
            self.setLineWidth(0.5)
            self.line(54, 744, 558, 744)

        # Footer
        text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 36, text)
        self.drawString(54, 36, "Licensed for Educational & Personal Study • Brofessor PKS")
        self.setStrokeColor(colors.HexColor("#E4E4E7"))
        self.setLineWidth(0.5)
        self.line(54, 46, 558, 46)
        self.restoreState()


def scrape_module(path: str) -> dict:
    url = f"{BASE_URL}{path}"
    print(f"  Fetching: {url}")
    try:
        resp = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
            timeout=15,
        )
        if resp.status_code != 200:
            print(f"  Warning: HTTP {resp.status_code} for {url}")
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
        
        art = soup.find("article") or soup.find("main")
        if not art:
            return None

        # Extract title
        h1 = art.find("h1")
        title = h1.get_text(" ", strip=True) if h1 else path.split("/")[-1].replace("-", " ").title()

        # Extract content sections
        # Skip breadcrumbs nav
        for nav in art.find_all("nav"):
            nav.decompose()
        for bc in art.find_all("ol", class_=re.compile(r"breadcrumb", re.I)):
            bc.decompose()

        sections = []
        current_heading = "Overview"
        current_elements = []

        # Find starting point after h1
        start_node = h1 if h1 else art

        for el in art.find_all(["h2", "h3", "p", "ul", "ol", "pre", "table"]):
            # Ignore breadcrumbs or navigation links
            if el.find_parent("nav"):
                continue

            tag = el.name
            if tag in ["h2", "h3"]:
                if current_elements:
                    sections.append({
                        "heading": current_heading,
                        "elements": current_elements
                    })
                    current_elements = []
                current_heading = el.get_text(" ", strip=True)
            elif tag == "p":
                txt = el.get_text(" ", strip=True)
                if txt and not txt.startswith("Home ›") and not "Note " in txt and not "min read" in txt:
                    current_elements.append(("p", txt))
            elif tag in ["ul", "ol"]:
                lis = [li.get_text(" ", strip=True) for li in el.find_all("li") if li.get_text(" ", strip=True)]
                if lis:
                    current_elements.append(("list", lis))
            elif tag == "pre":
                code = el.get_text("\n", strip=True)
                if code:
                    current_elements.append(("code", code))

        if current_elements:
            sections.append({
                "heading": current_heading,
                "elements": current_elements
            })

        return {
            "title": title,
            "url": url,
            "sections": sections,
        }
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return None


def generate_markdown(subject_key: str, subject_info: dict, modules_data: list, output_path: str):
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# {subject_info['title']}\n\n")
        f.write(f"> **Source**: [CodeKairo CS Notes]({BASE_URL}/notes/{subject_info['slug']})  \n")
        f.write(f"> **Overview**: {subject_info['description']}\n\n")
        f.write("---\n\n")
        f.write("## Table of Modules\n\n")
        for i, mod in enumerate(modules_data, 1):
            f.write(f"{i}. [{mod['title']}](#module-{i}-{mod['title'].lower().replace(' ', '-').replace(':', '')})\n")
        f.write("\n---\n\n")

        for i, mod in enumerate(modules_data, 1):
            f.write(f"## Module {i}: {mod['title']}\n\n")
            f.write(f"*Original URL: {mod['url']}*\n\n")
            for sec in mod["sections"]:
                f.write(f"### {sec['heading']}\n\n")
                for kind, val in sec["elements"]:
                    if kind == "p":
                        f.write(f"{val}\n\n")
                    elif kind == "list":
                        for item in val:
                            f.write(f"- {item}\n")
                        f.write("\n")
                    elif kind == "code":
                        f.write(f"```\n{val}\n```\n\n")
            f.write("\n---\n\n")
    print(f"Saved Markdown: {output_path} ({os.path.getsize(output_path)} bytes)")


def generate_pdf(subject_key: str, subject_info: dict, modules_data: list, output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#18181B"),
        spaceAfter=8,
    )
    subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=16,
        textColor=colors.HexColor("#52525B"),
        spaceAfter=14,
    )
    mod_heading_style = ParagraphStyle(
        "ModuleHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=19,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )
    sec_heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#334155"),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#27272A"),
        spaceAfter=5,
    )
    bullet_style = ParagraphStyle(
        "Bullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#27272A"),
        leftIndent=15,
        spaceAfter=2,
    )
    code_style = ParagraphStyle(
        "CodeBlock",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#1E293B"),
        backColor=colors.HexColor("#F1F5F9"),
        borderPadding=6,
        spaceBefore=4,
        spaceAfter=6,
    )

    story = []

    # Title block
    story.append(Paragraph(escape(subject_info["title"]), title_style))
    story.append(Paragraph(f"<b>Comprehensive Study Notes & Interview Guide</b> • CodeKairo Reference", subtitle_style))
    story.append(Paragraph(escape(subject_info["description"]), body_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1"), spaceBefore=6, spaceAfter=12))

    # Modules Table of Contents Overview
    story.append(Paragraph("<b>Table of Modules</b>", sec_heading_style))
    for i, mod in enumerate(modules_data, 1):
        story.append(Paragraph(f"&bull; <b>Module {i}:</b> {escape(mod['title'])}", bullet_style))
    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E2E8F0"), spaceAfter=14))

    # Build Modules
    for i, mod in enumerate(modules_data, 1):
        mod_block = []
        mod_block.append(Paragraph(f"Module {i}: {escape(mod['title'])}", mod_heading_style))
        mod_block.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor("#94A3B8"), spaceAfter=6))

        for sec in mod["sections"]:
            mod_block.append(Paragraph(escape(sec["heading"]), sec_heading_style))
            for kind, val in sec["elements"]:
                if kind == "p":
                    mod_block.append(Paragraph(escape(val), body_style))
                elif kind == "list":
                    for item in val:
                        mod_block.append(Paragraph(f"&bull; {escape(item)}", bullet_style))
                    mod_block.append(Spacer(1, 2))
                elif kind == "code":
                    clean_code = escape(val[:1200])  # Cap code snippet length for PDF box
                    mod_block.append(Preformatted(clean_code, code_style))

        mod_block.append(Spacer(1, 10))
        story.extend(mod_block)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Saved PDF: {output_path} ({os.path.getsize(output_path)} bytes)")


def main():
    target_dir = os.path.join("apps", "sources", "data", "starter_pack")
    os.makedirs(target_dir, exist_ok=True)

    print("==============================================================")
    print("  CodeKairo Notes Scraper & Starter Knowledge Generator       ")
    print("==============================================================")

    for subj_key, subj_info in SUBJECTS.items():
        print(f"\nProcessing Subject: {subj_key} ({subj_info['title']})...")
        modules_data = []

        for mod_path in subj_info["modules"]:
            data = scrape_module(mod_path)
            if data:
                modules_data.append(data)
            time.sleep(0.3)  # Polite crawling delay

        if not modules_data:
            print(f"Warning: No module data collected for {subj_key}")
            continue

        md_path = os.path.join(target_dir, f"{subj_key}_Complete_Notes.md")
        pdf_path = os.path.join(target_dir, f"{subj_key}_Complete_Notes.pdf")

        generate_markdown(subj_key, subj_info, modules_data, md_path)
        generate_pdf(subj_key, subj_info, modules_data, pdf_path)

    print("\nAll 4 subjects scraped and generated successfully in:", target_dir)


if __name__ == "__main__":
    main()
