from datetime import datetime
from app.extensions import db
from app.models import ExaminationSlot, Booking, Examination, User

class BookingService:
    @staticmethod
    def create_slot(examiner, exam_id, exam_date, start_time, end_time, maximum_capacity=1):
        """Examiner creates a slot during the slot creation window."""
        if examiner.role != 'examiner' or examiner.status != 'approved':
            raise PermissionError("Only approved examiners can create examination slots.")

        exam = Examination.query.get_or_404(exam_id)

        # 1. Examiner must be assigned to this examination
        if examiner not in exam.assigned_examiners:
            raise PermissionError("Examiner is not assigned to this examination.")

        # 2. Examination timeline check
        now = datetime.utcnow()
        if not exam.is_in_slot_creation_period(now):
            raise ValueError(f"Slot creation window closed or not open yet. Window: {exam.slot_creation_start.strftime('%Y-%m-%d %H:%M')} to {exam.slot_creation_end.strftime('%Y-%m-%d %H:%M')}.")

        # 3. Time validation
        if end_time <= start_time:
            raise ValueError("Slot end time must be after start time.")

        if maximum_capacity < 1:
            raise ValueError("Maximum capacity must be at least 1.")

        # 4. Overlap check for examiner
        overlapping = ExaminationSlot.query.filter(
            ExaminationSlot.examiner_id == examiner.id,
            ExaminationSlot.examination_date == exam_date,
            ExaminationSlot.status != 'Cancelled',
            ExaminationSlot.start_time < end_time,
            ExaminationSlot.end_time > start_time
        ).first()

        if overlapping:
            raise ValueError(f"Schedule conflict: Examiner already has an active slot on {exam_date} between {overlapping.start_time} and {overlapping.end_time}.")

        slot = ExaminationSlot(
            examination_id=exam.id,
            examiner_id=examiner.id,
            examination_date=exam_date,
            start_time=start_time,
            end_time=end_time,
            maximum_capacity=int(maximum_capacity),
            available_seats=int(maximum_capacity),
            status='Available'
        )
        db.session.add(slot)
        db.session.commit()
        return slot

    @staticmethod
    def update_slot(slot_id, examiner, exam_date, start_time, end_time, maximum_capacity):
        """Update an owned slot before booking opens, without disturbing reservations."""
        slot = ExaminationSlot.query.get_or_404(slot_id)
        if examiner is not None and slot.examiner_id != examiner.id:
            raise PermissionError("You do not have permission to modify this slot.")

        exam = slot.examination
        now = datetime.utcnow()
        if not exam.is_in_slot_creation_period(now):
            raise ValueError(f"Slot creation window is not currently active. Window: {exam.slot_creation_start.strftime('%Y-%m-%d %H:%M')} to {exam.slot_creation_end.strftime('%Y-%m-%d %H:%M')}.")
        if now >= exam.slot_booking_start:
            raise ValueError("Slots cannot be modified once the booking window has opened.")

        if slot.booked_count > 0:
            raise ValueError("Cannot edit a slot that already has student bookings.")

        if end_time <= start_time:
            raise ValueError("End time must be strictly after start time.")

        if int(maximum_capacity) < 1:
            raise ValueError("Maximum capacity must be at least 1.")

        # Check for schedule conflicts with other active slots of the same examiner on the same date
        existing_slots = ExaminationSlot.query.filter(
            ExaminationSlot.examiner_id == slot.examiner_id,
            ExaminationSlot.examination_date == exam_date,
            ExaminationSlot.id != slot.id,
            ExaminationSlot.status != 'Cancelled'
        ).all()
        for s in existing_slots:
            if not (end_time <= s.start_time or start_time >= s.end_time):
                raise ValueError(f"Slot overlaps with existing slot {s.start_time.strftime('%H:%M')}-{s.end_time.strftime('%H:%M')}.")

        slot.examination_date = exam_date
        slot.start_time = start_time
        slot.end_time = end_time
        slot.maximum_capacity = int(maximum_capacity)
        slot.available_seats = int(maximum_capacity)
        db.session.commit()
        return slot

    @staticmethod
    def delete_slot(slot_id, examiner=None, is_admin=False):
        """Delete a slot before bookings start or if empty."""
        slot = ExaminationSlot.query.get_or_404(slot_id)
        if not is_admin:
            if examiner is None or slot.examiner_id != examiner.id:
                raise PermissionError("Cannot delete slots owned by another examiner.")
            # Check if booking period has already started
            now = datetime.utcnow()
            if now >= slot.examination.slot_booking_start:
                raise ValueError("Cannot delete slot once the booking window has commenced.")
        
        if slot.booked_count > 0:
            raise ValueError("Cannot delete slot with active student bookings. Reschedule or cancel bookings first.")

        db.session.delete(slot)
        db.session.commit()
        return True

    @staticmethod
    def book_slot(student_id, slot_id):
        """Student books a slot with full concurrency protection and duplicate checks."""
        # Use with_for_update on slot to serialize concurrent booking operations
        slot = db.session.query(ExaminationSlot).filter_by(id=slot_id).with_for_update().first()
        if not slot:
            raise ValueError("Requested examination slot does not exist.")

        exam = slot.examination
        now = datetime.utcnow()

        # 1. Timeline check
        if not exam.is_in_booking_period(now):
            raise ValueError("Examination booking window is currently closed.")

        if exam.status not in ['Booking Open', 'Slot Creation']:
            raise ValueError(f"Examination is not accepting bookings (Status: {exam.status}).")

        # 2. Check slot status and seat capacity
        if slot.status != 'Available' or slot.available_seats <= 0:
            raise ValueError("This examination slot is full or unavailable.")

        # 3. Check duplicate active bookings for the same exam by this student
        existing_booking = Booking.query.filter_by(
            student_id=student_id,
            examination_id=exam.id,
            status='Booked'
        ).first()

        if existing_booking:
            raise ValueError(f"Duplicate booking prohibited: You already have an active booking for {exam.examination_name}.")

        # 4. Reserve seat and update slot status atomically
        slot.available_seats -= 1
        if slot.available_seats <= 0:
            slot.status = 'Full'

        booking = Booking(
            student_id=student_id,
            slot_id=slot.id,
            examination_id=exam.id,
            status='Booked'
        )
        db.session.add(booking)
        db.session.commit()
        return booking

    @staticmethod
    def cancel_booking(booking_id, user=None, is_admin=False):
        """Cancel a booking, restore capacity, and retain audit history."""
        booking = db.session.query(Booking).filter_by(id=booking_id).with_for_update().first()
        if not booking:
            raise ValueError("Booking record not found.")

        if booking.status != 'Booked':
            raise ValueError(f"Cannot cancel a booking with status '{booking.status}'.")

        # Permission verification
        if not is_admin:
            if user is None or booking.student_id != user.id:
                raise PermissionError("Unauthorized cancellation attempt.")
            # Student can cancel only before the booking deadline
            now = datetime.utcnow()
            if now >= booking.examination.slot_booking_end:
                raise ValueError("Cancellation deadline has passed for this examination.")

        slot = db.session.query(ExaminationSlot).filter_by(id=booking.slot_id).with_for_update().first()
        booking.status = 'Cancelled'

        if slot:
            slot.available_seats += 1
            if slot.status == 'Full' and slot.available_seats > 0:
                slot.status = 'Available'

        db.session.commit()
        return booking

    @staticmethod
    def reschedule_booking(booking_id, target_slot_id, admin_user):
        """Admin moves a student booking to a different slot within the same examination."""
        if not admin_user.is_admin:
            raise PermissionError("Only administrators can reschedule bookings.")

        booking = db.session.query(Booking).filter_by(id=booking_id).with_for_update().first()
        if not booking:
            raise ValueError("Booking not found.")

        if booking.status != 'Booked':
            raise ValueError("Only active ('Booked') bookings can be rescheduled.")

        target_slot = db.session.query(ExaminationSlot).filter_by(id=target_slot_id).with_for_update().first()
        if not target_slot:
            raise ValueError("Target slot does not exist.")

        if target_slot.examination_id != booking.examination_id:
            raise ValueError("Target slot must belong to the same examination.")

        if target_slot.id == booking.slot_id:
            raise ValueError("Booking is already assigned to this slot.")

        if target_slot.status != 'Available' or target_slot.available_seats <= 0:
            raise ValueError("Target slot does not have sufficient capacity.")

        source_slot = db.session.query(ExaminationSlot).filter_by(id=booking.slot_id).with_for_update().first()

        # Restore seat on source slot
        if source_slot:
            source_slot.available_seats += 1
            if source_slot.status == 'Full' and source_slot.available_seats > 0:
                source_slot.status = 'Available'

        # Deduct seat on target slot
        target_slot.available_seats -= 1
        if target_slot.available_seats <= 0:
            target_slot.status = 'Full'

        booking.slot_id = target_slot.id
        db.session.commit()
        return booking

    @staticmethod
    def reassign_examiner(slot_id, new_examiner_id, admin_user):
        """Admin reassigns the examiner of a slot."""
        if not admin_user.is_admin:
            raise PermissionError("Only administrators can reassign examiners.")

        slot = ExaminationSlot.query.get_or_404(slot_id)
        new_examiner = User.query.filter_by(id=new_examiner_id, role='examiner', status='approved').first()
        if not new_examiner:
            raise ValueError("Selected examiner is not an approved active examiner.")

        # Check for schedule conflicts for the new examiner
        conflict = ExaminationSlot.query.filter(
            ExaminationSlot.examiner_id == new_examiner.id,
            ExaminationSlot.examination_date == slot.examination_date,
            ExaminationSlot.id != slot.id,
            ExaminationSlot.status != 'Cancelled',
            ExaminationSlot.start_time < slot.end_time,
            ExaminationSlot.end_time > slot.start_time
        ).first()
        if conflict:
            raise ValueError(f"Schedule conflict: Examiner {new_examiner.full_name} already has an active slot on {slot.examination_date} from {conflict.start_time.strftime('%H:%M')} to {conflict.end_time.strftime('%H:%M')}.")

        # Ensure examiner is associated with examination
        if new_examiner not in slot.examination.assigned_examiners:
            slot.examination.assigned_examiners.append(new_examiner)

        slot.examiner_id = new_examiner.id
        db.session.commit()
        return slot
