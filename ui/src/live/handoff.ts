// "Copy hand-off note": a short English + Spanish note built only from fields already on the review page.
// Clipboard only: no network, no route, no backend. A draft for a human to review; nothing is sent.
import { DEMO_MEMORY } from '../app/demo-mode';

export type HandoffInput = {
  severity: 'S1' | 'S2' | 'S3';
  quote: string;
  coachReply: string | null; // next coach line, or null when the data says no reply yet
  decision: 'CONFIRMED' | 'ANNOTATED_WITH_A_NOTE' | 'DISMISSED_AS_FALSE_ALARMS';
  decisionLabel: string;
  reason: string | null;
};

const TIER_EN = { S1: 'S1, chest or breathing trouble', S2: 'S2, symptom', S3: 'S3, distress' } as const;
const TIER_ES = { S1: 'S1, dolor de pecho o dificultad para respirar', S2: 'S2, síntoma', S3: 'S3, angustia' } as const;
const LABEL_ES: Record<HandoffInput['decision'], string> = {
  CONFIRMED: 'Requiere seguimiento', ANNOTATED_WITH_A_NOTE: 'Ya atendido', DISMISSED_AS_FALSE_ALARMS: 'No es una alerta real',
};

export function reasonOf(decisionNote?: string): string | null {
  return /Reason:\s*(.+?)\.?$/.exec(decisionNote ?? '')?.[1] ?? null;
}

export function buildHandoff(h: HandoffInput): string {
  const escalate = h.decision === 'CONFIRMED';
  const demo = DEMO_MEMORY || import.meta.env.VITE_ENGINE_URL === '';
  return [
    'Hear Me Out hand-off (draft for a human to review; nothing was sent)',
    'Hear Me Out, nota de traspaso (borrador para que una persona la revise; no se envió nada)',
    '',
    'ENGLISH',
    `Participant said: "${h.quote}"`,
    `Flag: ${TIER_EN[h.severity]}`,
    `Coach reply next: ${h.coachReply ? `"${h.coachReply}"` : 'no coach reply yet'}`,
    `Reviewer decision: ${h.decisionLabel}${h.reason ? ` (reason: ${h.reason})` : ''}`,
    escalate ? 'Needs a nurse call-back today' : 'Review this week',
    '',
    'ESPAÑOL',
    `La persona dijo: "${h.quote}"`,
    `Alerta: ${TIER_ES[h.severity]}`,
    `Respuesta siguiente del coach: ${h.coachReply ? `"${h.coachReply}"` : 'todavía sin respuesta del coach'}`,
    `Decisión de quien revisa: ${LABEL_ES[h.decision]}${h.reason ? ` (motivo: ${h.reason})` : ''}`,
    escalate ? 'Requiere llamada de una enfermera hoy' : 'Revisar esta semana',
    ...(demo ? ['', 'Demo build: all people and calls are invented. / Versión de demostración: todas las personas y llamadas son inventadas.'] : []),
  ].join('\n');
}
