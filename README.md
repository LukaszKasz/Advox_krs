# advox_krs - Authentication Template

Minimalna aplikacja z funkcjonalnością logowania jako podstawa dla wielu innych projektów.

## 📋 Opis

Aplikacja zawiera tylko niezbędne komponenty do autentykacji użytkowników:
- Rejestracja użytkownika (username, email, password)
- Logowanie użytkownika (JWT token)
- Prosty Dashboard po zalogowaniu
- Wylogowanie
- Wielojęzyczność (PL/EN)

## 🛠️ Stack Technologiczny

### Backend
- **FastAPI** - nowoczesny framework Python do budowy API
- **PostgreSQL 15** - relacyjna baza danych
- **SQLAlchemy** - ORM dla Pythona
- **JWT (python-jose)** - autentykacja tokenami
- **Bcrypt** - hashowanie haseł
- **Pydantic** - walidacja danych

### Frontend
- **React 18** - biblioteka UI
- **Vite** - build tool
- **React Router** - routing
- **Axios** - HTTP client
- **i18next** - wielojęzyczność
- **Tailwind CSS** - stylowanie

### Infrastructure
- **Docker** - konteneryzacja
- **Docker Compose** - orkiestracja kontenerów
- **Nginx** - serwer produkcyjny dla frontendu

## 📦 Wymagania

- Docker Desktop (z WSL2 na Windows)
- Docker Compose

## 🚀 Uruchomienie

### 1. Klonowanie/Przejście do katalogu projektu

```bash
cd /home/lkasztelan/projekty/advox_krs
```

### 2. Uruchomienie aplikacji

```bash
docker-compose up --build
```

Pierwsze uruchomienie może potrwać kilka minut (pobieranie obrazów, instalacja zależności).

### 3. Dostęp do aplikacji

- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:8001
- **API Documentation (Swagger)**: http://localhost:8001/docs
- **PostgreSQL**: localhost:5432

## 📝 Użytkowanie

### Rejestracja nowego użytkownika

1. Otwórz http://localhost:3001
2. Kliknij "Zarejestruj się" / "Sign Up"
3. Wypełnij formularz:
   - Username (unikalna nazwa użytkownika)
   - Email (unikalny adres email)
   - Password (minimum 6 znaków)
   - Confirm Password
4. Kliknij "Zarejestruj się" / "Sign Up"
5. Po pomyślnej rejestracji zostaniesz przekierowany do strony logowania

### Logowanie

1. Wprowadź username i password
2. Kliknij "Zaloguj się" / "Sign In"
3. Po pomyślnym logowaniu zostaniesz przekierowany do Dashboard

### Dashboard

Dashboard wyświetla:
- Informacje o zalogowanym użytkowniku (ID, username, email)
- Status autentykacji
- Listę funkcji POC
- Przycisk wylogowania

### Zmiana języka

Użyj przełącznika EN/PL w prawym górnym rogu aplikacji.

## 🗂️ Struktura Projektu

```
advox_krs/
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py              # Główny plik aplikacji FastAPI
│   ├── database.py          # Konfiguracja bazy danych
│   ├── models.py            # Model User
│   └── auth.py              # Logika autentykacji JWT
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── api.js           # API client
│       ├── i18n.js          # Konfiguracja wielojęzyczności
│       ├── index.css
│       └── components/
│           ├── LoginForm.jsx
│           ├── RegisterForm.jsx
│           ├── Dashboard.jsx
│           └── LanguageSwitcher.jsx
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

## 🔧 Konfiguracja

### Zmienne środowiskowe

Skopiuj `.env.example` do `.env` i dostosuj wartości:

```bash
cp .env.example .env
```

Domyślne wartości:
- `POSTGRES_USER=postgres`
- `POSTGRES_PASSWORD=postgres`
- `POSTGRES_DB=advox_krs_db`
- `SECRET_KEY=your-secret-key-change-in-production-please`

**WAŻNE**: Zmień `SECRET_KEY` w środowisku produkcyjnym!

## 🛑 Zatrzymanie aplikacji

```bash
docker-compose down
```

Aby usunąć również wolumeny (baza danych):

```bash
docker-compose down -v
```

## 🧹 Czyszczenie

Usunięcie wszystkich kontenerów, obrazów i wolumenów:

```bash
docker-compose down -v --rmi all
```

## 📊 API Endpoints

### Publiczne (bez autentykacji)

- `GET /` - Health check
- `POST /register` - Rejestracja użytkownika
- `POST /login` - Logowanie (zwraca JWT token)
- `GET /health` - Health check dla Dockera

### Chronione (wymagają JWT token)

- `GET /me` - Informacje o zalogowanym użytkowniku

## 🔐 Bezpieczeństwo

- Hasła są hashowane za pomocą bcrypt
- Autentykacja oparta na JWT tokenach
- Tokeny wygasają po 30 minutach
- CORS skonfigurowany dla localhost
- Walidacja danych wejściowych (Pydantic)
- Security headers w nginx

## 🐛 Troubleshooting

### Port już zajęty

Jeśli porty 3001, 8001 lub 5432 są zajęte, zmień je w `docker-compose.yml`:

```yaml
ports:
  - "3002:80"    # Frontend (zmień 3001 na 3002, jeśli 3001 też jest zajęty)
  - "8002:8000"  # Backend (zmień 8001 na 8002, jeśli 8001 też jest zajęty)
  - "5433:5432"  # PostgreSQL (zmień 5432 na 5433)
```

### Błąd połączenia z bazą danych

Upewnij się, że kontener bazy danych jest uruchomiony:

```bash
docker-compose ps
```

Sprawdź logi:

```bash
docker-compose logs db
```

### Frontend nie łączy się z backendem

Sprawdź, czy backend jest dostępny:

```bash
curl http://localhost:8000/health
```

### Rebuild po zmianach w kodzie

```bash
docker-compose up --build
```

## 📚 Dalszy rozwój

Ta aplikacja jest podstawą. Możesz ją rozbudować o:
- Resetowanie hasła
- Weryfikację emaila
- Role użytkowników
- Profile użytkowników
- Dodatkowe funkcjonalności biznesowe

## 📄 Licencja

Projekt jest szablonem do użytku wewnętrznego.
