import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { authAPI, rejestrioAPI, tokenManager } from '../api';
import LanguageSwitcher from './LanguageSwitcher';

function parseKrsList(value) {
    return [...new Set(
        value
            .split(/[\s,;]+/)
            .map((item) => item.trim())
            .filter(Boolean)
    )];
}

function Dashboard() {
    const { t } = useTranslation();
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [activeTab, setActiveTab] = useState('rejestrio');
    const [settingsApiKey, setSettingsApiKey] = useState('');
    const [settingsSaved, setSettingsSaved] = useState(false);
    const [settingsHasApiKey, setSettingsHasApiKey] = useState(false);
    const [settingsLoading, setSettingsLoading] = useState(false);
    const [settingsError, setSettingsError] = useState('');
    const [krs, setKrs] = useState('');
    const [fetchLoading, setFetchLoading] = useState(false);
    const [fetchError, setFetchError] = useState('');
    const [resultJson, setResultJson] = useState('');
    const [savedOrganizations, setSavedOrganizations] = useState([]);
    const [savedOrganizationsLoading, setSavedOrganizationsLoading] = useState(false);
    const [savedOrganizationsError, setSavedOrganizationsError] = useState('');
    const navigate = useNavigate();

    useEffect(() => {
        const fetchInitialData = async () => {
            try {
                const [userData, settingsData] = await Promise.all([
                    authAPI.getCurrentUser(),
                    rejestrioAPI.getSettings(),
                ]);
                setUser(userData);
                setSettingsHasApiKey(settingsData.hasApiKey);
            } catch (err) {
                setError(t('dashboard.errorLoading'));
                tokenManager.removeToken();
                navigate('/login');
            } finally {
                setLoading(false);
            }
        };

        if (tokenManager.isAuthenticated()) {
            fetchInitialData();
        } else {
            navigate('/login');
        }
    }, [navigate, t]);

    const handleLogout = () => {
        tokenManager.removeToken();
        navigate('/login');
    };

    const handleSaveSettings = async (e) => {
        e.preventDefault();
        setSettingsError('');
        setSettingsSaved(false);
        setSettingsLoading(true);

        try {
            const response = await rejestrioAPI.saveSettings(settingsApiKey);
            setSettingsApiKey('');
            setSettingsHasApiKey(response.hasApiKey);
            setSettingsSaved(true);
        } catch (err) {
            setSettingsError(err.response?.data?.detail || 'Nie udało się zapisać klucza API.');
        } finally {
            setSettingsLoading(false);
        }
    };

    const handleFetch = async (mode) => {
        setFetchError('');
        setResultJson('');

        const krsList = parseKrsList(krs);

        if (krsList.length === 0) {
            setFetchError('Podaj co najmniej jeden numer KRS.');
            return;
        }

        const invalidKrs = krsList.find((item) => !/^\d{1,10}$/.test(item));
        if (invalidKrs) {
            setFetchError(`Nieprawidłowy numer KRS: ${invalidKrs}. Każdy KRS musi zawierać od 1 do 10 cyfr.`);
            return;
        }

        if (mode === 'financial-document' && krsList.length > 1) {
            setFetchError('Dokument finansowy można pobrać tylko dla jednego numeru KRS naraz.');
            return;
        }

        setFetchLoading(true);

        try {
            if (mode === 'financial-document') {
                const response = await rejestrioAPI.fetchFinancialDocument(krsList[0]);
                setResultJson(JSON.stringify(response, null, 2));
            } else {
                const responses = [];

                for (const singleKrs of krsList) {
                    const response = await rejestrioAPI.fetchCompany(singleKrs);
                    responses.push(response);
                }

                setResultJson(JSON.stringify(responses, null, 2));
            }
        } catch (err) {
            const detail = err.response?.data?.detail;
            if (typeof detail === 'string') {
                setFetchError(detail);
            } else if (detail) {
                setFetchError(JSON.stringify(detail, null, 2));
            } else {
                setFetchError('Nie udało się pobrać danych z Rejestr.io.');
            }
        } finally {
            setFetchLoading(false);
        }
    };

    const handleFetchCompany = async (e) => {
        e.preventDefault();
        await handleFetch('company');
    };

    const handleFetchFinancialDocument = async (e) => {
        e.preventDefault();
        await handleFetch('financial-document');
    };

    const handleLoadSavedOrganizations = async () => {
        setSavedOrganizationsError('');
        setSavedOrganizationsLoading(true);

        try {
            const response = await rejestrioAPI.getSavedOrganizations();
            setSavedOrganizations(response);
        } catch (err) {
            setSavedOrganizationsError('Nie udało się pobrać zapisanych organizacji z bazy.');
        } finally {
            setSavedOrganizationsLoading(false);
        }
    };

    const handleExportCsv = async () => {
        try {
            const token = tokenManager.getToken();
            const response = await fetch(rejestrioAPI.getSavedOrganizationsCsvUrl(), {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });

            if (!response.ok) {
                throw new Error('Export failed');
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = 'advox_krs_organizations.csv';
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);
        } catch (err) {
            setSavedOrganizationsError('Nie udało się wyeksportować CSV.');
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
                    <p className="mt-4 text-slate-600">{t('loading')}</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen flex items-center justify-center px-4">
                <div className="card max-w-md w-full text-center">
                    <p className="text-red-600">{error}</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
            <div className="absolute top-4 right-4">
                <LanguageSwitcher />
            </div>

            <div className="p-8">
                <div className="max-w-5xl mx-auto">
                    <div className="card space-y-8">
                        <div className="flex justify-between items-start gap-4">
                            <div>
                                <h1 className="text-3xl font-bold text-slate-800 mb-2">{t('dashboard.title')}</h1>
                                <p className="text-slate-600">{t('dashboard.subtitle')}</p>
                                {user && (
                                    <p className="text-sm text-slate-500 mt-2">
                                        {user.username} ({user.email})
                                    </p>
                                )}
                            </div>
                            <button onClick={handleLogout} className="btn-secondary">
                                {t('logout')}
                            </button>
                        </div>

                        <div className="flex gap-3 border-b border-slate-200 pb-4">
                            <button
                                type="button"
                                onClick={() => setActiveTab('rejestrio')}
                                className={activeTab === 'rejestrio' ? 'btn-primary' : 'btn-secondary'}
                            >
                                Rejestr.io
                            </button>
                            <button
                                type="button"
                                onClick={() => setActiveTab('settings')}
                                className={activeTab === 'settings' ? 'btn-primary' : 'btn-secondary'}
                            >
                                Ustawienia
                            </button>
                        </div>

                        {activeTab === 'rejestrio' && (
                            <div className="space-y-6">
                                <div>
                                    <h2 className="text-xl font-semibold text-slate-800">Pobieranie danych z Rejestr.io</h2>
                                    <p className="text-slate-600 mt-1">
                                        Wpisz jeden lub wiele numerów KRS. Możesz rozdzielać je przecinkiem, spacją, średnikiem albo nową linią.
                                    </p>
                                </div>

                                <form onSubmit={handleFetchCompany} className="space-y-4">
                                    <div>
                                        <label htmlFor="krs" className="block text-sm font-medium text-slate-700 mb-2">
                                            KRS / lista KRS
                                        </label>
                                        <textarea
                                            id="krs"
                                            name="krs"
                                            inputMode="numeric"
                                            value={krs}
                                            onChange={(e) => setKrs(e.target.value.replace(/[^\d,\s;\n\r]/g, ''))}
                                            className="input-field min-h-[120px]"
                                            placeholder={'0000123456,\n0000925551,\n5212345678'}
                                            required
                                        />
                                        <p className="mt-2 text-sm text-slate-500">
                                            Przykład: 0000123456, 0000925551 albo każdy numer w nowej linii.
                                        </p>
                                        <p className="text-sm text-slate-500">
                                            Pobieranie danych organizacji obsługuje wiele KRS naraz. Dokument finansowy działa dla jednego KRS.
                                        </p>
                                    </div>

                                    <div className="flex items-center gap-4">
                                        <button type="submit" disabled={fetchLoading} className="btn-primary">
                                            {fetchLoading ? 'Pobieranie...' : 'Pobierz dane organizacji'}
                                        </button>
                                        <button
                                            type="button"
                                            onClick={handleFetchFinancialDocument}
                                            disabled={fetchLoading}
                                            className="btn-secondary"
                                        >
                                            {fetchLoading ? 'Pobieranie...' : 'Pobierz dokument finansowy'}
                                        </button>
                                        <button
                                            type="button"
                                            onClick={handleLoadSavedOrganizations}
                                            disabled={savedOrganizationsLoading}
                                            className="btn-secondary"
                                        >
                                            {savedOrganizationsLoading ? 'Ładowanie...' : 'Pokaż zapisane w bazie'}
                                        </button>
                                        <button
                                            type="button"
                                            onClick={handleExportCsv}
                                            className="btn-secondary"
                                        >
                                            Export CSV
                                        </button>
                                        {!settingsHasApiKey && (
                                            <span className="text-sm text-amber-700">
                                                Najpierw zapisz klucz API w zakładce Ustawienia.
                                            </span>
                                        )}
                                    </div>
                                </form>

                                {fetchError && (
                                    <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg whitespace-pre-wrap">
                                        {fetchError}
                                    </div>
                                )}

                                {savedOrganizationsError && (
                                    <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                                        {savedOrganizationsError}
                                    </div>
                                )}

                                {savedOrganizations.length > 0 && (
                                    <div className="space-y-3">
                                        <label className="block text-sm font-medium text-slate-700">
                                            Zapisane organizacje w bazie
                                        </label>
                                        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
                                            <table className="min-w-full text-sm text-slate-700">
                                                <thead className="bg-slate-100">
                                                    <tr>
                                                        {Object.keys(savedOrganizations[0]).map((column) => (
                                                            <th key={column} className="border-b border-slate-200 px-3 py-2 text-left font-semibold whitespace-nowrap">
                                                                {column}
                                                            </th>
                                                        ))}
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {savedOrganizations.map((organization) => (
                                                        <tr key={organization.id} className="odd:bg-white even:bg-slate-50">
                                                            {Object.keys(savedOrganizations[0]).map((column) => (
                                                                <td key={`${organization.id}-${column}`} className="border-b border-slate-100 px-3 py-2 align-top whitespace-pre-wrap min-w-[160px]">
                                                                    {organization[column] === null ? '' : String(organization[column])}
                                                                </td>
                                                            ))}
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                )}

                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-2">
                                        JSON
                                    </label>
                                    <pre className="bg-slate-950 text-slate-100 rounded-lg p-4 overflow-x-auto min-h-[240px] text-sm">
{resultJson || '{\n  "status": "Brak danych"\n}'}
                                    </pre>
                                </div>
                            </div>
                        )}

                        {activeTab === 'settings' && (
                            <div className="space-y-6">
                                <div>
                                    <h2 className="text-xl font-semibold text-slate-800">Ustawienia</h2>
                                    <p className="text-slate-600 mt-1">
                                        Zapisz klucz API Rejestr.io po stronie backendu.
                                    </p>
                                </div>

                                <div className="bg-slate-50 border border-slate-200 rounded-lg px-4 py-3 text-sm text-slate-700">
                                    Zapisany klucz API: {settingsHasApiKey ? 'tak' : 'nie'}
                                </div>

                                <form onSubmit={handleSaveSettings} className="space-y-4">
                                    <div>
                                        <label htmlFor="rejestrioApiKey" className="block text-sm font-medium text-slate-700 mb-2">
                                            Klucz API Rejestr.io
                                        </label>
                                        <input
                                            id="rejestrioApiKey"
                                            name="rejestrioApiKey"
                                            type="password"
                                            value={settingsApiKey}
                                            onChange={(e) => {
                                                setSettingsApiKey(e.target.value);
                                                setSettingsSaved(false);
                                                setSettingsError('');
                                            }}
                                            className="input-field"
                                            placeholder="Wpisz klucz API"
                                            required
                                        />
                                    </div>

                                    <button type="submit" disabled={settingsLoading} className="btn-primary">
                                        {settingsLoading ? 'Zapisywanie...' : 'Zapisz'}
                                    </button>
                                </form>

                                {settingsSaved && (
                                    <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg">
                                        Klucz API został zapisany.
                                    </div>
                                )}

                                {settingsError && (
                                    <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                                        {settingsError}
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Dashboard;
