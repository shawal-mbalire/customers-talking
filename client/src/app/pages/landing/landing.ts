import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../services/auth.service';

import { HlmCardImports } from '@spartan-ng/helm/card';
import { HlmBadgeImports } from '@spartan-ng/helm/badge';
import { HlmButton } from '@spartan-ng/helm/button';
import { HlmSeparatorImports } from '@spartan-ng/helm/separator';

const STATS = [
  { value: '70%', label: 'queries resolved without a human agent' },
  { value: '< 2 s', label: 'average AI response time' },
  { value: '3 channels', label: 'USSD · SMS · Voice in one platform' },
  { value: '24 / 7', label: 'availability — no shift schedules needed' },
];

const PROBLEMS = [
  {
    problem: 'Customers can\'t reach you',
    solution: 'USSD works on every mobile network, every handset — no smartphone or data required.',
  },
  {
    problem: 'Support costs keep rising',
    solution: 'AI triages and resolves common queries instantly. Human agents only handle what truly needs them.',
  },
  {
    problem: 'Agents repeat the same answers',
    solution: 'A curated knowledge base answers FAQs across every channel in real time.',
  },
  {
    problem: 'Customers repeat themselves',
    solution: 'Sessions are tracked by phone number. Context flows from USSD to SMS to Voice automatically.',
  },
  {
    problem: 'No visibility into support quality',
    solution: 'A live dashboard shows every session, satisfaction signal, and escalation the moment it happens.',
  },
  {
    problem: 'Escalations get lost',
    solution: 'When the AI can\'t help, a structured handoff alerts your team with the full conversation history.',
  },
];

const FEATURES = [
  {
    title: 'Omnichannel reach',
    body: 'USSD reaches feature phones with zero data. SMS and Voice meet customers exactly where they are. One platform manages all three.',
  },
  {
    title: 'AI-first triage',
    body: 'Dialogflow CX classifies intent in milliseconds. Predefined answers fire instantly. Uncommon queries escalate cleanly.',
  },
  {
    title: 'Structured human handoff',
    body: 'When AI can\'t resolve an issue, your team gets an alert with the full conversation — no cold transfers, no lost context.',
  },
  {
    title: 'Satisfaction loops built in',
    body: 'After every AI response, the platform asks if the customer is satisfied. A "No" auto-escalates before they give up.',
  },
  {
    title: 'Real-time dashboard',
    body: 'Monitor live sessions, filter by channel or status, resolve escalations, and manage your knowledge base — all in one view.',
  },
  {
    title: 'Instant knowledge base',
    body: 'Add predefined answers that fire before Dialogflow is even called. Update them live without redeployment.',
  },
];

const HOW = [
  { step: '01', title: 'Customer contacts you', body: 'Via USSD (*384#), SMS (shortcode), or a toll-free voice line. No app required.' },
  { step: '02', title: 'AI resolves or routes', body: 'Intent is detected. Common answers fire instantly. Complex issues are queued for a human with full context.' },
  { step: '03', title: 'Agent takes over seamlessly', body: 'Your team sees the entire conversation history and picks up exactly where the AI left off.' },
  { step: '04', title: 'You measure and improve', body: 'Every interaction is logged. Track resolution rates, satisfaction scores, and channel usage in real time.' },
];

const CHANNELS = [
  {
    label: 'USSD',
    code: '*384#',
    description: 'Works on any mobile phone — no internet or smartphone required.',
    steps: ['Dial *384#', 'Select your query from the menu', 'Get an instant AI response'],
  },
  {
    label: 'SMS',
    code: 'Shortcode',
    description: 'Send a message any time. AI replies in seconds.',
    steps: ['Text your question to the shortcode', 'Receive an AI-powered reply', 'Reply to continue the conversation'],
  },
  {
    label: 'Voice',
    code: 'Toll-free',
    description: 'Call the toll-free line and speak naturally — AI understands.',
    steps: ['Call the toll-free number', 'State your issue verbally', 'AI responds or connects you to an agent'],
  },
];

@Component({
  selector: 'app-landing',
  imports: [RouterLink, ...HlmCardImports, ...HlmBadgeImports, HlmButton, ...HlmSeparatorImports],
  templateUrl: './landing.html',
})
export class LandingComponent {
  auth = inject(AuthService);
  stats = STATS;
  problems = PROBLEMS;
  features = FEATURES;
  how = HOW;
  // aliases matching the template
  journey = HOW;
  channels = CHANNELS;
  howItWorks = FEATURES;
}
