import type { NextConfig } from "next";

const config: NextConfig = {
  reactStrictMode: true,
  // The dashboard reads the API through NEXT_PUBLIC_API_BASE (see .env.local.example).
  // No rewrites/proxy: keeping the API's real origin visible means CORS problems surface
  // in development rather than in production.
};

export default config;
