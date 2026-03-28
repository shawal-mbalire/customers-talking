import { createAuthClient } from '@neondatabase/neon-js/auth';
import { env } from '../env';

export const authClient = createAuthClient(env.neonAuthUrl);
