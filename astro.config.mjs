import { defineConfig } from "astro/config";
import expressiveCode from "astro-expressive-code";
import sitemap from "@astrojs/sitemap";
import icon from "astro-icon";
import remarkGfm from "remark-gfm";
import rehypeSlug from "rehype-slug";
import rehypeAutolinkHeadings from "rehype-autolink-headings";

export default defineConfig({
  devToolbar: {
    enabled: false,
  },
  site: "https://YUyingyingcao.github.io",
  markdown: {
    remarkPlugins: [remarkGfm],
    rehypePlugins: [
      rehypeSlug,
      [
        rehypeAutolinkHeadings,
        {
          behavior: "append",
          properties: {
            className: ["anchor-link"],
            ariaLabel: "复制这个小标题的入口",
          },
          content: {
            type: "text",
            value: " #",
          },
        },
      ],
    ],
  },
  integrations: [
    expressiveCode({
      themes: ["github-light"],
      styleOverrides: {
        borderRadius: "10px",
        frames: {
          frameBoxShadowCssValue: "0 16px 42px rgba(67, 103, 132, 0.18)",
        },
      },
    }),
    icon(),
    sitemap(),
  ],
});
