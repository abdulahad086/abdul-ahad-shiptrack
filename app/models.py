import enum
from datetime import datetime
from sqlalchemy import Enum as SAEnum, ForeignKey, Integer, String, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Environment(str, enum.Enum):
    dev = "dev"
    staging = "staging"
    prod = "prod"


class DeploymentStatus(str, enum.Enum):
    pending = "pending"
    succeeded = "succeeded"
    failed = "failed"
    rolled_back = "rolled_back"


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    repo_url: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    deployments: Mapped[list["Deployment"]] = relationship(
        "Deployment",
        back_populates="application",
        cascade="all, delete-orphan",
    )


class Deployment(Base):
    __tablename__ = "deployments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    environment: Mapped[Environment] = mapped_column(
        SAEnum(Environment, name="environment_enum", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    status: Mapped[DeploymentStatus] = mapped_column(
        SAEnum(DeploymentStatus, name="deployment_status_enum", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=DeploymentStatus.pending,
        server_default="pending",
    )
    deployed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    application: Mapped["Application"] = relationship(
        "Application",
        back_populates="deployments",
    )

    __table_args__ = (
        Index(
            "ix_deployments_lookup",
            "application_id",
            "environment",
            "status",
            "deployed_at",
        ),
    )
