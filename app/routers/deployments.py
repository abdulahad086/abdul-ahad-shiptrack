import logging
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

import app.crud as crud
from app.audit import write_audit_line
from app.auth import require_api_key
from app.database import get_db
from app.models import DeploymentStatus
from app.schemas import DeploymentCreate, DeploymentOut

logger = logging.getLogger("shiptrack")
router = APIRouter(tags=["deployments"])


@router.post(
    "/deployments",
    response_model=DeploymentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Record a deployment",
    dependencies=[Depends(require_api_key)],
)
def create_deployment(
    dep_in: DeploymentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    # Check if application exists
    app_db = crud.get_application(db, app_id=dep_in.application_id)
    if not app_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "not_found",
                "message": f"Application {dep_in.application_id} not found",
            },
        )

    new_dep = crud.create_deployment(db, dep_in)

    # Log action (stdout)
    logger.info(
        f"deployment created id={new_dep.id} app_id={new_dep.application_id} env={new_dep.environment.value}"
    )

    # Queue audit log line
    background_tasks.add_task(
        write_audit_line,
        "CREATE_DEPLOYMENT",
        {
            "deployment_id": new_dep.id,
            "application_id": new_dep.application_id,
            "version": new_dep.version,
            "environment": new_dep.environment.value,
            "status": new_dep.status.value,
        },
    )

    return new_dep


@router.get(
    "/deployments",
    response_model=list[DeploymentOut],
    status_code=status.HTTP_200_OK,
    summary="List all deployments",
)
def list_deployments(db: Session = Depends(get_db)):
    return crud.get_deployments(db)


@router.get(
    "/deployments/{deployment_id}",
    response_model=DeploymentOut,
    status_code=status.HTTP_200_OK,
    summary="Fetch one deployment",
)
def get_deployment(
    deployment_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
):
    dep = crud.get_deployment(db, dep_id=deployment_id)
    if not dep:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "not_found",
                "message": f"Deployment {deployment_id} not found",
            },
        )
    return dep


@router.post(
    "/deployments/{deployment_id}/rollback",
    response_model=DeploymentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Roll back a deployment",
    dependencies=[Depends(require_api_key)],
)
def rollback_deployment(
    background_tasks: BackgroundTasks,
    deployment_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
):
    # Fetch target deployment
    target = crud.get_deployment(db, dep_id=deployment_id)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "not_found",
                "message": f"Deployment {deployment_id} not found",
            },
        )

    # Check preconditions
    if target.status in (DeploymentStatus.pending, DeploymentStatus.failed):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "invalid_rollback",
                "message": f"Cannot roll back deployment {deployment_id} with status '{target.status.value}'; only 'succeeded' deployments can be rolled back",
            },
        )

    if target.status == DeploymentStatus.rolled_back:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "invalid_rollback",
                "message": f"Deployment {deployment_id} is already rolled back",
            },
        )

    # Find previous succeeded deployment
    prev = crud.get_previous_succeeded_deployment(db, target=target)
    if not prev:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "invalid_rollback",
                "message": f"No previous succeeded deployment for application {target.application_id} in environment '{target.environment.value}'",
            },
        )

    # Perform transaction rollback and create new deployment
    new_dep = crud.execute_rollback(db, target=target, prev=prev)

    # Log action (stdout)
    logger.info(f"deployment rolled back id={new_dep.id} target_id={target.id}")

    # Queue audit log line
    background_tasks.add_task(
        write_audit_line,
        "ROLLBACK",
        {
            "deployment_id": target.id,
            "application_id": target.application_id,
            "environment": target.environment.value,
            "rolled_back_from_version": target.version,
            "rolled_back_to_version": prev.version,
            "new_deployment_id": new_dep.id,
        },
    )

    return new_dep
