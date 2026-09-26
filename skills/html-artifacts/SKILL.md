---
name: html-artifacts
description: Create a self-contained, offline HTML artifact when a response is dense, visual, interactive, or worth keeping or sharing—for example a plan, report, research explainer, review summary, comparison, diagram, walkthrough, timeline, or dashboard. Do not use for a short answer that is clearer in chat.
argument-hint: "[output-directory] [artifact-title]"
license: MIT
---

# html-artifacts

> **Quick usage:**
> ```
> html-artifacts
> html-artifacts /private/path/to/artifacts "Architecture review"
> ```

Create a single polished HTML file instead of a long chat response when the
deliverable benefits from visual structure, interaction, durability, or sharing.
Offer the artifact when it would help; produce it directly when the user asks for
a report, plan, comparison, diagram, dashboard, walkthrough, or saved deliverable.

## Non-negotiables

- Deliver exactly one `.html` file. Put all CSS in a `<style>` block and all
  JavaScript in a `<script>` block in that file.
- Make no external network requests: no CDNs, web fonts, images, icons,
  iframes, imports, or package dependencies. The file must work offline.
- Keep content accessible: semantic headings, table headers, visible focus,
  keyboard-operable interactions, responsive layouts, and text labels in
  addition to color for status or meaning.
- Use the house tokens below. Define them once in `:root`; components consume
  variables rather than adding one-off visual values.
- If the user supplies a private output directory, use it. Otherwise create a
  private per-run directory under the operating system temporary directory,
  save a dated, kebab-case filename there, and report the absolute path. Do
  not default generated artifacts to a repository.
- Open the completed file in an available browser or capture a screenshot.
  Check that the title, primary content, overflow behavior, and any interaction
  render correctly before saying it is done. Repair visible defects and verify
  again.

## House style

Use a warm, restrained developer aesthetic: quiet charcoal surfaces, Ruby-red
actions, small cyan highlights, strong typography, and generous whitespace.
Avoid neon, decorative terminal chrome, pervasive gradients, and card clutter.

```css
:root {
  --font-sans: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
    "Segoe UI", sans-serif;
  --font-mono: ui-monospace, "SFMono-Regular", Consolas, "Liberation Mono",
    monospace;

  --bg: #11151B;
  --surface: #1A2029;
  --text: #F5F2ED;
  --text-muted: #B8C0CC;
  --ruby: #CC342D;
  --ruby-bright: #FF817A;
  --cyan: #64D8E8;
  --focus: #F3C969;
  --divider: #343E4C;
  --border: #718096;

  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-6: 24px;
  --space-8: 32px;
  --space-12: 48px;
  --space-16: 64px;
  --radius-control: 8px;
  --radius-card: 12px;
  --shadow-float: 0 12px 32px rgba(0, 0, 0, 0.24);
}
```

Default to the dark palette above. Use `--ruby` for a primary action or the
selected state, `--cyan` for supporting emphasis, and `--ruby-bright` for red
text on a dark surface. Use `--focus` as a 3px outline with a 3px offset.
Keep body text at least 16px with a 1.6 line height, prose near 68 characters,
and controls at least 44px tall. Use 8px control corners, 12px cards, and the
shadow only for floating surfaces.

## Choose a layout

Start with one clear title, a short purpose statement, and a small metadata row
(date, scope, or status) when useful. Use the least-complex pattern that makes
the information easier to understand.

- **Report:** a readable single column, executive summary first, then findings,
  evidence, and next steps. Use callouts sparingly for decisions or risks.
- **Comparison:** a scrollable-on-small-screens semantic table. Keep criteria
  in the first column, use a highlighted recommended column only when a
  recommendation is supported, and state the deciding assumptions nearby.
- **Timeline:** chronological events with dates, short titles, and one outcome
  per event. Use a vertical line on narrow screens; do not rely on left-right
  positioning to convey order.
- **Diagram:** use HTML and CSS layout for boxes and connectors, with a text
  reading order that matches the flow. Include a compact legend and a plain-text
  explanation of the relationships.
- **Dashboard:** lead with three to six meaningful metrics, then supporting
  trends, filters, or detail. Make controls genuinely work with inline
  JavaScript, or omit them.

## Build and hand off

1. Extract the decision, audience, and content from the current task. Prefer a
   compact artifact over copying the entire conversation.
2. Pick the layout above, write the HTML, and keep all styling and behavior in
   the one file. Use system fonts and CSS/HTML primitives before adding visual
   complexity.
3. For interaction, use small inline JavaScript and make its initial state
   useful without JavaScript where practical. Honor `prefers-reduced-motion`.
4. Render-check the actual file. Verify at a desktop width and a narrow width;
   test at least one interactive control if present.
5. Return a brief chat handoff with a clickable absolute file link and one-line
   summary. Mention any unverified assumption rather than presenting it as fact.

## Output

Return the artifact path and a concise description of what it contains. Keep
the detailed material in the HTML file, not duplicated in chat.
