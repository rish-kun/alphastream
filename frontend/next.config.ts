import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Standalone output for Docker deployments
  output: "standalone",
  typescript: {
    // Type checking is done separately via tsc
    ignoreBuildErrors: false,
  },
  eslint: {
    // Linting is done separately via eslint
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;
