from flask import Flask, jsonify, request
from pydantic import BaseModel, BaseSettings
from typing import Optional
from flask_pydantic_spec import FlaskPydanticSpec, Response, Request
from sqlalchemy import create_engine, Integer, Float, TIMESTAMP, Column, String, Boolean, text, ForeignKey, Date
# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, declarative_base


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


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Start the API
app = Flask(__name__)
api = FlaskPydanticSpec("flask")


# Pydantic Schemas
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


class HealthExportResponseModel(BaseModel):
    accepted: bool


# SQLAlchemy Classes
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String,  nullable=False)
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


# Routes
@app.route("/hello/", methods=["GET"], strict_slashes=False)
def welcome():
    """Test if API is alive"""
    return jsonify({"greeting": "Hello World!"}), 200


@app.route("/health-export/", methods=["POST"], strict_slashes=False)
@api.validate(
    body=Request(HealthExportBodyModel),
    resp=Response(HTTP_200=HealthExportResponseModel),
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
                new_weight = Weight(**{
                                        'date': data.date,
                                        'weight': data.qty,
                                        'user_id': user_id})
                print(data.date, data.qty)
                # db.add(new_weight)
                # db.commit()
                # db.refresh(new_weight)
        else:
            print(f'skipping {metric.name}')
            # for data in metric.data:
            #     print(data.date, data.qty)
    return HealthExportResponseModel(accepted=True).dict()


if __name__ == "__main__":
    api.register(app)
    app.run(host="0.0.0.0", port=8787)
