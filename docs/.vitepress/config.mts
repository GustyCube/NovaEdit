import { defineConfig } from "vitepress";

export default defineConfig({
  title: "NovaEdit",
  description: "Code-edit–first model, server, and tooling.",
  lang: "en-US",
  srcDir: ".",
  cleanUrls: true,
  lastUpdated: true,
  themeConfig: {
    nav: [
      { text: "Guide", link: "/guide/quickstart" },
      { text: "API", link: "/api/server" },
      { text: "Plan", link: "/plan" },
      { text: "GitHub", link: "https://github.com/GustyCube/novaedit" }
    ],
    sidebar: [
      {
        text: "Guide",
        collapsed: false,
        items: [
          { text: "Quickstart", link: "/guide/quickstart" },
          { text: "Data & Training", link: "/guide/data" }
        ]
      },
      {
        text: "API",
        collapsed: false,
        items: [{ text: "Server API", link: "/api/server" }]
      },
      {
        text: "Project",
        collapsed: false,
        items: [{ text: "Plan", link: "/plan" }]
      }
    ],
    socialLinks: [{ icon: "github", link: "https://github.com/GustyCube/novaedit" }]
  },
  markdown: {
    theme: "github-light"
  }
});
