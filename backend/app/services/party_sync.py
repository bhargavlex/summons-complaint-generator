"""
Sync plaintiff and defendant tables from field_values (extracted or manual).

When LLM or user fills field_values for plaintiff_name, defendant_name, etc.,
this copies those values into the one plaintiff and one defendant row per session
so the preview and template merge use the same source.
"""
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import Session as SessionModel, FieldValue, Plaintiff, Defendant

logger = logging.getLogger(__name__)

# field_key (normalized lower) -> (table, attr). Covers common template field_key names.
_PLAINTIFF_KEYS = {
    "plaintiff_name": "name",
    "plaintiff_name_": "name",
    "plaintiff_address": "address",
    "plaintiff_street_address": "address",
    "plaintiff_street_address_": "address",
    "plaintiff_city": "city",
    "plaintiff_city_": "city",
    "plaintiff_state": "state",
    "plaintiff_state_": "state",
    "plaintiff_zip_code": "zip_code",
    "plaintiff_zip": "zip_code",
    "plaintiff_county": "county",
    "plaintiff_county_": "county",
}
_DEFENDANT_KEYS = {
    "defendant_name": "name",
    "defendant_name_": "name",
    "defendant_street_address": "address",
    "defendant_street_address_": "address",
    "defendant_city": "city",
    "defendant_state": "state",
    "defendant_zip_code": "zip_code",
    "defendant_county": "county",
}


def sync_parties_from_field_values(session: SessionModel, db: Session) -> None:
    """
    Build one plaintiff and one defendant from this session's field_values
    (final_value = manual_value or extracted_value) and upsert into plaintiffs/defendants.

    Call this after field values are updated (e.g. PATCH field, or after LLM extraction).
    """
    if not session:
        return
    field_values = (
        db.query(FieldValue)
        .filter(FieldValue.session_id == session.id)
        .all()
    )
    key_to_value: dict[str, str] = {}
    for fv in field_values:
        tf = fv.template_field
        if not tf or not tf.field_key:
            continue
        val = fv.final_value
        if val is None:
            continue
        key_to_value[(tf.field_key or "").strip().lower()] = (val or "").strip()

    def get_attr(keys_map: dict[str, str], attr: str) -> str:
        for k, a in keys_map.items():
            if a == attr and k in key_to_value:
                return key_to_value[k] or ""
        return ""

    # Plaintiff
    p_name = get_attr(_PLAINTIFF_KEYS, "name") or get_attr({"plaintiff_name_": "name"}, "name")
    p_address = get_attr(_PLAINTIFF_KEYS, "address")
    p_city = get_attr(_PLAINTIFF_KEYS, "city")
    p_state = get_attr(_PLAINTIFF_KEYS, "state")
    p_zip = get_attr(_PLAINTIFF_KEYS, "zip_code")
    p_county = get_attr(_PLAINTIFF_KEYS, "county")
    if p_name or p_address or p_city or p_state or p_zip or p_county:
        row = db.query(Plaintiff).filter(Plaintiff.session_id == session.id).order_by(Plaintiff.index).first()
        if row:
            row.name = p_name or row.name
            row.address = p_address or row.address
            row.city = p_city or row.city
            row.state = p_state or row.state
            row.zip_code = p_zip or row.zip_code
            row.county = p_county or row.county
        else:
            row = Plaintiff(
                session_id=session.id,
                index=1,
                name=p_name,
                address=p_address,
                city=p_city,
                state=p_state,
                zip_code=p_zip,
                county=p_county,
            )
            db.add(row)

    # Defendant
    d_name = get_attr(_DEFENDANT_KEYS, "name")
    d_address = get_attr(_DEFENDANT_KEYS, "address")
    d_city = get_attr(_DEFENDANT_KEYS, "city")
    d_state = get_attr(_DEFENDANT_KEYS, "state")
    d_zip = get_attr(_DEFENDANT_KEYS, "zip_code")
    d_county = get_attr(_DEFENDANT_KEYS, "county")
    if d_name or d_address or d_city or d_state or d_zip or d_county:
        row = db.query(Defendant).filter(Defendant.session_id == session.id).order_by(Defendant.index).first()
        if row:
            row.name = d_name or row.name
            row.address = d_address or row.address
            row.city = d_city or row.city
            row.state = d_state or row.state
            row.zip_code = d_zip or row.zip_code
            row.county = d_county or row.county
        else:
            row = Defendant(
                session_id=session.id,
                index=1,
                name=d_name,
                address=d_address,
                city=d_city,
                state=d_state,
                zip_code=d_zip,
                county=d_county,
            )
            db.add(row)

    try:
        db.commit()
    except Exception as e:
        logger.warning("sync_parties_from_field_values commit failed: %s", e)
        db.rollback()
