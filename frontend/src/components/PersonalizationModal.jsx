import { useState, useEffect } from 'react';
import Button from './Button';
import Badge from './Badge';
import { useToast } from './ToastContainer';
import { useProduct } from '../contexts/ProductContext';
import { api } from '../api';

export default function PersonalizationModal({ signal, onClose, onContacted }) {
  const toast = useToast();
  const { activeProduct } = useProduct();
  const [generating, setGenerating] = useState(false);
  const [personalization, setPersonalization] = useState(null);
  const [marking, setMarking] = useState(false);

  const generatePersonalization = async () => {
    if (!activeProduct) return;
    setGenerating(true);
    try {
      // Use the SPECIFIC signal that was clicked (pinned mode)
      const email = `contact@${signal.domain}`;
      const data = await api.personalizeFromEmail(email, activeProduct.id, 'there', signal.id);
      setPersonalization(data);
      toast.success('Personalization generated!');
    } catch (err) {
      toast.error(err.message || 'Generation failed');
    } finally {
      setGenerating(false);
    }
  };

  const markAsContacted = async () => {
    setMarking(true);
    try {
      await api.markSignalContacted(signal.id);
      toast.success('Marked as contacted!');
      if (onContacted) {
        onContacted(signal.id);
      }
      setTimeout(() => onClose(), 500);
    } catch (err) {
      toast.error(err.message || 'Failed to mark as contacted');
    } finally {
      setMarking(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  };

  // Auto-generate on mount
  useState(() => {
    generatePersonalization();
  }, []);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="p-6">
          {/* Header */}
          <div className="flex items-start justify-between mb-4">
            <div>
              <h2 className="text-xl font-semibold text-slate-900">{signal.company}</h2>
              <p className="text-sm text-slate-600">{signal.domain}</p>
            </div>
            <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Signal Source */}
          <div className="mb-6 p-4 bg-slate-50 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-slate-500 uppercase">Signal Source</span>
              <Badge>{signal.type}</Badge>
            </div>
            <h3 className="font-medium text-slate-900 mb-1">{signal.title}</h3>
            <p className="text-sm text-slate-600 mb-2">{signal.summary?.substring(0, 150)}{signal.summary?.length > 150 ? '...' : ''}</p>
            <a href={signal.url} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-600 hover:text-blue-800 hover:underline">
              View source →
            </a>
            <div className="mt-2 flex gap-2 text-xs text-slate-500">
              <span>Score: {signal.score}</span>
              <span>•</span>
              <span>{signal.recency_days}d ago</span>
              <span>•</span>
              <span>Magnitude: {signal.magnitude}</span>
            </div>
          </div>

          {/* Personalization Output */}
          {generating ? (
            <div className="py-8 text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div>
              <p className="mt-2 text-slate-600">Generating personalization...</p>
            </div>
          ) : personalization ? (
            <div className="space-y-4">
              {/* Subject */}
              <div className="p-4 bg-slate-50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-slate-500">SUBJECT</span>
                  <Button variant="ghost" size="sm" onClick={() => copyToClipboard(personalization.subject)}>
                    Copy
                  </Button>
                </div>
                <p className="text-sm font-medium break-words">{personalization.subject}</p>
                <p className="text-xs text-slate-500 mt-1">{personalization.subject.length} chars</p>
              </div>

              {/* Opening */}
              <div className="p-4 bg-slate-50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-slate-500">OPENING</span>
                  <Button variant="ghost" size="sm" onClick={() => copyToClipboard(personalization.opening)}>
                    Copy
                  </Button>
                </div>
                <p className="text-sm break-words">{personalization.opening}</p>
                <p className="text-xs text-slate-500 mt-1">{personalization.opening.length} chars</p>
              </div>

              {/* Insight Paragraph */}
              {personalization.insight && (
                <div className="p-4 bg-slate-50 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-slate-500">INSIGHT</span>
                    <Button variant="ghost" size="sm" onClick={() => copyToClipboard(personalization.insight)}>
                      Copy
                    </Button>
                  </div>
                  <p className="text-sm break-words">{personalization.insight}</p>
                </div>
              )}

              {/* Bridge Paragraph */}
              {personalization.bridge && (
                <div className="p-4 bg-slate-50 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-slate-500">{activeProduct?.name.toUpperCase()} BRIDGE</span>
                    <Button variant="ghost" size="sm" onClick={() => copyToClipboard(personalization.bridge)}>
                      Copy
                    </Button>
                  </div>
                  <p className="text-sm break-words">{personalization.bridge}</p>
                </div>
              )}

              {/* CTA */}
              {personalization.cta && (
                <div className="p-4 bg-slate-50 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-slate-500">CALL TO ACTION</span>
                    <Button variant="ghost" size="sm" onClick={() => copyToClipboard(personalization.cta)}>
                      Copy
                    </Button>
                  </div>
                  <p className="text-sm break-words">{personalization.cta}</p>
                </div>
              )}

              {/* Full Email Body */}
              {personalization.body && (
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-blue-700">COMPLETE EMAIL</span>
                    <Button variant="ghost" size="sm" onClick={() => copyToClipboard(personalization.body)}>
                      Copy All
                    </Button>
                  </div>
                  <p className="text-sm whitespace-pre-line break-words">{personalization.body}</p>
                  <p className="text-xs text-blue-600 mt-2">{personalization.body.length} chars total</p>
                </div>
              )}

              {/* Template Used */}
              <div className="text-xs text-slate-600">
                <p><strong>Template:</strong> {personalization.template_used}</p>
              </div>

              {/* Actions */}
              <div className="flex gap-3 pt-4">
                <Button onClick={markAsContacted} disabled={marking} className="flex-1">
                  {marking ? 'Marking...' : 'Reached Out'}
                </Button>
                <Button variant="outline" onClick={onClose} className="flex-1">
                  Close
                </Button>
              </div>
            </div>
          ) : (
            <div className="py-8 text-center text-slate-500">
              <p>Failed to generate personalization</p>
              <Button onClick={generatePersonalization} className="mt-4">
                Retry
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
