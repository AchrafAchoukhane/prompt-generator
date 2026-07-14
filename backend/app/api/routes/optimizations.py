from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.optimization import Optimization
from app.schemas.optimization import OptimizationCreate, OptimizationList, OptimizationRead
from app.services.optimization_service import create_optimization

router = APIRouter(prefix="/optimizations", tags=["optimizations"])


@router.post("", response_model=OptimizationRead, status_code=status.HTTP_201_CREATED)
def optimize_prompt(payload: OptimizationCreate, db: Session = Depends(get_db)) -> Optimization:
    return create_optimization(db, payload.prompt)


@router.get("", response_model=OptimizationList)
def list_optimizations(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> OptimizationList:
    total = db.scalar(select(func.count()).select_from(Optimization)) or 0
    items = db.scalars(
        select(Optimization).order_by(Optimization.created_at.desc()).offset(offset).limit(limit)
    ).all()
    return OptimizationList(items=list(items), total=total)


@router.get("/{optimization_id}", response_model=OptimizationRead)
def get_optimization(optimization_id: str, db: Session = Depends(get_db)) -> Optimization:
    record = db.get(Optimization, optimization_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Optimization not found")
    return record

