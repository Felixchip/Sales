import { useState, useEffect } from 'react';
import Section from '../components/Section';
import Button from '../components/Button';
import Table from '../components/Table';
import Badge from '../components/Badge';
import PersonalizationModal from '../components/PersonalizationModal';
import { useToast } from '../components/ToastContainer';
import { api } from '../api';

export default function Personalize() {
  const toast = useToast();
  const [activeTab, setActiveTab] = useState('signals');
  const [signals, setSignals] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [contactedSignals, setContactedSignals] = useState([]);
  const [selectedSignal, setSelectedSignal] = useState(null);
  const [loading, setLoading] = useState(false);
  const [email, setEmail] = useState('');
  const [generating, setGenerating] = useState(false);
  const [manualResult, setManualResult] = useState(null);
  const [showManualModal, setShowManualModal] = useState(false);

  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'signals') {
        const data = await api.getAllSignals(50);
        setSignals(data.signals || []);
      } else if (activeTab === 'templates') {
        const data = await api.getTemplates();
        setTemplates(data.templates || []);
      } else if (activeTab === 'contacted') {
        const data = await api.getContactedSignals(100);
        setContactedSignals(data.signals || []);
      }
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  };

  const openPersonalizationModal = (signal) => {
    setSelectedSignal(signal);
  };

  const closeModal = () => {
    setSelectedSignal(null);
    loadData(); // Refresh data after closing
  };

  const handleSignalContacted = (signalId) => {
    // Refresh data when signal is marked as contacted
    loadData();
  };

  const handleGenerateManual = async () => {
    if (!email.trim()) {
      toast.error('Please enter an email or domain');
      return;
    }

    setGenerating(true);
    setManualResult(null);

    try {
      const result = await api.personalizeFromEmail(email);
      setManualResult(result);
      setShowManualModal(true);
      toast.success('Personalization generated!');
      loadData(); // Refresh signals list
    } catch (err) {
      toast.error(err.message || 'Failed to generate personalization');
    } finally {
      setGenerating(false);
    }
  };

  const getScoreBadge = (score) => {
    if (score >= 75) return <Badge tone="green">{score}</Badge>;
    if (score >= 50) return <Badge tone="amber">{score}</Badge>;
    return <Badge tone="red">{score}</Badge>;
  };

  const tabs = [
    { id: 'signals', label: 'Signals', count: signals.length },
    { id: 'templates', label: 'Templates', count: templates.length },
    { id: 'contacted', label: 'Contacted', count: contactedSignals.length },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Personalize</h1>
        <p className="text-sm text-slate-600 mt-1">
          Signal-based automation for cold email personalization
        </p>
      </div>

      {/* Manual Personalization Form */}
      <Section title="Generate Personalization">
        <div className="space-y-4">
          <div className="flex gap-3">
            <input
              type="text"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter email or domain (e.g., sarah@linear.app or linear.app)"
              className="flex-1 px-4 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-slate-400"
              disabled={generating}
            />
            <Button
              onClick={handleGenerateManual}
              disabled={generating}
            >
              {generating ? 'Generating...' : 'Generate'}
            </Button>
          </div>
        </div>
      </Section>

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                pb-4 px-1 border-b-2 font-medium text-sm
                ${activeTab === tab.id
                  ? 'border-slate-900 text-slate-900'
                  : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
                }
              `}
            >
              {tab.label}
              {tab.count > 0 && (
                <span className="ml-2 py-0.5 px-2 rounded-full bg-slate-100 text-slate-600 text-xs">
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'signals' && (
        <Section title={`Signals (${signals.length})`}>
          {loading ? (
            <div className="py-8 text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div>
            </div>
          ) : signals.length === 0 ? (
            <p className="text-center text-slate-500 py-8">No signals yet. Signals will appear when you generate personalization.</p>
          ) : (
            <Table
              columns={[
                { key: "company", label: "Company" },
                { key: "type", label: "Type" },
                { key: "title", label: "Title" },
                { key: "score", label: "Score" },
                { key: "recency", label: "Age" },
                { key: "status", label: "Status" },
                { key: "actions", label: "" },
              ]}
              rows={signals.map(s => ({
                company: s.company,
                type: <Badge>{s.type}</Badge>,
                title: s.title.length > 50 ? s.title.substring(0, 50) + '...' : s.title,
                score: getScoreBadge(s.score),
                recency: `${s.recency_days}d`,
                status: s.contacted ? <Badge tone="green">Contacted</Badge> : '',
                actions: (
                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={() => openPersonalizationModal(s)}
                  >
                    Generate
                  </Button>
                )
              }))}
            />
          )}
        </Section>
      )}

      {activeTab === 'templates' && (
        <Section title={`Templates (${templates.length})`}>
          {loading ? (
            <div className="py-8 text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div>
            </div>
          ) : templates.length === 0 ? (
            <p className="text-center text-slate-500 py-8">No templates loaded</p>
          ) : (
            <Table
              columns={[
                { key: "name", label: "Name" },
                { key: "type", label: "Signal Type" },
                { key: "subject", label: "Subject" },
                { key: "fallback", label: "Fallback" },
              ]}
              rows={templates.map(t => ({
                name: t.name,
                type: t.signal_type || '-',
                subject: <div className="max-w-2xl break-words">{t.subject}</div>,
                fallback: t.is_fallback ? <Badge tone="amber">Yes</Badge> : '-'
              }))}
            />
          )}
        </Section>
      )}

      {activeTab === 'contacted' && (
        <Section title={`Contacted (${contactedSignals.length})`}>
          {loading ? (
            <div className="py-8 text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div>
            </div>
          ) : contactedSignals.length === 0 ? (
            <p className="text-center text-slate-500 py-8">No contacted signals yet. Mark signals as "Reached Out" to track them here.</p>
          ) : (
            <Table
              columns={[
                { key: "company", label: "Company" },
                { key: "type", label: "Type" },
                { key: "title", label: "Title" },
                { key: "contacted_at", label: "Contacted" },
              ]}
              rows={contactedSignals.map(s => ({
                company: s.company,
                type: <Badge>{s.type}</Badge>,
                title: s.title.length > 60 ? s.title.substring(0, 60) + '...' : s.title,
                contacted_at: s.contacted_at ? new Date(s.contacted_at).toLocaleDateString() : '-'
              }))}
            />
          )}
        </Section>
      )}

      {/* Personalization Modal (from signal list) */}
      {selectedSignal && (
        <PersonalizationModal
          signal={selectedSignal}
          onClose={closeModal}
          onContacted={handleSignalContacted}
        />
      )}

      {/* Manual Personalization Result Modal */}
      {showManualModal && manualResult && (
        <ManualResultModal
          result={manualResult}
          onClose={() => {
            setShowManualModal(false);
            setEmail('');
          }}
        />
      )}
    </div>
  );
}

function ManualResultModal({ result, onClose }) {
  const toast = useToast();

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h2 className="text-xl font-semibold text-slate-900">Generated Personalization</h2>
              <p className="text-sm text-slate-600">{result.domain}</p>
            </div>
            <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="space-y-4">
            {/* Subject */}
            <div className="p-4 bg-slate-50 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-slate-500">SUBJECT</span>
                <Button variant="ghost" size="sm" onClick={() => copyToClipboard(result.subject)}>
                  Copy
                </Button>
              </div>
              <p className="text-sm font-medium break-words">{result.subject}</p>
              <p className="text-xs text-slate-500 mt-1">{result.subject.length} chars</p>
            </div>

            {/* Opening */}
            <div className="p-4 bg-slate-50 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-slate-500">OPENING</span>
                <Button variant="ghost" size="sm" onClick={() => copyToClipboard(result.opening)}>
                  Copy
                </Button>
              </div>
              <p className="text-sm break-words">{result.opening}</p>
              <p className="text-xs text-slate-500 mt-1">{result.opening.length} chars</p>
            </div>

            {/* Insight */}
            {result.insight && (
              <div className="p-4 bg-slate-50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-slate-500">INSIGHT</span>
                  <Button variant="ghost" size="sm" onClick={() => copyToClipboard(result.insight)}>
                    Copy
                  </Button>
                </div>
                <p className="text-sm break-words">{result.insight}</p>
              </div>
            )}

            {/* Bridge */}
            {result.bridge && (
              <div className="p-4 bg-slate-50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-slate-500">ECHOTRAY BRIDGE</span>
                  <Button variant="ghost" size="sm" onClick={() => copyToClipboard(result.bridge)}>
                    Copy
                  </Button>
                </div>
                <p className="text-sm break-words">{result.bridge}</p>
              </div>
            )}

            {/* CTA */}
            {result.cta && (
              <div className="p-4 bg-slate-50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-slate-500">CALL TO ACTION</span>
                  <Button variant="ghost" size="sm" onClick={() => copyToClipboard(result.cta)}>
                    Copy
                  </Button>
                </div>
                <p className="text-sm break-words">{result.cta}</p>
              </div>
            )}

            {/* Complete Email */}
            {result.body && (
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-blue-700">COMPLETE EMAIL</span>
                  <Button variant="ghost" size="sm" onClick={() => copyToClipboard(result.body)}>
                    Copy All
                  </Button>
                </div>
                <p className="text-sm whitespace-pre-line break-words">{result.body}</p>
                <p className="text-xs text-blue-600 mt-2">{result.body.length} chars total</p>
              </div>
            )}

            <div className="text-xs text-slate-600">
              <p><strong>Template:</strong> {result.template_used}</p>
              {result.selection_reason && (
                <p className="mt-1"><strong>Selection:</strong> {result.selection_reason}</p>
              )}
            </div>

            <Button onClick={onClose} className="w-full">
              Close
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
