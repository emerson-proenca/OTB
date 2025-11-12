export const manifest = (() => {
  function __memo(fn) {
    let value;
    return () => (value ??= value = fn());
  }

  return {
    appDir: "_app",
    appPath: "_app",
    assets: new Set(["favicon.png", "otb.svg", "otb.svg", "otb.svg"]),
    mimeTypes: { ".png": "image/png", ".svg": "image/svg+xml" },
    _: {
      client: {
        start: "_app/immutable/entry/start.CNZNGmgz.js",
        app: "_app/immutable/entry/app.CESycoG5.js",
        imports: [
          "_app/immutable/entry/start.CNZNGmgz.js",
          "_app/immutable/chunks/DReKMYYU.js",
          "_app/immutable/chunks/vJZCVrIk.js",
          "_app/immutable/chunks/DdNP_-N1.js",
          "_app/immutable/entry/app.CESycoG5.js",
          "_app/immutable/chunks/vJZCVrIk.js",
          "_app/immutable/chunks/D9Ra-wEw.js",
          "_app/immutable/chunks/BUC0fcqK.js",
          "_app/immutable/chunks/DdNP_-N1.js",
          "_app/immutable/chunks/BPk0C5hz.js",
        ],
        stylesheets: [],
        fonts: [],
        uses_env_dynamic_public: false,
      },
      nodes: [
        __memo(() => import("./nodes/0.js")),
        __memo(() => import("./nodes/1.js")),
        __memo(() => import("./nodes/2.js")),
      ],
      remotes: {},
      routes: [
        {
          id: "/",
          pattern: /^\/$/,
          params: [],
          page: { layouts: [0], errors: [1], leaf: 2 },
          endpoint: null,
        },
      ],
      prerendered_routes: new Set([]),
      matchers: async () => {
        return {};
      },
      server_assets: {},
    },
  };
})();
