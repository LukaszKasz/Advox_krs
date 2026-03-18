from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import timedelta
from urllib import error, request
import json
import csv
import io
from openpyxl import Workbook

from database import engine, get_db, Base
from models import User, AppSetting, AdvoxKrsOrganization
from auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="advox_krs Auth API",
    description="Authentication API - Base Template",
    version="1.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for request/response
class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class LoginRequest(BaseModel):
    username: str
    password: str


class RejestrioSettingsRequest(BaseModel):
    apiKey: str


class RejestrioSettingsResponse(BaseModel):
    hasApiKey: bool


class RejestrioKrsRequest(BaseModel):
    krs: str


def normalize_krs(krs: str) -> str:
    normalized = "".join(char for char in krs if char.isdigit())
    if not normalized or len(normalized) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="KRS must contain from 1 to 10 digits",
        )
    return normalized


def get_setting_value(db: Session, key: str) -> str | None:
    setting = db.query(AppSetting).filter(AppSetting.key == key).first()
    return setting.value if setting else None


def set_setting_value(db: Session, key: str, value: str) -> None:
    setting = db.query(AppSetting).filter(AppSetting.key == key).first()
    if setting:
        setting.value = value
    else:
        setting = AppSetting(key=key, value=value)
        db.add(setting)
    db.commit()


def dump_json(value) -> str | None:
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False)


def serialize_organization_row(organization: AdvoxKrsOrganization) -> dict:
    serialized = {}
    for column in AdvoxKrsOrganization.__table__.columns:
        value = getattr(organization, column.name)
        if hasattr(value, "isoformat"):
            serialized[column.name] = value.isoformat()
        else:
            serialized[column.name] = value
    return serialized


def get_saved_organizations(db: Session) -> list[AdvoxKrsOrganization]:
    return (
        db.query(AdvoxKrsOrganization)
        .order_by(AdvoxKrsOrganization.updated_at.desc())
        .all()
    )


def build_export_rows(organizations: list[AdvoxKrsOrganization]) -> list[dict]:
    rows = []
    for organization in organizations:
        serialized = serialize_organization_row(organization)
        rows.append({field: serialized.get(field) for field in CSV_EXPORT_FIELDS})
    return rows


CSV_EXPORT_FIELDS = [
    "nazwa_pelna",
    "krs",
    "nip",
    "glowna_osoba_imie_nazwisko",
    "adres_miejscowosc",
    "ostatnie_sprawozdanie_rocznik",
    "aktywa",
    "pasywa",
    "przychody",
    "koszty",
    "zysk",
    "podatek_dochodowy",
]


def upsert_organization(db: Session, organization_data: dict) -> AdvoxKrsOrganization:
    nazwy = organization_data.get("nazwy") or {}
    numery = organization_data.get("numery") or {}
    stan = organization_data.get("stan") or {}
    glowna_osoba = organization_data.get("glowna_osoba") or {}
    adres = organization_data.get("adres") or {}
    adres_teryt = adres.get("teryt") or {}
    krs_rejestry = organization_data.get("krs_rejestry") or {}
    krs_wpisy = organization_data.get("krs_wpisy") or {}
    krs_powiazania = organization_data.get("krs_powiazania_liczby") or {}
    ostatnie_sprawozdanie = organization_data.get("ostatnie_sprawozdanie") or {}
    glowne_pola = ostatnie_sprawozdanie.get("glowne_pola") or {}
    metadane = organization_data.get("metadane") or {}

    krs = numery.get("krs")
    if not krs:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Rejestr.io response does not include KRS",
        )

    record = (
        db.query(AdvoxKrsOrganization)
        .filter(AdvoxKrsOrganization.krs == krs)
        .first()
    )
    if not record:
        record = AdvoxKrsOrganization(krs=krs, raw_json="{}")
        db.add(record)

    record.rejestrio_org_id = organization_data.get("id")
    record.typ = organization_data.get("typ")
    record.nazwa_pelna = nazwy.get("pelna")
    record.nazwa_skrocona = nazwy.get("skrocona")
    record.krs = krs
    record.nip = numery.get("nip")
    record.regon = numery.get("regon")
    record.forma_prawna = stan.get("forma_prawna")
    record.czy_wykreslona = stan.get("czy_wykreslona")
    record.w_likwidacji = stan.get("w_likwidacji")
    record.w_upadlosci = stan.get("w_upadlosci")
    record.w_zawieszeniu = stan.get("w_zawieszeniu")
    record.wielkosc = stan.get("wielkosc")
    record.czy_jest_na_gpw = stan.get("czy_jest_na_gpw")
    record.czy_spolka_skarbu_panstwa = stan.get("czy_spolka_skarbu_panstwa")
    record.czy_otrzymala_pomoc_publiczna = stan.get("czy_otrzymala_pomoc_publiczna")
    record.czy_dofinansowana_przez_ue = stan.get("czy_dofinansowana_przez_ue")
    record.czy_pozytku_publicznego = stan.get("czy_pozytku_publicznego")
    record.glowna_osoba_id = str(glowna_osoba.get("id")) if glowna_osoba.get("id") is not None else None
    record.glowna_osoba_imie_nazwisko = glowna_osoba.get("imiona_i_nazwisko")
    record.adres_panstwo = adres.get("panstwo")
    record.adres_wojewodztwo = adres_teryt.get("wojewodztwo")
    record.adres_powiat = adres_teryt.get("powiat")
    record.adres_gmina = adres_teryt.get("gmina")
    record.adres_miejscowosc = adres.get("miejscowosc")
    record.adres_poczta = adres.get("poczta")
    record.adres_kod = adres.get("kod")
    record.adres_ulica = adres.get("ulica")
    record.adres_nr_domu = adres.get("nr_domu")
    record.krs_rejestr_przedsiebiorcow_data_wpisu = krs_rejestry.get("rejestr_przedsiebiorcow_data_wpisu")
    record.krs_wpis_pierwszy_data = krs_wpisy.get("pierwszy_data")
    record.krs_wpis_najnowszy_data = krs_wpisy.get("najnowszy_data")
    record.krs_wpis_najnowszy_numer = krs_wpisy.get("najnowszy_numer")
    record.krs_powiazania_aktualne = krs_powiazania.get("aktualne")
    record.krs_powiazania_przeszle = krs_powiazania.get("przeszle")
    record.ostatnie_sprawozdanie_id = ostatnie_sprawozdanie.get("id")
    record.ostatnie_sprawozdanie_data_od = ostatnie_sprawozdanie.get("data_od")
    record.ostatnie_sprawozdanie_data_do = ostatnie_sprawozdanie.get("data_do")
    record.ostatnie_sprawozdanie_rocznik = ostatnie_sprawozdanie.get("rocznik")
    record.ostatnie_sprawozdanie_rocznik_przyblizony = ostatnie_sprawozdanie.get("rocznik_przyblizony")
    record.aktywa = (glowne_pola.get("aktywa") or {}).get("wartosc")
    record.pasywa = (glowne_pola.get("pasywa") or {}).get("wartosc")
    record.przychody = (glowne_pola.get("przychody") or {}).get("wartosc")
    record.koszty = (glowne_pola.get("koszty") or {}).get("wartosc")
    record.zysk = (glowne_pola.get("zysk") or {}).get("wartosc")
    record.podatek_dochodowy = (glowne_pola.get("podatek_dochodowy") or {}).get("wartosc")
    record.raw_json = dump_json(organization_data) or "{}"
    record.metadane_json = dump_json(metadane)
    record.adres_json = dump_json(adres)
    record.glowna_osoba_json = dump_json(glowna_osoba)
    record.krs_rejestry_json = dump_json(krs_rejestry)
    record.krs_wpisy_json = dump_json(krs_wpisy)
    record.krs_powiazania_liczby_json = dump_json(krs_powiazania)
    record.ostatnie_sprawozdanie_json = dump_json(ostatnie_sprawozdanie)
    record.stan_json = dump_json(stan)
    record.nazwy_json = dump_json(nazwy)
    record.numery_json = dump_json(numery)

    db.commit()
    db.refresh(record)
    return record


def make_rejestrio_request(api_key: str, url: str) -> dict | list:
    headers_to_try = [
        {"Authorization": api_key, "Accept": "application/json"},
        {"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
    ]

    last_error = None

    for headers in headers_to_try:
        req = request.Request(url, headers=headers, method="GET")
        try:
            with request.urlopen(req, timeout=15) as response:
                body = response.read().decode("utf-8")
                return json.loads(body)
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            try:
                details = json.loads(body) if body else {}
            except json.JSONDecodeError:
                details = {"raw": body}

            last_error = HTTPException(
                status_code=exc.code,
                detail={
                    "message": "Rejestr.io request failed",
                    "rejestrio": details,
                },
            )

            if exc.code not in (401, 403) or headers["Authorization"].startswith("Bearer "):
                raise last_error
        except error.URLError as exc:
            last_error = HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to connect to Rejestr.io: {exc.reason}",
            )
            raise last_error

    if last_error:
        raise last_error

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="Unexpected Rejestr.io error",
    )


def fetch_rejestrio_company(api_key: str, rejestrio_id: str) -> dict | list:
    return make_rejestrio_request(api_key, f"https://rejestr.io/api/v2/org/{rejestrio_id}")


def fetch_rejestrio_financial_document(api_key: str, rejestrio_id: str) -> dict | list:
    documents_url = f"https://rejestr.io/api/v2/org/{rejestrio_id}/krs-dokumenty"
    documents_response = make_rejestrio_request(api_key, documents_url)

    if not isinstance(documents_response, list):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unexpected Rejestr.io documents response",
        )

    selected_document_id = None

    for period in documents_response:
        documents = period.get("dokumenty", []) if isinstance(period, dict) else []
        for document in documents:
            if document.get("czy_ma_json"):
                selected_document_id = document.get("id")
                break
        if selected_document_id:
            break

    if not selected_document_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No financial document in JSON format was found for this organization",
        )

    document_url = (
        f"https://rejestr.io/api/v2/org/{rejestrio_id}/krs-dokumenty/"
        f"{selected_document_id}?format=json"
    )
    return make_rejestrio_request(api_key, document_url)


@app.get("/")
def read_root():
    """
    Root endpoint - API health check.
    """
    return {
        "message": "advox_krs Auth API is running",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user.
    """
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@app.post("/login", response_model=Token)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Login endpoint - returns JWT token.
    """
    # Find user by username
    user = db.query(User).filter(User.username == login_data.username).first()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.
    Protected endpoint - requires valid JWT token.
    """
    return current_user


@app.get("/health")
def health_check():
    """
    Health check endpoint for Docker.
    """
    return {"status": "healthy"}


@app.get("/api/settings/rejestrio", response_model=RejestrioSettingsResponse)
def get_rejestrio_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {"hasApiKey": bool(get_setting_value(db, "rejestrio_api_key"))}


@app.post("/api/settings/rejestrio", response_model=RejestrioSettingsResponse)
def save_rejestrio_settings(
    payload: RejestrioSettingsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    api_key = payload.apiKey.strip()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="API key is required",
        )

    set_setting_value(db, "rejestrio_api_key", api_key)
    return {"hasApiKey": True}


@app.post("/api/rejestrio/company")
def get_rejestrio_company(
    payload: RejestrioKrsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    api_key = get_setting_value(db, "rejestrio_api_key")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rejestr.io API key is not configured",
        )

    normalized_krs = normalize_krs(payload.krs)
    organization_data = fetch_rejestrio_company(api_key, normalized_krs)
    if not isinstance(organization_data, dict):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unexpected Rejestr.io organization response",
        )

    upsert_organization(db, organization_data)
    return organization_data


@app.get("/api/rejestrio/organizations")
def list_saved_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    organizations = get_saved_organizations(db)

    return [serialize_organization_row(organization) for organization in organizations]


@app.get("/api/rejestrio/organizations/export")
def export_saved_organizations_csv(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    organizations = get_saved_organizations(db)
    export_rows = build_export_rows(organizations)

    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=CSV_EXPORT_FIELDS,
    )
    writer.writeheader()

    for row in export_rows:
        writer.writerow(row)

    return Response(
        content=output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="advox_krs_organizations.csv"'
        },
    )


@app.get("/api/rejestrio/organizations/export/xlsx")
def export_saved_organizations_xlsx(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    organizations = get_saved_organizations(db)
    export_rows = build_export_rows(organizations)

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Organizations"
    sheet.append(CSV_EXPORT_FIELDS)

    for row in export_rows:
        sheet.append([row.get(field) for field in CSV_EXPORT_FIELDS])

    output = io.BytesIO()
    workbook.save(output)

    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": 'attachment; filename="advox_krs_organizations.xlsx"'
        },
    )


@app.post("/api/rejestrio/financial-document")
def get_rejestrio_financial_document(
    payload: RejestrioKrsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    api_key = get_setting_value(db, "rejestrio_api_key")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rejestr.io API key is not configured",
        )

    normalized_krs = normalize_krs(payload.krs)
    return fetch_rejestrio_financial_document(api_key, normalized_krs)
