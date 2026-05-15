import { useState } from 'react';
import Button from './Button';
import Badge from './Badge';

export default function BulkResultsModal({ results, onClose, onSavePassed }) {
  const [filteredResults, setFilteredResults] = useState(results);

  const removeEmail = (email) => {
    setFilteredResults(filteredResults.filter(r => r.email !== email));
  };

  const passedEmails = filteredResults.filter(r => r.passed);
  const failedEmails = filteredResults.filter(r => !r.passed);

  const handleSavePassed = () => {
    onSavePassed(passedEmails);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        <div className="p-6 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">Bulk Verification Results</h2>
            <p className="text-sm text-slate-600 mt-1">
              {passedEmails.length} passed, {failedEmails.length} failed
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 text-2xl leading-none"
          >
            ×
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="text-xs uppercase tracking-wide text-slate-500 border-b border-slate-200">
                  <th className="px-3 py-2 font-semibold">Email</th>
                  <th className="px-3 py-2 font-semibold">Name</th>
                  <th className="px-3 py-2 font-semibold">Score</th>
                  <th className="px-3 py-2 font-semibold">Status</th>
                  <th className="px-3 py-2 font-semibold">SMTP</th>
                  <th className="px-3 py-2 font-semibold">Issues</th>
                  <th className="px-3 py-2 font-semibold"></th>
                </tr>
              </thead>
              <tbody className="text-sm">
                {filteredResults.map((r, i) => (
                  <tr key={i} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="px-3 py-3">{r.email}</td>
                    <td className="px-3 py-3">{r.name || '-'}</td>
                    <td className="px-3 py-3">{r.score}/100</td>
                    <td className="px-3 py-3">
                      <Badge tone={r.passed ? "green" : "red"}>
                        {r.passed ? "PASS" : "FAIL"}
                      </Badge>
                    </td>
                    <td className="px-3 py-3">{r.smtp_status}</td>
                    <td className="px-3 py-3">
                      {[
                        r.disposable && "Disposable",
                        r.role && "Role",
                        r.catch_all && "Catch-All"
                      ].filter(Boolean).join(", ") || "-"}
                    </td>
                    <td className="px-3 py-3">
                      {!r.passed && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeEmail(r.email)}
                        >
                          Remove
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="p-6 border-t border-slate-200 flex justify-between items-center">
          <p className="text-sm text-slate-600">
            {passedEmails.length} email(s) ready to save
          </p>
          <div className="flex gap-3">
            <Button variant="secondary" onClick={onClose}>
              Close
            </Button>
            {passedEmails.length > 0 && (
              <Button onClick={handleSavePassed}>
                Save Passed Emails ({passedEmails.length})
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
