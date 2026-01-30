"""
Preview Service - Generates DOCX previews using MailMerge

One plaintiff and one defendant per session. Values come from plaintiffs and defendants
tables and are merged into the template (Plaintiff_name_, Defendant_name, etc.).
Other fields come from field_values.
"""
import logging
from pathlib import Path
from typing import Dict

from sqlalchemy.orm import Session
from mailmerge import MailMerge

from app.core.config import settings
from app.db.models import Session as SessionModel, FieldValue, Plaintiff, Defendant

logger = logging.getLogger(__name__)


class PreviewService:
    """Service for generating DOCX previews using MailMerge (single plaintiff, single defendant)."""

    def __init__(self, db: Session):
        self.db = db

    def _resolve_template_path(self, template_path: str) -> Path:
        """Resolve template file path (handles relative/absolute paths)."""
        file_path = Path(template_path)
        if file_path.is_absolute():
            if not file_path.exists():
                raise FileNotFoundError(f"Template file not found: {template_path}")
            return file_path

        backend_dir = Path(__file__).parent.parent.parent
        resolved_path = backend_dir / template_path
        if not resolved_path.exists():
            template_dir = Path(settings.TEMPLATE_DIR)
            if template_dir.is_absolute():
                resolved_path = template_dir / Path(template_path).name
            else:
                resolved_path = backend_dir / template_dir / Path(template_path).name
        if not resolved_path.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")
        return resolved_path

    def generate_preview(self, session: SessionModel) -> str:
        """
        Generate a DOCX preview for a session by merging field values into the template.
        Uses at most one plaintiff and one defendant from DB; fills template fields directly.
        """
        if not session.template:
            raise ValueError(f"Session {session.uuid} has no associated template")

        template = session.template
        preview_dir = Path(settings.PREVIEW_DIR)
        if not preview_dir.is_absolute():
            backend_dir = Path(__file__).parent.parent.parent
            preview_dir = backend_dir / preview_dir
        preview_dir.mkdir(parents=True, exist_ok=True)
        preview_filename = f"session_{session.uuid}_preview.docx"
        preview_path = preview_dir / preview_filename

        # Build merge dict from field_values
        values_dict: Dict[str, str] = {}
        field_values = self.db.query(FieldValue).filter(FieldValue.session_id == session.id).all()
        for fv in field_values:
            tf = fv.template_field
            if not tf:
                continue
            merge_name = (tf.placeholder or "").replace("«", "").replace("»", "").strip()
            if not merge_name:
                continue
            values_dict[merge_name] = fv.final_value if fv.final_value is not None else ""

        # One plaintiff, one defendant: overlay from tables (exact template field names)
        plaintiff = (
            self.db.query(Plaintiff)
            .filter(Plaintiff.session_id == session.id)
            .order_by(Plaintiff.index)
            .first()
        )
        defendant = (
            self.db.query(Defendant)
            .filter(Defendant.session_id == session.id)
            .order_by(Defendant.index)
            .first()
        )

        if plaintiff:
            values_dict["Plaintiff_name_"] = (plaintiff.name or "").strip()
        if defendant:
            values_dict["Defendant_name"] = (defendant.name or "").strip()
            values_dict["Defendant_Street_Address_"] = (defendant.address or "").strip()
            values_dict["Defendant_City"] = (defendant.city or "").strip()
            values_dict["Defendant_State"] = (defendant.state or "").strip()
            values_dict["Defendant_Zip_code"] = (defendant.zip_code or "").strip()
            values_dict["Defendant_County"] = (defendant.county or "").strip()

        logger.info(f"Generating preview for session {session.uuid}: merging {len(values_dict)} fields")

        template_path = self._resolve_template_path(template.file_path)
        with MailMerge(str(template_path)) as doc:
            doc.merge(**values_dict)
            doc.write(str(preview_path))

        logger.info(f"Preview generated successfully: {preview_path}")
        return str(preview_path)
