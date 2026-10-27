# Design System & Visual Guidelines – Samanvay (समन्वय)

This document specifies the visual identity, typography, design tokens, color palette, and component design patterns used across the Samanvay user interface.

---

## 1. Design Philosophy: Command-and-Control for Governance

Samanvay is built as a mission-critical **regulatory command-and-control platform** for government officers. The visual language balances:
1. **High Information Density with Zero Clutter**: Essential metrics (SLA deadlines, open overlaps, conflict warnings) are immediately legible without unnecessary ornamentation.
2. **Authoritative Government Aesthetics**: Deep Navy and Slate backgrounds convey trust, institutional authority, and official stature.
3. **High-Contrast Status Signaling**: Strict semantic color coding (Emerald for resolved/verified, Amber for impending SLA/warnings, Rose/Red for critical conflicts/violations).
4. **Bilingual Legibility**: Typography and layouts accommodate varying length between English and Hindi (हिन्दी) Devanagari script.

---

## 2. Color Palette & Semantic Tokens

```
Deep Navy (#0f172a)     Slate Surface (#f8fafc)    AICTE Blue (#1d4ed8)
      ████                     ████                     ████
Success Green (#16a34a) Warning Amber (#f59e0b) Critical Danger (#dc2626)
      ████                     ████                     ████
```

### 2.1 Color Tokens
| Token | Hex / HSL | Usage |
| :--- | :--- | :--- |
| `navy.DEFAULT` | `#0f172a` (Slate 900) | Sidebar background, primary brand headers, executive cards. |
| `navy.light` | `#1e293b` (Slate 800) | Sidebar active item state, sub-headers, dark mode accents. |
| `background` | `hsl(0, 0%, 100%)` | Main workspace background, modal bodies. |
| `card` | `#ffffff` / border `#e2e8f0` | Content container cards, table wrappers, case item cards. |
| `primary` | `#0f172a` | Primary call-to-action buttons, active navigation markers. |
| `aicte-blue` | `#1d4ed8` / `#2563eb` | Lead bureau badges, coordination room highlight, active links. |
| `success` | `#16a34a` (Emerald 600) | Cryptographic chain verified, compliant institutions, resolved cases. |
| `warning` | `#f59e0b` (Amber 500) | Pre-save overlap banner, impending SLA breach ($\le$ 3 days), moderate risk. |
| `danger` | `#dc2626` (Red 600) | Action Intent conflicts, high-risk institutions ($\ge$ 70), broken hashes. |

---

## 3. Typography & Hierarchy

### 3.1 Font Stack
```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
  'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
```
For Hindi text, fallback relies on system Devanagari fonts (*Nirmala UI*, *Mangal*, *Kohinoor Devanagari*) ensuring clear glyph rendering at all sizes.

### 3.2 Type Scale
- **H1 / Page Title**: `text-2xl font-bold tracking-tight text-slate-900`
- **H2 / Section Title**: `text-lg font-semibold text-slate-900`
- **H3 / Card Header**: `text-sm font-semibold text-slate-800`
- **Body Regular**: `text-sm text-slate-600 leading-normal`
- **Subtext / Captions**: `text-xs text-slate-500`
- **Micro-labels / Badges**: `text-[11px] font-bold uppercase tracking-wider`
- **Code / Cryptographic Hash**: `font-mono text-xs text-slate-700 bg-slate-100 rounded px-1.5 py-0.5`

---

## 4. Key UI Components & Design Patterns

### 4.1 Exception-Only "My Desk" Cards
- High-priority cards feature a subtle 4px left-border accent:
  - Red accent for action intent conflicts.
  - Amber accent for pending overlap requests.
  - Emerald accent for completed joint decisions.

### 4.2 Pre-Save Live Overlap Warning Banner
- Rendered inline within the Complaint Intake Modal.
- Background: Amber-50 (`bg-amber-50/90 border border-amber-200`).
- Icon: Alert triangle with glowing pulse effect.
- Action: Direct high-contrast button *"Save & Open Coordination Room"*.

### 4.3 Side-by-Side Coordination Room Diff View
- 2-Column responsive split:
  - Left Column: Regulation Bureau / Case A details.
  - Right Column: PGRC / Case B details.
- Highlighted Differences: Category variance, date disparities, and contradictory allegations highlighted in soft blue/amber badges.
- Central Lead Recommendation Pill: Floating pill indicating *"Recommended Lead: Regulation Bureau"* with statutory rationale.

### 4.4 Common Operating Picture (COP) Map Pins
- Built on Leaflet with custom circular SVG markers:
  - 🟢 **Green** (`#16a34a`): Risk Score < 35, 0 active cross-bureau overlaps.
  - 🟡 **Amber** (`#f59e0b`): Risk Score 35–69, or single-bureau inquiry.
  - 🔴 **Red** (`#dc2626`): Risk Score $\ge$ 70, or active multi-bureau dispute.
  - Popup: Displays institution name, AICTE ID, open complaints, and button to open full college dossier.

### 4.5 Status Badges
| Status | Class Styling |
| :--- | :--- |
| `Suggested` | `bg-amber-50 text-amber-700 border-amber-200` |
| `Confirmed Related` | `bg-blue-50 text-blue-700 border-blue-200` |
| `Coordinating` | `bg-purple-50 text-purple-700 border-purple-200` |
| `Decided` | `bg-emerald-50 text-emerald-700 border-emerald-200` |
| `Rejected` | `bg-slate-100 text-slate-600 border-slate-200` |

---

## 5. Responsive Layout & Breakpoints

- **Sidebar**: Fixed on desktop (`w-64`), collapsible/hidden on mobile (`< 768px`) with touch drawer.
- **Top Navigation Bar**: Persistent notification badge, language switcher (`EN / हिन्दी`), and active user profile dropdown.
- **Breakpoints**: Standard Tailwind breakpoints (`sm: 640px`, `md: 768px`, `lg: 1024px`, `xl: 1280px`).
