import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/enrollments/:path*",
        destination: `${process.env.ENROLLMENT_API || "http://localhost:8080"}/api/enrollments/:path*`,
      },
      {
        source: "/api/processed-enrollments/:path*",
        destination: `${process.env.PROCESSING_API || "http://localhost:8081"}/api/processed-enrollments/:path*`,
      },
      // AI routes handled by src/app/api/ai/ route handlers (longer timeout)
    ];
  },
};

export default nextConfig;
