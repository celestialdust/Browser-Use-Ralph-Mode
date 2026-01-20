import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Transpile remark-gfm and its dependencies to fix Turbopack ESM resolution issues
  transpilePackages: [
    "remark-gfm",
    "mdast-util-gfm",
    "mdast-util-gfm-table",
    "mdast-util-gfm-strikethrough",
    "mdast-util-gfm-task-list-item",
    "mdast-util-gfm-autolink-literal",
    "mdast-util-gfm-footnote",
    "micromark-extension-gfm",
    "micromark-extension-gfm-table",
  ],
};

export default nextConfig;
