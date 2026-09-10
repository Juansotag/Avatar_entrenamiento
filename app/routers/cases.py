from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session as DBSession
from sqlmodel import select

from app.db import get_db
from app.models import Case
from app.schemas import CaseCreate, CaseRead, CaseUpdate

router = APIRouter(prefix="/api/cases", tags=["cases"])


@router.post("", response_model=CaseRead)
def create_case(payload: CaseCreate, db: DBSession = Depends(get_db)) -> Case:
    case = Case(
        title=payload.title,
        scenario_text=payload.scenario_text,
        duration_seconds=payload.duration_seconds or 300,
        user_name=payload.user_name or "",
        user_role=payload.user_role or "",
        user_organization=payload.user_organization or "",
        user_objectives=payload.user_objectives or "",
        avatar_name=payload.avatar_name or "Contraparte",
        avatar_profile=payload.avatar_profile,
        avatar_tone=payload.avatar_tone,
        avatar_rules=payload.avatar_rules,
        avatar_voice=payload.avatar_voice or "onyx",
        persona_notes=payload.persona_notes,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


@router.get("", response_model=list[CaseRead])
def list_cases(db: DBSession = Depends(get_db)) -> list[Case]:
    return list(db.exec(select(Case).order_by(Case.created_at.desc())))


@router.get("/{case_id}", response_model=CaseRead)
def get_case(case_id: int, db: DBSession = Depends(get_db)) -> Case:
    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Caso no encontrado")
    return case


@router.put("/{case_id}", response_model=CaseRead)
def update_case(case_id: int, payload: CaseUpdate, db: DBSession = Depends(get_db)) -> Case:
    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Caso no encontrado")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(case, key, value)
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


@router.delete("/{case_id}", status_code=204)
def delete_case(case_id: int, db: DBSession = Depends(get_db)) -> None:
    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Caso no encontrado")
    db.delete(case)
    db.commit()
