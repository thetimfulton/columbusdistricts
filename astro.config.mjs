// @ts-check
import { defineConfig } from 'astro/config';

// https://astro.build/config
// Cloudflare Pages target: served from the domain root (no subpath).
export default defineConfig({
  site: 'https://www.columbusdistricts.com',
  base: '/',
  trailingSlash: 'always',
});
