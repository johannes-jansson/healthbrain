from flask import Flask, jsonify, request
from pydantic import BaseModel, BaseSettings
from typing import Optional
from flask_pydantic_spec import FlaskPydanticSpec, Response, Request
from sqlalchemy import create_engine, Integer, Float, TIMESTAMP, Column, String, Boolean, text, ForeignKey, Date
# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import insert


# Settings object, based on pydantic's dotenv implementation
class Settings(BaseSettings):
    DATABASE_PORT: int
    POSTGRES_PASSWORD: str
    POSTGRES_USER: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_HOSTNAME: str
    CLIENT_ORIGIN: str

    class Config:
        env_file = './.env'


settings = Settings()


# Database setup
SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOSTNAME}:{settings.DATABASE_PORT}/{settings.POSTGRES_DB}"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Start the API
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URL
api = FlaskPydanticSpec("flask")
db = SQLAlchemy(app)


# Pydantic Schemas
class CreateUserBodyModel(BaseModel):
    name: str

class HealthExportMetricDataModel(BaseModel):
    qty: Optional[float]
    date: Optional[str]
    source: Optional[str]


class HealthExportMetricModel(BaseModel):
    data: Optional[list[HealthExportMetricDataModel]]
    name: str
    units: str


class HealthExportModel(BaseModel):
    metrics: list[HealthExportMetricModel]
    workouts: Optional[list]
    symptoms: Optional[list]


class HealthExportBodyModel(BaseModel):
    data: HealthExportModel



class ResponseModel(BaseModel):
    accepted: bool


# SQLAlchemy Classes
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String,  unique=True, nullable=False)
    weights = relationship("Weight")
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=text("now()"))
    updated_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=text("now()"))


class Weight(Base):
    __tablename__ = 'weights'
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    weight = Column(Float, nullable=False)
    user_id = Column(Integer,  ForeignKey("users.id"))
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=text("now()"))
    updated_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=text("now()"))
    __table_args__ = (
        db.UniqueConstraint('user_id', 'date',),
    )


# Routes
@app.route("/hello/", methods=["GET"], strict_slashes=False)
def welcome():
    """Test if API is alive"""
    return jsonify({"greeting": "Hello World!"}), 200

@app.route("/users/", methods=["POST"], strict_slashes=False)
@api.validate(
    body=Request(CreateUserBodyModel),
    resp=Response(HTTP_200=ResponseModel),
    tags=["api"],
)
def create_user():
    """Creates users"""
    body = CreateUserBodyModel.parse_obj(request.json)
    new_user = User(**{'name': body.name})
    db.session.add(new_user)
    db.session.commit()
    db.session.refresh(new_user)
    return ResponseModel(accepted=True).dict()


@app.route("/health-export/", methods=["POST"], strict_slashes=False)
@api.validate(
    body=Request(HealthExportBodyModel),
    resp=Response(HTTP_200=ResponseModel),
    tags=["api"],
)
def health_export():
    """Accept exports from the iOS app Health Auto Export

    Accepts a HealthExportBodyModel json, and returns a
    HealthExportResponeModel json.
    """
    if request.headers.get('Username') == 'jansson':
        user_id = 1
    else:
        raise
    body = HealthExportBodyModel.parse_obj(request.json)
    for metric in body.data.metrics:
        if metric.name == 'weight_body_mass':
            for data in metric.data:
                stmt = insert(Weight).values(
                    date=data.date,
                    weight=data.qty,
                    user_id=user_id)
                stmt = stmt.on_conflict_do_update(
                    index_elements=[Weight.date, Weight.user_id], set_=dict(weight=stmt.excluded.weight, updated_at='now()')
                ).returning(Weight)
                db.session.execute(stmt)
        else:
            print(f'skipping {metric.name}')
            # for data in metric.data:
            #     print(data.date, data.qty)
    db.session.commit()
    return ResponseModel(accepted=True).dict()


if __name__ == "__main__":
    api.register(app)
    app.run(host="0.0.0.0", port=8787)
