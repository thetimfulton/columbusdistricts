// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// https://astro.build/config
// Cloudflare Pages target: served from the domain root (no subpath).
export default defineConfig({
  site: 'https://www.columbusdistricts.com',
  base: '/',
  trailingSlash: 'always',
  integrations: [
    // Emits sitemap-index.xml + sitemap-0.xml at build time (uses `site` above).
    // Exclude the 404 page — it should never be an indexable/crawlable URL.
    sitemap({
      filter: (page) => !page.endsWith('/404/') && !page.includes('/404'),
    }),
  ],
});
