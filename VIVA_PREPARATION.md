# VIVA VOCE PREPARATION GUIDE
## Examination Management Portal (EMP)

This guide prepares you to confidently present, explain, and defend the Examination Management Portal (EMP) in front of an academic examination committee or viva examiner.

---

## 1. Core Architecture Deep-Dive

### The Flask Application Factory Pattern
- **Where is it defined?** [`app/__init__.py`](app/__init__.py) in `create_app(config_name)`.
- **Why did we use it?** Rather than creating a single global `app` object at the module level, the factory pattern creates an application instance dynamically based on the passed configuration (`development`, `testing`, `production`). This allows our automated test suite in [`tests/conftest.py`](tests/conftest.py) to spin up independent, isolated testing applications with in-memory SQLite databases without affecting local files or production data.

### Blueprint Architecture
Instead of registering all routes on a monolithic application, EMP modularizes controllers into four dedicated blueprints:
1. `auth_bp` (`/auth`): Authentication, student registration, faculty application, logout.
2. `admin_bp` (`/admin`): System dashboard, course CRUD, exam configuration, rubric builder, examiner verification, student directory, rescheduling.
3. `examiner_bp` (`/examiner`): Assigned examinations, slot creation, candidate rosters, rubric grading.
4. `student_bp` (`/student`): Examination catalog, slot reservation, cancellation, scorecard viewing, profile updating.

### Service Layer Decoupling
Business logic is not mixed directly into view route functions:
- `ExaminationService` ([`app/services/examination_service.py`](app/services/examination_service.py)): Validates timeline windows, rubric mark ceilings, and automated status transitions.
- `BookingService` ([`app/services/booking_service.py`](app/services/booking_service.py)): Manages atomic seat decrements, duplicate active booking guards, slot cancellation capacity restorations, and administrative rescheduling.
- `EvaluationService` ([`app/services/evaluation_service.py`](app/services/evaluation_service.py)): Enforces that only assigned examiners can grade their own candidates, validates non-negative rubric scores within criteria bounds, and guards published results against unauthorized edits.

---

## 2. Key Technical Concepts to Explain

### 1. Flask Request Lifecycle
1. **HTTP Request Arrival:** WSGI server (Werkzeug development server) receives an HTTP request and packages WSGI environment variables.
2. **Context Creation:** Flask pushes both an **Application Context** (`current_app`, `g`) and a **Request Context** (`request`, `session`).
3. **URL Routing & Matching:** Flask matches the requested URL against the URL map registered by blueprints.
4. **Before Request Hooks:** Decorators such as `@admin_bp.before_request`, `@login_required`, and our custom `@admin_required` execute to verify permissions.
5. **View Function Execution:** The controller delegates to a Service class, executes database operations, and calls `render_template`.
6. **Context Teardown:** Flask invokes teardown hooks (committing or rolling back database sessions), pops the contexts, and serializes the HTTP response back to the client.

### 2. Password Security & Werkzeug Hashing
- We never store plaintext passwords. In [`app/models/user.py`](app/models/user.py), `set_password` calls `werkzeug.security.generate_password_hash(password)`.
- It utilizes **PBKDF2 with SHA-256** and a cryptographic salt.
- Authentication checks execute in constant time via `check_password_hash(self.password_hash, password)` to thwart timing attacks.

### 3. Faculty Approval Gate
- Self-registered examiners receive `status = 'pending'`.
- In [`app/models/user.py`](app/models/user.py), Flask-Login's `is_active` property is overridden:
  ```python
  @property
  def is_active(self):
      if self.role == 'examiner':
          return self.status == 'approved'
      ...
  ```
  If an unapproved or deactivated examiner attempts to authenticate, Flask-Login automatically blocks the session from activating.

### 4. Concurrency & Overbooking Elimination
- When a candidate books a slot, `BookingService.book_slot` executes inside an atomic database transaction.
- The service inspects `slot.available_seats > 0` and decrements `slot.available_seats -= 1`. If `available_seats == 0`, `slot.status` updates to `'Full'`.
- If two candidates simultaneously attempt to claim the final seat, the first transaction commits and the second fails the `available_seats > 0` guard, raising `ValueError("This examination slot is full or unavailable.")`.

### 5. Duplicate Booking Prevention
- **Application Level:** `Booking.query.filter_by(student_id=student_id, examination_id=exam.id, status='Booked').first()` rejects second reservations for the same exam.
- **Database Level:** In [`app/models/booking.py`](app/models/booking.py), we defined an SQLite partial unique index:
  ```python
  __table_args__ = (
      db.Index(
          'uq_active_student_exam_booking',
          'student_id',
          'examination_id',
          unique=True,
          sqlite_where=(status == 'Booked')
      ),
  )
  ```
  This guarantees database-level uniqueness for active bookings while permitting historical records of past cancelled bookings.

---

## 3. Thirty Likely Viva Questions & Model Answers

### General Architecture
1. **Q: Why did you choose SQLite over MySQL or PostgreSQL?**  
   *A:* SQLite is a serverless, self-contained, ACID-compliant relational database engine ideal for local testing, zero-configuration institutional grading, and single-host execution without external server overhead.
2. **Q: What is the benefit of the Blueprint pattern?**  
   *A:* Blueprints allow logical separation of concerns. Instead of placing all routes in a single file, routes are segmented by user domain (`auth`, `admin`, `examiner`, `student`), each with their own URL prefixes, before-request hooks, and template subdirectories.
3. **Q: How does template inheritance work in your application?**  
   *A:* `base.html` defines the common skeleton: HTML head, Bootstrap 5 links, navigation bar, responsive sidebar, flash alert container, and footer. Child templates extend `base.html` and override specific blocks (`{% block content %}`) to inject page-specific markup.
4. **Q: How are database transactions handled in Flask-SQLAlchemy?**  
   *A:* Flask-SQLAlchemy binds a scoped session to the request lifecycle. Multiple modifications are staged with `db.session.add()`. Calling `db.session.commit()` commits the atomic unit of work, while `db.session.rollback()` reverts any uncommitted state during exceptions.

### Authentication & Authorization
5. **Q: How did you implement Role-Based Access Control (RBAC)?**  
   *A:* Through custom Python decorators in `app/routes/decorators.py` (`@admin_required`, `@examiner_required`, `@student_required`). They inspect `current_user.role` and status before the wrapped route executes, issuing an HTTP 403 Forbidden abort if privileges are insufficient.
6. **Q: Can a student manipulate the browser URL to access admin panels?**  
   *A:* No. Access control is enforced strictly on the server side. Even if a student manually types `/admin/courses/new`, the `@admin_required` decorator intercepts the request, blocks execution, and returns HTTP 403.
7. **Q: What prevents a faculty examiner from evaluating students before being approved?**  
   *A:* When an examiner registers, their account status is set to `'pending'`. The overridden `is_active` property in `User` returns `False` for pending examiners, which halts Flask-Login authentication and redirects them to `auth.pending_approval`.
8. **Q: How are user sessions persisted?**  
   *A:* Flask uses secure cryptographically signed HTTP cookies. The session data is signed with the server's `SECRET_KEY`, preventing client-side tampering.

### Examination & Slot Management
9. **Q: How do you enforce that examiners only author slots during the allowed period?**  
   *A:* In `ExaminationService` and `BookingService.create_slot`, the system compares `datetime.utcnow()` against `examination.slot_creation_start` and `examination.slot_creation_end`. If the current timestamp is outside this window, slot creation is rejected.
10. **Q: What stops an examiner from creating overlapping slots?**  
    *A:* In `BookingService.create_slot`, a database filter queries for existing active slots under the same examiner on the same date where `existing.start_time < new_end_time` and `existing.end_time > new_start_time`. Overlaps trigger a schedule conflict exception.
11. **Q: Can an examiner delete a slot that already has student bookings?**  
    *A:* No. `BookingService.delete_slot` checks `slot.booked_count > 0`. If bookings exist, deletion is prohibited to preserve candidate commitments.

### Booking & Capacity Logic
12. **Q: Explain how overbooking is prevented.**  
    *A:* Each `ExaminationSlot` maintains an explicit `available_seats` counter. When a reservation request arrives, `BookingService.book_slot` verifies `slot.available_seats > 0` before decrementing it. If the count reaches 0, the slot status changes to `'Full'`.
13. **Q: What happens when a student cancels a booking?**  
    *A:* The student's booking status is updated to `'Cancelled'`. The associated slot's `available_seats` is incremented by 1, and if the slot was previously `'Full'`, its status reverts to `'Available'`.
14. **Q: Why not delete the booking row when cancelled?**  
    *A:* Institutional compliance requires auditing. Keeping the record with status `'Cancelled'` preserves the audit trail of who booked, when, and when they cancelled.
15. **Q: How is duplicate booking prevented if a student tries to book twice in different tabs?**  
    *A:* In addition to the service-layer query check, our SQLite database schema contains a partial unique index on `(student_id, examination_id) WHERE status = 'Booked'`. A concurrent duplicate insert will fail at the database engine level with an `IntegrityError`.
16. **Q: How does administrative rescheduling work?**  
    *A:* `BookingService.reschedule_booking` takes the student's booking ID and a destination slot ID within the same exam. It atomically restores capacity on the origin slot, decrements capacity on the destination slot, and updates `booking.slot_id`.

### Rubrics & Evaluations
17. **Q: What is a rubric in your system?**  
    *A:* A structured evaluation criterion associated with an examination (e.g. *Code Demonstration*, *Oral Defense*), defined with a name, description, weightage, and maximum marks ceiling.
18. **Q: How do you validate that rubric marks don't exceed the exam limit?**  
    *A:* When administrators add rubrics, `ExaminationService.add_rubric` queries the SQL sum of existing criteria marks and ensures `current_sum + new_marks <= exam.maximum_marks`.
19. **Q: Can an examiner give negative marks or exceed a criterion's maximum?**  
    *A:* No. `EvaluationService.submit_evaluation` iterates through submitted scores, validating that each score satisfies `0 <= score <= rubric.maximum_marks`.
20. **Q: What stops an examiner from evaluating another examiner's students?**  
    *A:* In `EvaluationService`, the code verifies `booking.slot.examiner_id == examiner.id` (unless the user is an administrator). Unauthorized evaluators receive an immediate `PermissionError`.
21. **Q: When can a student see their evaluation marks?**  
    *A:* Only when `publication_status == 'Published'`. While in `'Draft'`, the student's results dashboard and scorecard view display results as pending.
22. **Q: Can an examiner modify marks after publishing?**  
    *A:* Once an evaluation is published, examiners cannot alter the marks. Only an administrator can unpublish or override finalized grades.

### Database & Testing
23. **Q: What is the purpose of the `examination_examiners` table?**  
    *A:* It is an association table establishing a Many-to-Many relationship between `examinations` and `users` (examiners), ensuring that only assigned faculty members can conduct slots for a given examination.
24. **Q: How did you configure tests to run in-memory without affecting the live database?**  
    *A:* In `config.py`, `TestingConfig` sets `SQLALCHEMY_DATABASE_URI = 'sqlite://'` and configures SQLAlchemy's `StaticPool`. This maintains a single shared in-memory database per test run that is completely destroyed after test execution.
25. **Q: Why was `StaticPool` necessary for testing?**  
    *A:* In standard SQLite in-memory mode, each new database connection creates a fresh, empty in-memory database. `StaticPool` forces all connections in the test client to share the exact same in-memory database instance.
26. **Q: How many tests did you implement and what do they verify?**  
    *A:* 20 automated pytest tests covering all role operations: authentication, student/examiner registration, admin approval, course/exam CRUD, slot creation conflicts, overbooking prevention, duplicate booking rejection, deadline enforcement, cancellation capacity restoration, and rubric grading.

### Security & Compliance
27. **Q: How does the system prevent SQL injection?**  
    *A:* All database queries use SQLAlchemy ORM parameter binding and query methods (`filter`, `filter_by`, `get`). Parameter values are escaped automatically by the database driver, preventing raw SQL injection.
28. **Q: How does the system prevent Cross-Site Scripting (XSS)?**  
    *A:* Jinja2 auto-escapes all dynamic variables by default (e.g. converting `<` to `&lt;` and `&` to `&amp;`), preventing malicious script injection from user inputs.
29. **Q: What is Session Fixation and how does Flask-Login prevent it?**  
    *A:* Session fixation occurs when an attacker sets a victim's session ID before login. Flask-Login regenerates the session ID upon `login_user()`, invalidating pre-authentication sessions.
30. **Q: What Git branching and commit practices did you follow?**  
    *A:* We maintained a clean `main` branch with structured, logical commits following conventional commit standards (`feat:`, `chore:`, `test:`), regular pushes to GitHub, and a live synchronized `DEVELOPMENT_LOG.md`.

---

## 4. Live Coding Modifications (Examiner Challenges)

During the viva, the examiner might ask you to make a live modification to test your understanding. Here are 5 likely requests and their solutions:

### Challenge 1: "Add a minimum password length of 8 characters instead of 6"
- **File:** [`app/routes/auth.py`](app/routes/auth.py)
- **Edit:** Change `len(password) < 6` to `len(password) < 8` in `register_student` and `register_examiner`.
- **Template:** In `register_student.html`, update `minlength="8"`.

### Challenge 2: "Require examiner remarks to be mandatory when submitting marks"
- **File:** [`app/services/evaluation_service.py`](app/services/evaluation_service.py)
- **Edit:** In `submit_evaluation`:
  ```python
  if not remarks or not remarks.strip():
      raise ValueError("Examiner qualitative remarks are mandatory when submitting evaluations.")
  ```

### Challenge 3: "Allow students to book only up to 2 active examinations at a time"
- **File:** [`app/services/booking_service.py`](app/services/booking_service.py)
- **Edit:** In `book_slot`:
  ```python
  active_total = Booking.query.filter_by(student_id=student_id, status='Booked').count()
  if active_total >= 2:
      raise ValueError("Maximum limit of 2 concurrent active examination bookings reached.")
  ```

### Challenge 4: "Add an extra status 'Archived' for Courses"
- **File:** [`app/models/course.py`](app/models/course.py)
- **Edit:** Update docstring/comment to include `'Archived'`. In `app/routes/admin.py`, add route `/admin/courses/<id>/archive` that sets `course.status = 'Archived'`.

### Challenge 5: "Display percentage score alongside total marks on the student scorecard"
- **File:** [`app/templates/student/result_card.html`](app/templates/student/result_card.html)
- **Edit:** Under the final marks total row:
  ```jinja2
  <div>Percentage: <strong>{{ ((evaluation.total_marks / evaluation.booking.examination.maximum_marks) * 100) | round(2) }}%</strong></div>
  ```

---

## 5. Video Presentation Checklist & Script (5–10 Minutes)

### Suggested Video Timeline
| Timestamp | Segment | Key Talking Points |
|---|---|---|
| **0:00 – 0:30** | Introduction & Problem | Introduce self (Tirth Bora), IIT Madras project, shortcomings of spreadsheets and emails. |
| **0:30 – 1:30** | Technology & Architecture | Flask factory pattern, SQLite, SQLAlchemy, Bootstrap 5, Jinja2, Service layer design. |
| **1:30 – 3:30** | Admin Workflow | Show Admin Dashboard stats, Course creation, Examination configuration, Rubrics builder, Examiner approvals, Rescheduling. |
| **3:30 – 5:00** | Examiner Workflow | Log in as approved examiner, author slot within window, view booked candidates, grade candidate with rubric, publish marks. |
| **5:00 – 7:00** | Student Workflow | Log in as student, browse catalog, book open slot, show seat decrement, inspect schedule, cancel booking (show seat restoration), view verified scorecard. |
| **7:00 – 8:30** | Critical Business Logic & Tests | Demonstrate overbooking rejection, duplicate booking prevention, and run `pytest tests -v` live. |
| **8:30 – 9:00** | Conclusion & GitHub Repo | Show GitHub repository commit history, private visibility, code cleanliness, and conclude. |
