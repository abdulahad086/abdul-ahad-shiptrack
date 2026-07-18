import logging
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

import app.crud as crud
from app.audit import write_audit_line
from app.auth import require_api_key
from app.database import get_db
from app.schemas import ApplicationCreate, ApplicationOut

logger = logging.getLogger("shiptrack")
router = APIRouter(tags=["applications"])


@router.post(
    "/applications",
    response_model=ApplicationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new application",
    dependencies=[Depends(require_api_key)],
)
def create_application(
    app_in: ApplicationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    # Check duplicate name
    existing_app = crud.get_application_by_name(db, name=app_in.name)
    if existing_app:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "duplicate_name",
                "message": f"Application '{app_in.name}' already exists",
            },
        )

    new_app = crud.create_application(db, app_in)

    # Log the action (stdout)
    logger.info(f"application created id={new_app.id} name={new_app.name}")

    # Queue audit log line
    background_tasks.add_task(
        write_audit_line,
        "CREATE_APPLICATION",
        {"application_id": new_app.id, "name": new_app.name},
    )

    return new_app


@router.get(
    "/applications",
    response_model=list[ApplicationOut],
    status_code=status.HTTP_200_OK,
    summary="List all applications",
)
def list_applications(db: Session = Depends(get_db)):
    return crud.get_applications(db)
