// Formats HTML/CSS/JS files in place the way webformatter.com/html does (Prettier 3.3.3 with its default options there).
// usage: node format.mjs file [file ...]      (run "npm install" in this folder once)
import fs from "node:fs";
import * as prettier from "prettier";
const OPTS = { printWidth: 120, tabWidth: 4, useTabs: false, semi: true, singleQuote: false, trailingComma: "es5", bracketSpacing: true, arrowParens: "always", endOfLine: "lf", proseWrap: "preserve" };
let failed = 0;
for (const f of process.argv.slice(2)) {
    const parser = f.endsWith(".css") ? "css" : f.endsWith(".js") || f.endsWith(".mjs") ? "babel" : "html";
    try {
        const src = fs.readFileSync(f, "utf8");
        const out = await prettier.format(src, { ...OPTS, parser });
        if (out !== src) fs.writeFileSync(f, out);
    } catch (e) {
        failed++;
        console.error("FAILED " + f + "\n" + String(e.message).slice(0, 800));
    }
}
process.exit(failed ? 1 : 0);
