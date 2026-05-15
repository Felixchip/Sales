import { useState, useEffect } from 'react';
import Section from '../components/Section';
import Button from '../components/Button';
import Table from '../components/Table';
import Badge from '../components/Badge';
import BulkResultsModal from '../components/BulkResultsModal';
import PersonalizationResultsModal from '../components/PersonalizationResultsModal';
import { useToast } from '../components/ToastContainer';
import { useProduct } from '../contexts/ProductContext';
import { api } from '../api';

export default function Verify() {
  const toast = useToast();
  const { activeProduct } = useProduct();
  const [email, setEmail] = useState('');
  const [bulkEmails, setBulkEmails] = useState('');
  const [csvFile, setCsvFile] = useState(null);
  const [verifying, setVerifying] = useState(false);
  const [result, setResult] = useState(null);
  const [bulkResults, setBulkResults] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [savedEmails, setSavedEmails] = useState([]);
  const [history, setHistory] = useState([]);
  const [activeTab, setActiveTab] = useState('saved');
  const [personalizationResult, setPersonalizationResult] = useState(null);
  const [showPersonalizationModal, setShowPersonalizationModal] = useState(false);
  const [personalizing, setPersonalizing] = useState(false);

  useEffect(() => {
    loadSavedEmails();
    loadHistory();
  }, []);

  const verifyOne = async () => {
    if (!email.trim()) {
      toast.error('Please enter an email address');
      return;
    }

    setVerifying(true);
    try {
      const data = await api.verifyEmail(email.trim());
      setResult(data);
      toast.success(`Verified! Score: ${data.score}`);
      loadHistory();
    } catch (err) {
      toast.error(err.message || 'Verification failed');
    } finally {
      setVerifying(false);
    }
  };

  const saveCurrentEmail = async () => {
    if (!result || !result.passed) {
      toast.error('Only passed emails can be saved');
      return;
    }

    try {
      await api.saveEmail(result.email, result.score);
      toast.success('Email saved to list');
      loadSavedEmails();
    } catch (err) {
      toast.error(err.message || 'Failed to save email');
    }
  };

  const verifyBatch = async () => {
    const emails = bulkEmails.split('\n').map(e => e.trim()).filter(e => e);
    
    if (emails.length === 0) {
      toast.error('Please enter at least one email');
      return;
    }

    setVerifying(true);
    try {
      const data = await api.verifyBatch(emails);
      setBulkResults(data.results || []);
      setShowModal(true);
      toast.success(`Verified ${data.results?.length || 0} emails`);
      setBulkEmails('');
      loadHistory().catch(err => console.error('History load failed:', err));
    } catch (err) {
      toast.error(err.message || 'Batch verification failed');
    } finally {
      setVerifying(false);
    }
  };

  const verifyCSV = async () => {
    if (!csvFile) {
      toast.error('Please select a CSV file');
      return;
    }

    setVerifying(true);
    try {
      const data = await api.verifyBatchCSV(csvFile);
      setBulkResults(data.results || []);
      setShowModal(true);
      toast.success(`Verified ${data.results?.length || 0} emails from CSV`);
      setCsvFile(null);
      loadHistory().catch(err => console.error('History load failed:', err));
    } catch (err) {
      toast.error(err.message || 'CSV verification failed');
    } finally {
      setVerifying(false);
    }
  };

  const loadHistory = async () => {
    try {
      const data = await api.getVerificationHistory(50);
      setHistory(data.results || []);
    } catch (err) {
      console.error('Failed to load history:', err);
    }
  };

  const loadSavedEmails = async () => {
    try {
      const data = await api.getSavedEmails();
      setSavedEmails(data.results || []);
    } catch (err) {
      console.error('Failed to load saved emails:', err);
    }
  };

  const deleteSaved = async (email) => {
    try {
      await api.deleteSavedEmail(email);
      toast.success('Email removed');
      loadSavedEmails();
    } catch (err) {
      toast.error('Failed to remove email');
    }
  };

  const saveBulkPassedEmails = async (passedEmails) => {
    try {
      for (const email of passedEmails) {
        await api.saveEmail(email.email, email.score, email.name);
      }
      toast.success(`Saved ${passedEmails.length} email(s) to list`);
      setShowModal(false);
      loadSavedEmails();
    } catch (err) {
      toast.error(err.message || 'Failed to save emails');
    }
  };

  const exportSavedEmails = () => {
    const csv = savedEmails.map(e => `${e.email},${e.name || ''}`).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `verified-emails-${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const generatePersonalization = async (email, name) => {
    if (!activeProduct) {
      toast.error('No active product selected');
      return;
    }
    setPersonalizing(true);
    try {
      const data = await api.personalizeFromEmail(email, activeProduct.id, name);
      setPersonalizationResult(data);
      setShowPersonalizationModal(true);
      toast.success('Personalization generated!');
    } catch (err) {
      toast.error(err.message || 'Failed to generate personalization');
    } finally {
      setPersonalizing(false);
    }
  };

  const generateBulkPersonalizations = async () => {
    if (savedEmails.length === 0) {
      toast.error('No saved emails to personalize');
      return;
    }

    setPersonalizing(true);
    const results = [];
    let successCount = 0;
    let failCount = 0;

    try {
      for (const email of savedEmails) {
        try {
          const data = await api.personalizeFromEmail(email.email, activeProduct.id, email.name);
          results.push({ ...data, email: email.email, name: email.name });
          successCount++;
        } catch (err) {
          console.error(`Failed to personalize ${email.email}:`, err);
          failCount++;
        }
      }

      const csv = results.map(r => 
        `${r.email},${r.name || ''},${r.subject.replace(/,/g, ';')},${r.opening.replace(/,/g, ';').replace(/\n/g, ' ')}`
      ).join('\n');
      const header = 'email,name,subject,opening\n';
      const blob = new Blob([header + csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `personalizations-${Date.now()}.csv`;
      a.click();
      URL.revokeObjectURL(url);

      toast.success(`Generated ${successCount} personalizations! ${failCount > 0 ? `(${failCount} failed)` : ''}`);
    } catch (err) {
      toast.error(err.message || 'Bulk personalization failed');
    } finally {
      setPersonalizing(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Email Verification</h1>
        <p className="text-sm text-slate-600 mt-1">
          Verify email deliverability before sending
        </p>
        <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-xs text-blue-700">
            <strong>Note:</strong> SMTP verification may timeout for some providers (Gmail, Outlook) due to network restrictions. 
            Syntax, MX, and domain checks still provide valuable verification.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Section title="Single Email">
          <div className="space-y-4">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter email address"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
            />
            <Button onClick={verifyOne} disabled={verifying}>
              {verifying ? 'Verifying...' : 'Verify Email'}
            </Button>

            {result && (
              <div className="mt-4 p-4 bg-slate-50 rounded-lg space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-medium">Score: {result.score}/100</span>
                  <Badge tone={result.passed ? "green" : "red"}>
                    {result.passed ? "PASS" : "FAIL"}
                  </Badge>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>Syntax: {result.syntax ? '✓' : '✗'}</div>
                  <div>MX Records: {result.has_mx ? '✓' : '✗'}</div>
                  <div>SMTP Status: <span className={result.smtp_status === 'valid' ? 'text-green-600' : result.smtp_status === 'invalid' ? 'text-red-600' : 'text-amber-600'}>{result.smtp_status}</span></div>
                  <div>SMTP Code: {result.smtp_code || 'N/A'}</div>
                  <div>Disposable: {result.disposable ? 'Yes' : 'No'}</div>
                  <div>Role Address: {result.role ? 'Yes' : 'No'}</div>
                  <div>Catch-All: {result.catch_all ? 'Yes' : 'No'}</div>
                </div>
                {result.smtp_status === 'unknown' && result.smtp_code >= 400 && (
                  <div className="mt-2 text-xs text-amber-600">
                    ⚠️ SMTP connection issue (code {result.smtp_code}). Email may still be valid.
                  </div>
                )}
                {result.passed && (
                  <Button onClick={saveCurrentEmail} variant="secondary" size="sm">
                    Save to List
                  </Button>
                )}
              </div>
            )}
          </div>
        </Section>

        <Section title="Bulk Verification">
          <div className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">CSV File Upload</label>
              <input
                id="csv-upload"
                type="file"
                accept=".csv"
                onChange={(e) => setCsvFile(e.target.files[0])}
                className="hidden"
              />
              <div className="flex items-center gap-2">
                <button
                  onClick={() => document.getElementById('csv-upload').click()}
                  className="flex-1 px-3 py-2 border border-slate-300 rounded-lg text-sm text-slate-600 hover:bg-slate-50"
                >
                  {csvFile ? csvFile.name : 'Choose CSV file...'}
                </button>
                {csvFile && (
                  <Button onClick={verifyCSV} disabled={verifying} size="sm">
                    Verify
                  </Button>
                )}
              </div>
            </div>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-slate-300"></div>
              </div>
              <div className="relative flex justify-center text-xs">
                <span className="bg-white px-2 text-slate-500">OR</span>
              </div>
            </div>
            
            <textarea
              value={bulkEmails}
              onChange={(e) => setBulkEmails(e.target.value)}
              placeholder="Enter emails (one per line)"
              rows={6}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900 font-mono text-sm"
            />
            <Button onClick={verifyBatch} disabled={verifying} className="w-full">
              {verifying ? 'Verifying...' : 'Verify Batch'}
            </Button>
          </div>
        </Section>
      </div>

      <Section 
        title="Email Lists"
        action={
          <div className="flex gap-2">
            {activeTab === 'saved' && savedEmails.length > 0 && (
              <>
                <Button variant="ghost" size="sm" onClick={generateBulkPersonalizations} disabled={personalizing}>
                  {personalizing ? 'Generating...' : 'Personalize All'}
                </Button>
                <Button variant="ghost" size="sm" onClick={exportSavedEmails}>
                  Export CSV
                </Button>
              </>
            )}
            <Button variant="ghost" size="sm" onClick={() => {
              if (activeTab === 'saved') loadSavedEmails();
              else loadHistory();
            }}>
              Refresh
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          <div className="flex gap-2 border-b">
            <button 
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'saved' 
                  ? 'text-slate-900 border-slate-900' 
                  : 'text-slate-500 border-transparent hover:text-slate-700'
              }`}
              onClick={() => setActiveTab('saved')}
            >
              Saved Emails ({savedEmails.length})
            </button>
            <button 
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'history' 
                  ? 'text-slate-900 border-slate-900' 
                  : 'text-slate-500 border-transparent hover:text-slate-700'
              }`}
              onClick={() => setActiveTab('history')}
            >
              Recent Verifications ({history.length})
            </button>
          </div>

          {activeTab === 'saved' ? (
            savedEmails.length === 0 ? (
              <p className="text-center text-slate-500 py-8">No saved emails yet</p>
            ) : (
              <Table
                columns={[
                  { key: "email", label: "Email" },
                  { key: "name", label: "Name" },
                  { key: "score", label: "Score" },
                  { key: "actions", label: "" }
                ]}
                rows={savedEmails.map(e => ({
                  email: e.email,
                  name: e.name || '-',
                  score: `${e.score}/100`,
                  actions: (
                    <div className="flex gap-2">
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        onClick={() => generatePersonalization(e.email, e.name)}
                        disabled={personalizing}
                      >
                        Personalize
                      </Button>
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        onClick={() => deleteSaved(e.email)}
                      >
                        Remove
                      </Button>
                    </div>
                  )
                }))}
              />
            )
          ) : (
            history.length === 0 ? (
              <p className="text-center text-slate-500 py-8">No verification history yet</p>
            ) : (
              <Table
                columns={[
                  { key: "email", label: "Email" },
                  { key: "score", label: "Score" },
                  { key: "status", label: "Status" },
                  { key: "smtp_status", label: "SMTP" },
                  { key: "flags", label: "Flags" }
                ]}
                rows={history.map(h => ({
                  email: h.email,
                  score: `${h.score || 0}/100`,
                  status: (
                    <Badge tone={h.passed ? "green" : "red"}>
                      {h.passed ? "PASS" : "FAIL"}
                    </Badge>
                  ),
                  smtp_status: h.smtp_status || 'unknown',
                  flags: [
                    h.disposable && "Disposable",
                    h.role && "Role",
                    h.catch_all && "Catch-All"
                  ].filter(Boolean).join(", ") || "-"
                }))}
              />
            )
          )}
        </div>
      </Section>

      {showModal && (
        <BulkResultsModal
          results={bulkResults}
          onClose={() => setShowModal(false)}
          onSavePassed={saveBulkPassedEmails}
        />
      )}

      {showPersonalizationModal && (
        <PersonalizationResultsModal
          results={personalizationResult}
          onClose={() => setShowPersonalizationModal(false)}
        />
      )}
    </div>
  );
}
