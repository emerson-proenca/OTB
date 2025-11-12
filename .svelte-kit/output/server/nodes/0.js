

export const index = 0;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/fallbacks/layout.svelte.js')).default;
export const universal = {
  "ssr": false
};
export const universal_id = "src/routes/+layout.ts";
export const imports = ["_app/immutable/nodes/0.Daw8ByYf.js","_app/immutable/chunks/BUC0fcqK.js","_app/immutable/chunks/vJZCVrIk.js","_app/immutable/chunks/BPk0C5hz.js"];
export const stylesheets = [];
export const fonts = [];
