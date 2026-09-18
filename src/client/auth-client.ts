import { createAuthClient } from "better-auth/react";

// Same origin as the page: Vite proxies /api to Express in dev.
export const authClient = createAuthClient();
