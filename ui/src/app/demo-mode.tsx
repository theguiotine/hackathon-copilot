// Demo mode (hand-written, not generated): VITE_DEMO_MEMORY=1 runs the whole app on the in-memory
// fixtures with a fixed Manager identity and no Archie backend or sign-in. Fictional data only.
import * as React from 'react';
import type { AuthPort } from '../domain/auth';
import type { AuthenticatedIdentity } from '../domain/session';
import { AuthProvider, IdentityProvider, RepositoriesProvider, type Repositories } from '../presentation/app-context';
import { createMemoryAccuracyMeasureRepository } from '../infrastructure/memory/accuracyMeasure.adapter';
import { createMemoryActiveSessionRepository } from '../infrastructure/memory/activeSession.adapter';
import { createMemoryCallLineRepository } from '../infrastructure/memory/callLine.adapter';
import { createMemoryChecklistItemRepository } from '../infrastructure/memory/checklistItem.adapter';
import { createMemoryCoachRepository } from '../infrastructure/memory/coach.adapter';
import { createMemoryCoachingCallRepository } from '../infrastructure/memory/coachingCall.adapter';
import { createMemoryCurrentUserRepository } from '../infrastructure/memory/currentUser.adapter';
import { createMemoryHumanReviewFlagRepository } from '../infrastructure/memory/humanReviewFlag.adapter';
import { createMemoryInvitationRepository } from '../infrastructure/memory/invitation.adapter';
import { createMemoryParticipantRepository } from '../infrastructure/memory/participant.adapter';
import { createMemoryRoleRepository } from '../infrastructure/memory/role.adapter';
import { createMemoryScorecardRepository } from '../infrastructure/memory/scorecard.adapter';
import { createMemoryTaskRepository } from '../infrastructure/memory/task.adapter';
import { createMemoryUserRepository } from '../infrastructure/memory/user.adapter';
import { createMemoryUserActivityRepository } from '../infrastructure/memory/userActivity.adapter';

export const DEMO_MEMORY = import.meta.env.VITE_DEMO_MEMORY === '1';

const DEMO_IDENTITY: AuthenticatedIdentity = {
  id: 'demo-manager',
  email: 'esteban.guio@example.com',
  roles: ['Manager'],
  firstName: 'Esteban',
  lastName: 'Guio',
};

const ok = async () => ({ ok: true as const, data: undefined });
const DEMO_AUTH: AuthPort = {
  signIn: ok, signUp: ok, signOut: ok, requestPasswordReset: ok, confirmPasswordReset: ok, verifyEmail: ok,
};

function createDemoRepositories(): Repositories {
  return {
    accuracyMeasure: createMemoryAccuracyMeasureRepository().repository,
    activeSession: createMemoryActiveSessionRepository().repository,
    callLine: createMemoryCallLineRepository().repository,
    checklistItem: createMemoryChecklistItemRepository().repository,
    coach: createMemoryCoachRepository().repository,
    coachingCall: createMemoryCoachingCallRepository().repository,
    currentUser: createMemoryCurrentUserRepository().repository,
    humanReviewFlag: createMemoryHumanReviewFlagRepository().repository,
    invitation: createMemoryInvitationRepository().repository,
    participant: createMemoryParticipantRepository().repository,
    role: createMemoryRoleRepository().repository,
    scorecard: createMemoryScorecardRepository().repository,
    task: createMemoryTaskRepository().repository,
    user: createMemoryUserRepository().repository,
    userActivity: createMemoryUserActivityRepository().repository,
  };
}

export function DemoAppProviders(props: { readonly children: React.ReactNode }): React.ReactElement {
  const repositories = React.useMemo(createDemoRepositories, []);
  return React.createElement(RepositoriesProvider, {
    repositories,
    children: React.createElement(AuthProvider, {
      auth: DEMO_AUTH,
      children: React.createElement(IdentityProvider, { identity: DEMO_IDENTITY, pending: false, children: props.children }),
    }),
  });
}

export function DemoAuthGuard(props: { readonly children?: React.ReactNode }): React.ReactElement {
  return React.createElement(React.Fragment, null, props.children);
}
