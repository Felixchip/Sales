import Section from '../components/Section';

export default function Settings() {
  const items = [
    { k: "Timezone", v: "America/New_York" },
    { k: "Primary windows", v: "09:15, 12:40 (ET)" },
    { k: "Max posts/day", v: "2" },
    { k: "Relevance threshold", v: "0.62" },
    { k: "Auto-publish threshold", v: "0.74" },
  ];

  return (
    <div>
      <Section title="Runtime settings">
        <ul className="grid grid-cols-1 gap-3 md:grid-cols-2">
          {items.map((i) => (
            <li
              key={i.k}
              className="flex items-center justify-between rounded-xl border border-slate-200 bg-white px-4 py-3"
            >
              <span className="text-slate-600">{i.k}</span>
              <span className="font-medium text-slate-900">{i.v}</span>
            </li>
          ))}
        </ul>
      </Section>

      <Section title="Safety & brand guardrails">
        <ul className="list-disc space-y-2 pl-5 text-sm text-slate-700">
          <li>Hard filters: politics, health claims, personal attacks.</li>
          <li>Tone: confident, direct, practical; 2–4 precise hashtags.</li>
          <li>Approval: auto-publish when relevance ≥ 0.74; else queue.</li>
        </ul>
      </Section>

      <Section title="EchoTray content pillars">
        <ul className="list-disc space-y-2 pl-5 text-sm text-slate-700">
          <li><strong>OOO:</strong> Out-of-office, handoffs, coverage, catch-up</li>
          <li><strong>Meetings:</strong> Meeting summaries, decisions, action items</li>
          <li><strong>Priority:</strong> Signal vs noise, focus time, triage</li>
          <li><strong>Enterprise:</strong> Slack, Teams, Google, Microsoft; SSO, SOC2</li>
        </ul>
      </Section>
    </div>
  );
}
