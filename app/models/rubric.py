from app.extensions import db

class ExaminationRubric(db.Model):
    __tablename__ = 'examination_rubrics'

    id = db.Column(db.Integer, primary_key=True)
    examination_id = db.Column(db.Integer, db.ForeignKey('examinations.id', ondelete='CASCADE'), nullable=False, index=True)
    criterion_name = db.Column(db.String(150), nullable=False)
    maximum_marks = db.Column(db.Float, nullable=False)
    weightage = db.Column(db.Float, nullable=False, default=1.0)
    description = db.Column(db.Text, nullable=True)

    # Relationships
    examination = db.relationship('Examination', back_populates='rubrics')
    evaluation_details = db.relationship('EvaluationDetail', back_populates='rubric', cascade='all, delete-orphan', lazy='dynamic')

    def __repr__(self):
        return f"<Rubric {self.id}: {self.criterion_name} (Max: {self.maximum_marks})>"

# FK constraint & cascade delete linked with Examination
