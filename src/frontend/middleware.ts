import { clerkMiddleware } from '@clerk/nextjs/server';

// Expose `/api/webhooks` so Svix/Clerk can post without auth
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-expect-error - older Clerk types may not include `publicRoutes`, but runtime supports it
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export default clerkMiddleware((auth, req) => {
  // No custom auth handling needed here
}, {
  publicRoutes: ['/api/webhooks(.*)'],
});

export const config = {
  matcher: [
    // Skip Next.js internals and all static files, unless found in search params
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    // Always run for API routes
    '/(api|trpc)(.*)',
  ],
};