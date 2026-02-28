import type { NextConfig } from "next";

const nextConfig: NextConfig = {
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
