from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Application, Deployment, DeploymentStatus
from app.schemas import ApplicationCreate, DeploymentCreate


def get_application(db: Session, app_id: int) -> Application | None:
    return db.scalar(select(Application).where(Application.id == app_id))


def get_application_by_name(db: Session, name: str) -> Application | None:
    return db.scalar(select(Application).where(Application.name == name))


def get_applications(db: Session) -> list[Application]:
    return list(db.scalars(select(Application).order_by(Application.id.asc())).all())


def create_application(db: Session, app_in: ApplicationCreate) -> Application:
    db_app = Application(
        name=app_in.name,  # Validator already stripped it
        repo_url=app_in.repo_url,
    )
    db.add(db_app)
    db.commit()
    db.refresh(db_app)
    return db_app


def get_deployment(db: Session, dep_id: int) -> Deployment | None:
    return db.scalar(select(Deployment).where(Deployment.id == dep_id))


def get_deployments(db: Session) -> list[Deployment]:
    return list(
        db.scalars(
            select(Deployment).order_by(Deployment.deployed_at.desc(), Deployment.id.desc())
        ).all()
    )


def create_deployment(db: Session, dep_in: DeploymentCreate) -> Deployment:
    db_dep = Deployment(
        application_id=dep_in.application_id,
        version=dep_in.version,
        environment=dep_in.environment,
        status=dep_in.status,
        deployed_at=datetime.now(timezone.utc),
    )
    db.add(db_dep)
    db.commit()
    db.refresh(db_dep)
    return db_dep


def get_previous_succeeded_deployment(db: Session, target: Deployment) -> Deployment | None:
    return db.scalar(
        select(Deployment)
        .where(
            Deployment.application_id == target.application_id,
            Deployment.environment == target.environment,
            Deployment.status == DeploymentStatus.succeeded,
            Deployment.deployed_at < target.deployed_at,
        )
        .order_by(Deployment.deployed_at.desc(), Deployment.id.desc())
    )


def execute_rollback(db: Session, target: Deployment, prev: Deployment) -> Deployment:
    # Update target status
    target.status = DeploymentStatus.rolled_back

    # Create new deployment
    new_dep = Deployment(
        application_id=target.application_id,
        version=prev.version,
        environment=target.environment,
        status=DeploymentStatus.succeeded,
        deployed_at=datetime.now(timezone.utc),
    )
    db.add(new_dep)
    db.commit()
    db.refresh(new_dep)
    return new_dep
