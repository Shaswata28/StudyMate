import type { NextConfig } from "next";

const nextConfig: NextConfig = process.env.STUDYMATE_RELEASE === "1"
  ? { output: "export", trailingSlash: true }
  : {
      experimental: { proxyTimeout: 30 * 60 * 1000 },
      async rewrites() {
        return [{ source: "/api/:path*", destination: "http://127.0.0.1:8000/api/:path*" }];
      },
    };

export default nextConfig;
