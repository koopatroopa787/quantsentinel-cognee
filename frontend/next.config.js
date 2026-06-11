/** @type {import('next').NextConfig} */
const nextConfig = {
  // Raise the Node.js HTTP server socket timeout so long-running SSE streams
  // (ADK timeout 90s + fallback pipeline ~60s) don't get dropped mid-stream.
  serverExternalPackages: [],
};

// Patch the http.Server timeout after Next.js creates it
const { createServer } = require("http");
const _origCreate = createServer;
// eslint-disable-next-line no-global-assign
require("http").createServer = function (...args) {
  const server = _origCreate(...args);
  server.setTimeout(600_000); // 10 minutes — well beyond any legitimate run
  server.keepAliveTimeout = 600_000;
  server.headersTimeout  = 601_000;
  return server;
};

module.exports = nextConfig;
