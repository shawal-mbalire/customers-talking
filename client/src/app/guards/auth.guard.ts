import { CanActivateFn } from '@angular/router';

// Auth stubbed out — all routes are publicly accessible
export const authGuard: CanActivateFn = () => true;
