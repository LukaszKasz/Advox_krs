from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text
from sqlalchemy.sql import func
from database import Base


class User(Base):
    """
    User model for authentication.
    Stores user credentials and basic information.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<User(username={self.username}, email={self.email})>"


class AppSetting(Base):
    """
    Simple key-value application setting stored in the main database.
    """
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(String(2048), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self):
        return f"<AppSetting(key={self.key})>"


class AdvoxKrsOrganization(Base):
    __tablename__ = "advox_krs_organizations"

    id = Column(Integer, primary_key=True, index=True)
    rejestrio_org_id = Column(Integer, nullable=True)
    typ = Column(String(50), nullable=True)
    nazwa_pelna = Column(String(1024), nullable=True)
    nazwa_skrocona = Column(String(512), nullable=True)
    krs = Column(String(10), unique=True, index=True, nullable=False)
    nip = Column(String(20), nullable=True)
    regon = Column(String(20), nullable=True)
    forma_prawna = Column(String(512), nullable=True)
    czy_wykreslona = Column(Boolean, nullable=True)
    w_likwidacji = Column(Boolean, nullable=True)
    w_upadlosci = Column(Boolean, nullable=True)
    w_zawieszeniu = Column(Boolean, nullable=True)
    wielkosc = Column(String(100), nullable=True)
    czy_jest_na_gpw = Column(Boolean, nullable=True)
    czy_spolka_skarbu_panstwa = Column(Boolean, nullable=True)
    czy_otrzymala_pomoc_publiczna = Column(Boolean, nullable=True)
    czy_dofinansowana_przez_ue = Column(Boolean, nullable=True)
    czy_pozytku_publicznego = Column(Boolean, nullable=True)
    glowna_osoba_id = Column(String(50), nullable=True)
    glowna_osoba_imie_nazwisko = Column(String(512), nullable=True)
    adres_panstwo = Column(String(255), nullable=True)
    adres_wojewodztwo = Column(String(50), nullable=True)
    adres_powiat = Column(String(50), nullable=True)
    adres_gmina = Column(String(50), nullable=True)
    adres_miejscowosc = Column(String(255), nullable=True)
    adres_poczta = Column(String(255), nullable=True)
    adres_kod = Column(String(20), nullable=True)
    adres_ulica = Column(String(255), nullable=True)
    adres_nr_domu = Column(String(50), nullable=True)
    krs_rejestr_przedsiebiorcow_data_wpisu = Column(String(20), nullable=True)
    krs_wpis_pierwszy_data = Column(String(20), nullable=True)
    krs_wpis_najnowszy_data = Column(String(20), nullable=True)
    krs_wpis_najnowszy_numer = Column(Integer, nullable=True)
    krs_powiazania_aktualne = Column(Integer, nullable=True)
    krs_powiazania_przeszle = Column(Integer, nullable=True)
    ostatnie_sprawozdanie_id = Column(Integer, nullable=True)
    ostatnie_sprawozdanie_data_od = Column(String(20), nullable=True)
    ostatnie_sprawozdanie_data_do = Column(String(20), nullable=True)
    ostatnie_sprawozdanie_rocznik = Column(Integer, nullable=True)
    ostatnie_sprawozdanie_rocznik_przyblizony = Column(Integer, nullable=True)
    aktywa = Column(Float, nullable=True)
    pasywa = Column(Float, nullable=True)
    przychody = Column(Float, nullable=True)
    koszty = Column(Float, nullable=True)
    zysk = Column(Float, nullable=True)
    podatek_dochodowy = Column(Float, nullable=True)
    raw_json = Column(Text, nullable=False)
    metadane_json = Column(Text, nullable=True)
    adres_json = Column(Text, nullable=True)
    glowna_osoba_json = Column(Text, nullable=True)
    krs_rejestry_json = Column(Text, nullable=True)
    krs_wpisy_json = Column(Text, nullable=True)
    krs_powiazania_liczby_json = Column(Text, nullable=True)
    ostatnie_sprawozdanie_json = Column(Text, nullable=True)
    stan_json = Column(Text, nullable=True)
    nazwy_json = Column(Text, nullable=True)
    numery_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
