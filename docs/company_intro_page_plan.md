# Company Intro Page Plan

- Purpose: Build a modern company introduction page reusing the content from `docs/Introduction.md` and the visual asset `static/img/bable_ci.png`.
- Tone: Confident and polished, matching existing site styling while updating to a more contemporary, content-first layout.
- Tech: Bootstrap 5.3, responsive-first, light theme with subtle depth (shadows, gradients, soft dividers).

## Content Inputs
- Text: English and zh-CN copy from `docs/Introduction.md` (About + Vision). Keep both languages accessible via tabs.
- Visual: Use `static/img/bable_ci.png` as the hero anchor (logo/mark) and optionally as a watermark in the vision section.

## Visual Direction
- Color: Use brand palette from `bable_ci.png` — rich charcoal (`#231815`) for primary text, bright orange dot accent (`#e7501e`), soft warm gray (`#d1d1d1`) for secondary UI, and white/off-white background. Add a subtle warm gradient header (`linear-gradient(135deg, #fff8f5, #f3f0ec)`) to avoid a flat feel.
- Typography: Use one expressive sans (e.g., `Manrope` or `Space Grotesk`) for headings and a clean sans (e.g., `Inter`-like fallback) for body. Slight letter-spacing on headings for a modern feel.
- Shapes: Rounded corners (12–16px), subtle blurred gradient blobs behind hero image, thin dividers to separate blocks.
- Motion: Gentle fade-up + stagger on sections; CTA buttons have micro hover lift and shadow.

## Page Structure (desktop → mobile stack)
1. Hero band  
   - Left: Badge (“About B.able”), concise headline, one-sentence elevator pitch, primary CTA (“Contact Sales”) + secondary (“Download Deck”).  
   - Right: Card featuring `bable_ci.png` with a soft gradient backdrop and a caption.
2. Language toggle  
   - Tabs (EN | 中文) controlling text blocks below; default EN. Persist language selection per session (localStorage optional later).
3. About & Vision split  
   - Two-column layout; left “About B.able Company” text, right “Our Vision”. Include a small accent badge on Vision.
4. What We Do (pillars)  
   - Three cards: Live Commerce, Short-form Commerce, Content Commerce. Each with icon, one-liner, and key metric/benefit.
5. Global Strengths / Differentiators  
   - Grid of four highlights (e.g., “Global Talent”, “Data-driven Marketing”, “K-Brand Focus”, “Omnichannel Reach”) with concise copy.
6. Process Snapshot  
   - Horizontal steps (Discover → Produce → Launch → Optimize) with icons; stack vertically on mobile.
7. Social Proof / Metrics (optional if data available)  
   - Metric chips (e.g., “+X brands onboarded”, “Y% uplift”, “Z markets”); omit if not confirmed.
8. CTA Footer  
   - Brief invitation, button to contact and secondary to learn more. Include small print for email contact.

## Responsiveness
- Desktop: 2–3 column grids with ample whitespace.  
- Tablet: 2-column cards; hero image scales to 60% width.  
- Mobile: Single column, center-aligned text, stacked CTAs full-width, reduced padding.

## Component Styling Notes
- Buttons: Pill shape, bold label, primary uses teal, secondary outline navy with hover fill.
- Cards: Soft shadow (`rgba(15,23,42,0.08)`), 14–16px radius, inner padding 20–24px.
- Tabs: Underline style with accent color; clear focus states.
- Dividers: Hairline (`1px`) with slight opacity to segment sections without heavy borders.

## Asset Usage
- Place `static/img/bable_ci.png` in the hero image card; reuse as a faint watermark background in the vision block (using CSS opacity/blur).
- Consider adding a gradient overlay (`linear-gradient(135deg, #e0f7f4, #fef3c7)`) behind the hero for depth.

## Copy Adaptation
- Keep sentences concise for hero; move full paragraphs into About/Vision blocks.  
- Use consistent labels: “About B.able Company”, “Our Vision”, “What We Do”, “How We Operate”.

## Implementation Notes
- Template location suggestion: `templates/company_intro.html` with Bootstrap components; add route as needed.  
- Keep utility classes consistent with existing styles; add minimal scoped CSS if required (e.g., `company-hero` class).  
- Ensure image is loaded via static tag and responsive (`img-fluid`, max width constraints).
- Default language EN; toggle uses simple JS to switch content blocks without reload.
