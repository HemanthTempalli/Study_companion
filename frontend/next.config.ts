import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  allowedDevOrigins: ['192.168.56.1', 'localhost'],
};

export default nextConfig;
