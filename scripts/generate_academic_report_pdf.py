import os
import sys
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
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
        self.setFillColor(colors.HexColor("#555555"))
        # Header (pages 2+)
        if self._pageNumber > 1:
            self.drawString(36, 762, "Examination Management Portal (EMP) — Academic Project Report")
            self.drawRightString(576, 762, "IIT Madras | MAD-1 / TDS")
            self.setStrokeColor(colors.HexColor("#d0d7de"))
            self.setLineWidth(0.5)
            self.line(36, 756, 576, 756)
        
        # Footer
        self.setStrokeColor(colors.HexColor("#d0d7de"))
        self.setLineWidth(0.5)
        self.line(36, 42, 576, 42)
        self.drawString(36, 30, "Candidate: Tirth Bora (Roll: 24f3002455 | tirthbora8806@gmail.com) | EMP_24f3002455.zip")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(576, 30, page_str)
        self.restoreState()

def build_pdf(output_path):
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=46,
        bottomMargin=48
    )

    styles = getSampleStyleSheet()
    
    # Custom Palette
    PRIMARY = colors.HexColor("#0f2b48")
    SECONDARY = colors.HexColor("#1e568a")
    TEXT_DARK = colors.HexColor("#24292f")
    BG_LIGHT = colors.HexColor("#f6f8fa")
    BORDER_COLOR = colors.HexColor("#d0d7de")

    # Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=PRIMARY,
        spaceAfter=3,
        alignment=1
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=SECONDARY,
        spaceAfter=8,
        alignment=1
    )
    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=PRIMARY,
        spaceBefore=7,
        spaceAfter=3,
        keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=12,
        textColor=SECONDARY,
        spaceBefore=5,
        spaceAfter=2,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.2,
        leading=11,
        textColor=TEXT_DARK,
        spaceAfter=3
    )
    bullet_style = ParagraphStyle(
        'Bullet',
        parent=body_style,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=2
    )
    meta_label = ParagraphStyle(
        'MetaLabel',
        parent=body_style,
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=PRIMARY
    )
    meta_val = ParagraphStyle(
        'MetaVal',
        parent=body_style,
        fontSize=8,
        leading=10
    )
    code_style = ParagraphStyle(
        'Code',
        parent=body_style,
        fontName='Courier',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#0969da")
    )
    table_cell = ParagraphStyle(
        'TableCell',
        parent=body_style,
        fontSize=7.5,
        leading=9.5
    )
    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=table_cell,
        fontName='Helvetica-Bold',
        textColor=PRIMARY
    )

    story = []

    # Title Banner
    story.append(Paragraph("ACADEMIC PROJECT REPORT", title_style))
    story.append(Paragraph("<b>Examination Management Portal (EMP)</b> — Full Stack Web Application", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceAfter=6, spaceBefore=0))

    # Meta Table (Student details & project ID)
    meta_data = [
        [Paragraph("<b>Student Name:</b>", meta_label), Paragraph("Tirth Bora", meta_val),
         Paragraph("<b>Roll Number:</b>", meta_label), Paragraph("<b>24f3002455</b>", meta_val)],
        [Paragraph("<b>Email:</b>", meta_label), Paragraph("tirthbora8806@gmail.com", meta_val),
         Paragraph("<b>Institution:</b>", meta_label), Paragraph("IIT Madras", meta_val)],
        [Paragraph("<b>Program:</b>", meta_label), Paragraph("BS in Data Science & Applications", meta_val),
         Paragraph("<b>Package Name:</b>", meta_label), Paragraph("<code>EMP_24f3002455.zip</code>", code_style)],
        [Paragraph("<b>Repository:</b>", meta_label), Paragraph("github.com/TirthRahulBora/examination-management-portal", code_style),
         Paragraph("<b>Course:</b>", meta_label), Paragraph("Tools in Data Science (MAD-1 / TDS)", meta_val)],
        [Paragraph("<b>Demo Video URL:</b>", meta_label), Paragraph("<i>[Google Drive / YouTube Video Link Placeholder - Enter URL Here]</i>", meta_val),
         Paragraph("<b>Submission Date:</b>", meta_label), Paragraph("November 2026", meta_val)],
    ]
    t_meta = Table(meta_data, colWidths=[90, 180, 85, 185])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 0.8, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.4, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 6))

    # Section 1: Problem Statement & Objectives
    story.append(Paragraph("1. Problem Statement & Operational Context", h1_style))
    story.append(Paragraph(
        "Academic examination administration—encompassing viva-voce tests, laboratory practicals, and capstone demonstrations—"
        "traditionally relies on decentralized spreadsheets, shared documents, and ad-hoc email communications. "
        "This legacy approach causes critical operational vulnerabilities: schedule collisions between faculty members, "
        "student overbooking beyond laboratory capacity, timeline violations, non-standardized evaluation criteria, "
        "and a total absence of auditable historical records.",
        body_style
    ))
    story.append(Paragraph(
        "The <b>Examination Management Portal (EMP)</b> replaces manual workflows with a unified, role-based, synchronized web system "
        "serving three key institutional roles: <b>Administrators</b> (academic configuration, rubric creation, approvals), "
        "<b>Examiners</b> (slot authoring within defined windows, candidate attendance, rubric evaluation), and "
        "<b>Students</b> (catalog exploration, slot reservation, cancellation, official scorecard access).",
        body_style
    ))

    # Section 2: Architecture & Technical Foundations
    story.append(Paragraph("2. Architecture & Technology Stack", h1_style))
    story.append(Paragraph(
        "Strictly conforming to the IIT Madras MAD-1 project specifications, EMP is developed entirely with server-side Python and Flask. "
        "No single-page application (SPA) frontend frameworks (React, Angular, Vue) or external database servers (PostgreSQL, MySQL, MongoDB) are employed.",
        body_style
    ))

    stack_data = [
        [Paragraph("Tier / Layer", table_cell_bold), Paragraph("Technology Spec", table_cell_bold), Paragraph("Architectural Justification", table_cell_bold)],
        [Paragraph("Backend Framework", table_cell), Paragraph("Python 3.13 / Flask 3.0.3", code_style), Paragraph("Lightweight WSGI framework; application factory pattern (`create_app`) isolating configs.", table_cell)],
        [Paragraph("Relational Database", table_cell), Paragraph("SQLite 3 (Local Serverless)", code_style), Paragraph("Zero-configuration ACID-compliant local storage; transactions with partial unique indexing.", table_cell)],
        [Paragraph("ORM & Modeling", table_cell), Paragraph("Flask-SQLAlchemy 3.1.1", code_style), Paragraph("Declarative relational models, cascade semantics, parameterized SQL binding.", table_cell)],
        [Paragraph("Authentication & RBAC", table_cell), Paragraph("Flask-Login 0.6.3 + Werkzeug", code_style), Paragraph("Salted PBKDF2-SHA256 password hashing; session protection; `@role_required` decorators.", table_cell)],
        [Paragraph("Presentation Tier", table_cell), Paragraph("Jinja2 + Bootstrap 5.3.3", code_style), Paragraph("Server-rendered HTML5 templates, responsive grid, dynamic scoring UX, accessibility.", table_cell)],
        [Paragraph("Security Hardening", table_cell), Paragraph("Native HMAC CSRF / Lax Cookies", code_style), Paragraph("Cryptographic CSRF token verification across all POST/PUT/DELETE forms; debug=False by default.", table_cell)],
        [Paragraph("Automated Testing", table_cell), Paragraph("Pytest 9.2.0 (31 Tests)", code_style), Paragraph("Isolated test harness using in-memory SQLite (`StaticPool`); 100% pass rate.", table_cell)]
    ]
    t_stack = Table(stack_data, colWidths=[110, 140, 290])
    t_stack.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 0.6, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_stack)
    story.append(Spacer(1, 6))

    # Section 3: Entity-Relationship Relational Design
    story.append(Paragraph("3. Relational Schema & Entity Specifications", h1_style))
    story.append(Paragraph(
        "The relational database schema is structured into 8 cohesive entities created and managed programmatically via SQLAlchemy ORM:",
        body_style
    ))

    schema_data = [
        [Paragraph("Entity", table_cell_bold), Paragraph("Primary / Foreign Keys", table_cell_bold), Paragraph("Core Attributes", table_cell_bold), Paragraph("Business Constraints & Integrity", table_cell_bold)],
        [Paragraph("User", table_cell_bold), Paragraph("PK: `id`", code_style), Paragraph("`email`, `password_hash`, `role`, `status`, `department`, `contact`", table_cell), Paragraph("Unique email; role in {'admin','examiner','student'}; status gate on examiners.", table_cell)],
        [Paragraph("Course", table_cell_bold), Paragraph("PK: `id`", code_style), Paragraph("`course_code`, `course_name`, `description`, `status`", table_cell), Paragraph("Unique course code; Active/Inactive lifecycle.", table_cell)],
        [Paragraph("Examination", table_cell_bold), Paragraph("PK: `id`<br/>FK: `course_id`", code_style), Paragraph("`examination_name`, `type`, `duration`, `max_marks`, timeline windows", table_cell), Paragraph("Enforces slot creation and booking date boundaries; automated state machine.", table_cell)],
        [Paragraph("ExamExaminers", table_cell_bold), Paragraph("FK: `examination_id`<br/>FK: `user_id`", code_style), Paragraph("Association table for M:N mapping", table_cell), Paragraph("Restricts slot authoring strictly to faculty assigned to the examination.", table_cell)],
        [Paragraph("Rubric", table_cell_bold), Paragraph("PK: `id`<br/>FK: `examination_id`", code_style), Paragraph("`criterion_name`, `maximum_marks`, `weightage`", table_cell), Paragraph("Sum of criterion marks matches examination ceiling; cascade on delete.", table_cell)],
        [Paragraph("Slot", table_cell_bold), Paragraph("PK: `id`<br/>FK: `exam_id`, `examiner_id`", code_style), Paragraph("`examination_date`, `start_time`, `end_time`, `capacity`, `available_seats`", table_cell), Paragraph("No overlapping slots for same examiner; atomic seat decrement.", table_cell)],
        [Paragraph("Booking", table_cell_bold), Paragraph("PK: `id`<br/>FK: `student_id`, `slot_id`", code_style), Paragraph("`booking_date`, `status` ('Booked','Cancelled','Completed')", table_cell), Paragraph("Partial unique index `uq_active_student_exam_booking` prevents duplicate booking.", table_cell)],
        [Paragraph("Evaluation", table_cell_bold), Paragraph("PK: `id`<br/>FK: `booking_id`, `examiner_id`", code_style), Paragraph("`total_marks`, `remarks`, `publication_status`", table_cell), Paragraph("1:1 with Booking; published evaluations locked against non-admin edits.", table_cell)],
        [Paragraph("EvalDetail", table_cell_bold), Paragraph("PK: `id`<br/>FK: `eval_id`, `rubric_id`", code_style), Paragraph("`marks_awarded`, `remarks`", table_cell), Paragraph("Mandatory inclusion of all criteria; rejects negative/NaN/Inf scores.", table_cell)]
    ]
    t_schema = Table(schema_data, colWidths=[65, 95, 180, 200])
    t_schema.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 0.6, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_schema)
    story.append(Spacer(1, 6))

    # Section 4: Blueprint Controllers & API Endpoints
    story.append(Paragraph("4. Controller Architecture & Endpoint Catalog", h1_style))
    story.append(Paragraph(
        "Application routes are organized modularly across four Flask blueprints, each equipped with strict role-based access decorators:",
        body_style
    ))

    routes_data = [
        [Paragraph("Blueprint", table_cell_bold), Paragraph("Endpoint URL Pattern", table_cell_bold), Paragraph("HTTP Methods", table_cell_bold), Paragraph("Role Guard", table_cell_bold), Paragraph("Functional Description", table_cell_bold)],
        [Paragraph("Auth", table_cell), Paragraph("`/auth/login`", code_style), Paragraph("GET, POST", table_cell), Paragraph("Public", table_cell), Paragraph("Credential validation; PBKDF2 hash checking; sets session cookie.", table_cell)],
        [Paragraph("Auth", table_cell), Paragraph("`/auth/register/student`", code_style), Paragraph("GET, POST", table_cell), Paragraph("Public", table_cell), Paragraph("Student self-registration; activates account immediately.", table_cell)],
        [Paragraph("Auth", table_cell), Paragraph("`/auth/register/examiner`", code_style), Paragraph("GET, POST", table_cell), Paragraph("Public", table_cell), Paragraph("Examiner application; placed into pending status awaiting admin approval.", table_cell)],
        [Paragraph("Admin", table_cell), Paragraph("`/admin/dashboard`", code_style), Paragraph("GET", table_cell), Paragraph("Admin", table_cell), Paragraph("System statistics, pending examiner review queue, active booking counts.", table_cell)],
        [Paragraph("Admin", table_cell), Paragraph("`/admin/courses`", code_style), Paragraph("GET, POST", table_cell), Paragraph("Admin", table_cell), Paragraph("Course catalog management (Create, Read, Update, Deactivate).", table_cell)],
        [Paragraph("Admin", table_cell), Paragraph("`/admin/examinations`", code_style), Paragraph("GET, POST", table_cell), Paragraph("Admin", table_cell), Paragraph("Examination definition, timeline window configuration, state updates.", table_cell)],
        [Paragraph("Admin", table_cell), Paragraph("`/admin/examiners`", code_style), Paragraph("GET, POST", table_cell), Paragraph("Admin", table_cell), Paragraph("Faculty vetting: one-click approval, rejection, and account deactivation.", table_cell)],
        [Paragraph("Admin", table_cell), Paragraph("`/admin/bookings/<id>/reschedule`", code_style), Paragraph("GET, POST", table_cell), Paragraph("Admin", table_cell), Paragraph("Transactional student transfer across slots within the same examination.", table_cell)],
        [Paragraph("Admin", table_cell), Paragraph("`/admin/slots/<id>/reassign`", code_style), Paragraph("POST", table_cell), Paragraph("Admin", table_cell), Paragraph("Reassigns slot examiner with schedule conflict and assignment validation.", table_cell)],
        [Paragraph("Examiner", table_cell), Paragraph("`/examiner/examinations/<id>/slots/new`", code_style), Paragraph("GET, POST", table_cell), Paragraph("Examiner", table_cell), Paragraph("Authors examination slot within the approved slot creation timeline window.", table_cell)],
        [Paragraph("Examiner", table_cell), Paragraph("`/examiner/slots/<id>/edit`", code_style), Paragraph("GET, POST", table_cell), Paragraph("Examiner", table_cell), Paragraph("Modifies owned slot before booking commences; checks schedule overlap.", table_cell)],
        [Paragraph("Examiner", table_cell), Paragraph("`/examiner/bookings/<id>/evaluate`", code_style), Paragraph("GET, POST", table_cell), Paragraph("Examiner", table_cell), Paragraph("Multi-criteria rubric grading; validates score ceilings; saves draft/published.", table_cell)],
        [Paragraph("Student", table_cell), Paragraph("`/student/examinations`", code_style), Paragraph("GET", table_cell), Paragraph("Student", table_cell), Paragraph("Catalog browsing with course and examination type filtering.", table_cell)],
        [Paragraph("Student", table_cell), Paragraph("`/student/slots/<id>/book`", code_style), Paragraph("POST", table_cell), Paragraph("Student", table_cell), Paragraph("Reserves slot seat with atomic capacity decrement and duplicate guard.", table_cell)],
        [Paragraph("Student", table_cell), Paragraph("`/student/bookings/<id>/cancel`", code_style), Paragraph("POST", table_cell), Paragraph("Student", table_cell), Paragraph("Cancels booking before deadline; restores available seat to pool.", table_cell)],
        [Paragraph("Student", table_cell), Paragraph("`/student/results/<id>`", code_style), Paragraph("GET", table_cell), Paragraph("Student", table_cell), Paragraph("Accesses verified official scorecard; IDOR protected (HTTP 403 on mismatch).", table_cell)]
    ]
    t_routes = Table(routes_data, colWidths=[55, 145, 60, 55, 225])
    t_routes.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 0.6, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 1.8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.8),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(t_routes)
    story.append(Spacer(1, 6))

    # Section 5: Critical Business Logic & Concurrency Hardening
    story.append(Paragraph("5. Critical Business Logic & Security Hardening", h1_style))
    story.append(Paragraph(
        "The application integrates multi-layered validation safeguards at both the service layer and database engine level:",
        body_style
    ))
    
    rules = [
        "<b>1. Concurrency Safety & Atomic Capacity Decrement:</b> SQLite executes with database-level write transactions. To eliminate race conditions and overselling without relying on nonexistent row-level locks, `BookingService.book_slot` executes an atomic conditional SQL statement: <code>UPDATE examination_slots SET available_seats = available_seats - 1 WHERE id = :id AND available_seats > 0</code>. If multiple requests compete for the final seat, only one finds <code>available_seats > 0</code>; losing requests receive an immediate capacity rejection.",
        "<b>2. Database-Level Duplicate Booking Prevention:</b> In addition to service queries, duplicate active registrations for the same examination are physically prevented by an SQLite partial unique index: <code>CREATE UNIQUE INDEX uq_active_student_exam_booking ON bookings (student_id, examination_id) WHERE status = 'Booked'</code>.",
        "<b>3. Strict Timeline Synchronization:</b> Slot authoring and modification are restricted to <code>slot_creation_start <= now <= slot_creation_end</code> and prior to <code>slot_booking_start</code>. Candidate booking is permitted strictly while <code>slot_booking_start <= now <= slot_booking_end</code>. Booking cancellation is strictly rejected once the deadline arrives (<code>now >= slot_booking_end</code>).",
        "<b>4. Faculty Overlap & Reassignment Checks:</b> Both initial slot authoring and administrative examiner reassignment execute temporal overlap algorithms to ensure no faculty member has conflicting sessions on the same date.",
        "<b>5. Mandatory Complete Rubric Scoring:</b> Evaluations reject incomplete submissions where any configured criterion is omitted. Furthermore, submitted marks strictly reject <code>NaN</code>, <code>Infinity</code>, and negative values.",
        "<b>6. Cross-Site Request Forgery (CSRF) Protection:</b> All state-changing methods (POST, PUT, DELETE) require a cryptographically random session token (<code>secrets.token_hex(32)</code>) validated via constant-time comparison (<code>hmac.compare_digest</code>).",
        "<b>7. Insecure Direct Object Reference (IDOR) Immunity:</b> Endpoints taking object IDs (such as <code>/student/results/&lt;id&gt;</code> and <code>/student/bookings/&lt;id&gt;/cancel</code>) enforce ownership checks against <code>current_user.id</code>, returning HTTP 403 Forbidden upon unauthorized access.",
        "<b>8. Secure Configuration & Production Hardening:</b> <code>DEBUG</code> is disabled by default. Production mode strictly mandates an externally supplied <code>SECRET_KEY</code> and environment-configured administrator credentials (<code>EMP_ADMIN_EMAIL</code>, <code>EMP_ADMIN_PASSWORD</code>)."
    ]
    for r in rules:
        story.append(Paragraph(f"• {r}", bullet_style))
    story.append(Spacer(1, 6))

    # Section 6: Automated Testing & Pytest Verification
    story.append(Paragraph("6. Quality Assurance & Pytest Verification (31 Tests)", h1_style))
    story.append(Paragraph(
        "A comprehensive automated regression test suite containing <b>31 unit and integration test cases</b> was implemented across 5 test modules. "
        "All tests execute against an isolated in-memory SQLite database utilizing SQLAlchemy's <code>StaticPool</code>:",
        body_style
    ))

    test_data = [
        [Paragraph("Module", table_cell_bold), Paragraph("Tests", table_cell_bold), Paragraph("Key Invariants Verified", table_cell_bold), Paragraph("Result", table_cell_bold)],
        [Paragraph("`test_auth.py`", code_style), Paragraph("6 Tests", table_cell), Paragraph("Admin login, student instant active registration, examiner approval gate, RBAC HTTP 403 URL guards, CSRF token validation, production SECRET_KEY requirement.", table_cell), Paragraph("<font color='#1a7f37'><b>100% PASS</b></font>", table_cell)],
        [Paragraph("`test_admin.py`", code_style), Paragraph("5 Tests", table_cell), Paragraph("Course CRUD, exam lifecycle, rubric criteria weight ceilings, examiner deactivation, slot reassignment conflict prevention.", table_cell), Paragraph("<font color='#1a7f37'><b>100% PASS</b></font>", table_cell)],
        [Paragraph("`test_examiner.py`", code_style), Paragraph("8 Tests", table_cell), Paragraph("Slot creation, schedule conflict rejection, roster inspection, rubric grading, unauthorized evaluation guard, slot editing window enforcement, missing criteria rejection, NaN/Inf score rejection.", table_cell), Paragraph("<font color='#1a7f37'><b>100% PASS</b></font>", table_cell)],
        [Paragraph("`test_student.py`", code_style), Paragraph("5 Tests", table_cell), Paragraph("Catalog search & filtering, slot booking, booking cancellation seat restoration, published scorecard visibility, scorecard IDOR 403 protection, cancellation IDOR 403 protection.", table_cell), Paragraph("<font color='#1a7f37'><b>100% PASS</b></font>", table_cell)],
        [Paragraph("`test_booking.py`", code_style), Paragraph("7 Tests", table_cell), Paragraph("Overbooking prevention, duplicate booking rejection, booking deadline enforcement, slot creation window enforcement, admin rescheduling, cancellation deadline boundary, atomic capacity exhaustion.", table_cell), Paragraph("<font color='#1a7f37'><b>100% PASS</b></font>", table_cell)],
        [Paragraph("<b>TOTAL</b>", table_cell_bold), Paragraph("<b>31 Tests</b>", table_cell_bold), Paragraph("<b>Comprehensive end-to-end coverage of all business logic, security, and boundary rules.</b>", table_cell_bold), Paragraph("<font color='#1a7f37'><b>31 / 31 (100%)</b></font>", table_cell_bold)]
    ]
    t_tests = Table(test_data, colWidths=[80, 50, 340, 70])
    t_tests.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BG_LIGHT),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#eef5fc")),
        ('BOX', (0, 0), (-1, -1), 0.6, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_tests)
    story.append(Spacer(1, 6))

    # Section 7: Declaration of Ownership & AI Usage
    story.append(Paragraph("7. Academic Integrity & AI Usage Declaration", h1_style))
    story.append(Paragraph(
        "<b>1. Declaration of Originality:</b> I, Tirth Bora, hereby certify that this project—the Examination Management Portal (EMP)—"
        "is my original work prepared for the academic assessment requirements of IIT Madras. All database schemas, business rules, "
        "and architectural patterns have been implemented to adhere to course standards.",
        body_style
    ))
    story.append(Paragraph(
        "<b>2. Declaration of AI Tool Usage:</b> In compliance with IIT Madras guidelines regarding artificial intelligence assistance, "
        "I declare that <b>Google Antigravity</b> (powered by Gemini) was utilized during development. "
        "The tool assisted with architectural scaffolding, Jinja2/Bootstrap HTML boilerplate generation, "
        "and drafting automated pytest test cases. All architectural decisions, SQLite concurrency implementations, "
        "business logic validations, security hardening, and code verification were actively directed, evaluated, and verified by me.",
        body_style
    ))
    story.append(Paragraph(
        "<b>3. Project Demonstration Video Link:</b> The video walkthrough demonstrating all three role dashboards, "
        "slot creation, student booking, rubric evaluation, overbooking rejection, and live automated test execution is accessible at: "
        "<code>[Google Drive / YouTube Video Link Placeholder - Enter URL Here]</code>.",
        body_style
    ))

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[PDF GENERATION] Document generated at: {output_path}")

if __name__ == '__main__':
    project_root = Path(__file__).resolve().parent.parent
    pdf_out = project_root / 'EMP_Final_Submission_Report.pdf'
    build_pdf(pdf_out)
