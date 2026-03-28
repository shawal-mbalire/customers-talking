import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

import { HlmCardImports } from '@spartan-ng/helm/card';
import { HlmBadgeImports } from '@spartan-ng/helm/badge';
import { HlmButton } from '@spartan-ng/helm/button';
import { HlmSeparatorImports } from '@spartan-ng/helm/separator';

const JOURNEY = [
  {
    step: '1',
    icon: '📟',
    title: 'USSD First Contact',
    body: 'Customer dials *384#. No internet needed. Works on any handset across Africa.',
  },
  {
    step: '2',
    icon: '🤖',
    title: 'AI Resolves or Escalates',
    body: 'Dialogflow CX detects intent. Predefined answers reply instantly. Complex issues trigger a live-agent handoff.',
  },
  {
    step: '3',
    icon: '📞',
    title: 'Voice / SMS for Complex Issues',
    body: 'The customer receives an SMS or a voice callback. Context travels with them — no need to repeat themselves.',
  },
];

const CHANNELS = [
  {
    icon: '📟',
    title: 'USSD',
    code: '*384#',
    description: 'Dial from any mobile phone — no internet required. Works on 2G and feature phones.',
    steps: ['Dial *384#', 'Choose your issue from the menu', 'Follow the prompts', 'Get instant help'],
  },
  {
    icon: '💬',
    title: 'SMS',
    code: '20880',
    description: 'Text our shortcode. AI reads your message, classifies intent, and replies within seconds.',
    steps: ['Text your question to 20880', 'Receive an automated reply', 'Reply to continue the conversation'],
  },
  {
    icon: '📞',
    title: 'Voice',
    code: '0800 123 456',
    description: 'Call our toll-free line. An AI voice agent guides you with DTMF prompts.',
    steps: ['Call 0800 123 456 (toll-free)', 'Follow voice prompts', 'Press keys to navigate'],
  },
];

const HOW_IT_WORKS = [
  { icon: '🔍', title: 'Intent Detection', body: 'Every message is passed through Dialogflow CX to identify what the customer needs.' },
  { icon: '⚡', title: 'Predefined Solutions', body: 'Common questions are answered instantly from a curated knowledge base — no AI round-trip.' },
  { icon: '🧑‍💼', title: 'Human Handoff', body: 'When the AI can\'t resolve the issue, a live-agent handoff fires. The agent dashboard lights up.' },
  { icon: '🔗', title: 'Cross-Channel Context', body: 'Sessions are tracked by phone number. Start on USSD, continue via SMS — no repetition.' },
];

@Component({
  selector: 'app-landing',
  imports: [RouterLink, ...HlmCardImports, ...HlmBadgeImports, HlmButton, ...HlmSeparatorImports],
  templateUrl: './landing.html',
})
export class LandingComponent {
  journey = JOURNEY;
  channels = CHANNELS;
  howItWorks = HOW_IT_WORKS;
}
