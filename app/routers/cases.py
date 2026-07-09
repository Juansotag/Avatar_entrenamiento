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
        persona_notes=payload.persona_notes,
        avatar_name=payload.avatar_name,
        duration_seconds=payload.duration_seconds,
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
    if payload.title is not None:
        case.title = payload.title
    if payload.scenario_text is not None:
        case.scenario_text = payload.scenario_text
    if payload.persona_notes is not None:
        case.persona_notes = payload.persona_notes
    if payload.avatar_name is not None:
        case.avatar_name = payload.avatar_name
    if payload.duration_seconds is not None:
        case.duration_seconds = payload.duration_seconds
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
