/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  trailingSlash: true,
  distDir: 'out',
  // Ensure static generation works
  generateBuildId: async () => {
    return 'swarm-squad-ep2'
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.resolve = {
        ...config.resolve,
        fallback: {
          ...config.resolve.fallback,
          url: false,
          punycode: false,
          querystring: false
        }
      }
    }
    return config;
  },
}

export default nextConfig
