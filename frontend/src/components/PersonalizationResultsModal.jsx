import { useState } from 'react';
import Badge from './Badge';

export default function PersonalizationResultsModal({ results, onClose }) {
  const [copied, setCopied] = useState(null);

  const copyToClipboard = (text, field) => {
    navigator.clipboard.writeText(text);
    setCopied(field);
    setTimeout(() => setCopied(null), 2000);
  };

  if (!results) return null;

  const validation = results.validation || {};
  const hasIssues = validation.issues && validation.issues.length > 0;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">Email Personalization</h2>
            <p className="text-sm text-slate-600 mt-1">{results.email}</p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 text-2xl leading-none"
          >
            ×
          </button>
        </div>

        <div className="p-6 space-y-6">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-slate-700">Subject Line</label>
              <button
                onClick={() => copyToClipboard(results.subject, 'subject')}
                className="text-xs text-slate-600 hover:text-slate-900 font-medium"
              >
                {copied === 'subject' ? '✓ Copied!' : 'Copy'}
              </button>
            </div>
            <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
              <p className="text-slate-900">{results.subject}</p>
            </div>
            {validation.subject_length && (
              <p className="text-xs text-slate-500">
                {validation.subject_length} characters
                {validation.subject_length >= 36 && validation.subject_length <= 54 ? (
                  <Badge tone="green" className="ml-2">Optimal</Badge>
                ) : validation.subject_length < 36 ? (
                  <Badge tone="yellow" className="ml-2">Too Short</Badge>
                ) : (
                  <Badge tone="yellow" className="ml-2">Too Long</Badge>
                )}
              </p>
            )}
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-slate-700">Opening</label>
              <button
                onClick={() => copyToClipboard(results.opening, 'opening')}
                className="text-xs text-slate-600 hover:text-slate-900 font-medium"
              >
                {copied === 'opening' ? '✓ Copied!' : 'Copy'}
              </button>
            </div>
            <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
              <p className="text-slate-900 whitespace-pre-wrap">{results.opening}</p>
            </div>
            {validation.opening_length && (
              <p className="text-xs text-slate-500">
                {validation.opening_length} characters
                {validation.opening_length <= 220 ? (
                  <Badge tone="green" className="ml-2">Good</Badge>
                ) : (
                  <Badge tone="yellow" className="ml-2">Too Long</Badge>
                )}
              </p>
            )}
          </div>

          <div className="space-y-3">
            <label className="text-sm font-medium text-slate-700">Signal Used</label>
            <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
              <p className="text-sm text-blue-900 font-medium">{results.signal?.type || 'fallback'}</p>
              <p className="text-sm text-blue-700 mt-1">{results.signal?.title || 'No recent signals - using fallback template'}</p>
              {results.signal?.score !== undefined && (
                <p className="text-xs text-blue-600 mt-2">Score: {results.signal.score}/100</p>
              )}
            </div>
          </div>

          {hasIssues && (
            <div className="space-y-3">
              <label className="text-sm font-medium text-slate-700">Quality Issues</label>
              <div className="p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                <ul className="text-sm text-yellow-800 space-y-1">
                  {validation.issues.map((issue, idx) => (
                    <li key={idx}>• {issue}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="p-3 bg-slate-50 rounded-lg">
              <p className="text-slate-600">Domain</p>
              <p className="text-slate-900 font-medium">{results.domain}</p>
            </div>
            <div className="p-3 bg-slate-50 rounded-lg">
              <p className="text-slate-600">Template</p>
              <p className="text-slate-900 font-medium">{results.template_used || 'fallback'}</p>
            </div>
          </div>
        </div>

        <div className="p-6 border-t border-slate-200 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
