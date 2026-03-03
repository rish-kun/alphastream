import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  typescript: {
    ignoreBuildErrors: false,
  },
  turbopack: {
    resolveAlias: {
      "@": "./src",
    },
  },
};

export default nextConfig;
