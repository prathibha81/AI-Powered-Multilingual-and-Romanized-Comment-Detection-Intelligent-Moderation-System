from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Analysis(db.Model):
    __tablename__ = "analyses"

    id = db.Column(db.Integer, primary_key=True)
    source_url = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    is_demo = db.Column(db.Boolean, default=False, nullable=False)
    total_scraped = db.Column(db.Integer, default=0, nullable=False)
    comments_analyzed = db.Column(db.Integer, default=0, nullable=False)
    total_comments = db.Column(db.Integer, default=0, nullable=False)
    toxic_comments = db.Column(db.Integer, default=0, nullable=False)
    non_toxic_comments = db.Column(db.Integer, default=0, nullable=False)
    toxicity_percentage = db.Column(db.Float, default=0, nullable=False)
    average_confidence = db.Column(db.Float, default=0, nullable=False)

    comments = db.relationship(
        "CommentResult",
        back_populates="analysis",
        cascade="all, delete-orphan",
        order_by="CommentResult.id",
    )

    def to_dict(self, include_comments: bool = False) -> dict:
        result = {
            "id": self.id,
            "source_url": self.source_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_demo": self.is_demo,
            "total_scraped": self.total_scraped,
            "comments_analyzed": self.comments_analyzed,
            "total_comments": self.total_comments,
            "toxic_comments": self.toxic_comments,
            "non_toxic_comments": self.non_toxic_comments,
            "toxicity_percentage": round(self.toxicity_percentage or 0, 2),
            "average_confidence": round(self.average_confidence or 0, 4),
        }
        if include_comments:
            result["comments"] = [comment.to_dict() for comment in self.comments]
        return result


class CommentResult(db.Model):
    __tablename__ = "comment_results"

    id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(
        db.Integer, db.ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False
    )
    comment_text = db.Column(db.Text, nullable=False)
    cleaned_text = db.Column(db.Text, nullable=False)
    label = db.Column(db.String(20), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    username = db.Column(db.String(255))
    timestamp = db.Column(db.String(100))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    analysis = db.relationship("Analysis", back_populates="comments")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "text": self.comment_text,
            "cleaned_text": self.cleaned_text,
            "label": self.label,
            "confidence": round(self.confidence or 0, 4),
            "username": self.username or "",
            "timestamp": self.timestamp or "",
        }
