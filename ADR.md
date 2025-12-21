# Architecture Decision Records

This document captures key architectural decisions for the Dishcovery project.

---

## Template

Use this template for new ADRs:

```markdown
## ADR-XXX: [Title]

**Date:** YYYY-MM-DD
**Status:** Proposed | Accepted | Deprecated | Superseded
**Tickets:** [related ticket IDs]

### Context

[What is the issue that we're seeing that is motivating this decision?]

### Decision

[What is the change that we're proposing and/or doing?]

### Consequences

[What becomes easier or more difficult to do because of this change?]
```

---

## ADR-001: Server-Side Rendering with Jinja2 + HTMX

**Date:** 2025-12-21
**Status:** Accepted
**Tickets:** dishcovery-dx1, dishcovery-cir, dishcovery-lwv

### Context

The project originally started with a JSON API architecture, anticipating a separate frontend client (React, Vue, or similar SPA). The docker-compose.yml included a commented-out `dishcovery-ui` service placeholder.

After evaluating the requirements:
- Recipe search with faceted filtering
- Simple browse/search/filter UX
- Single deployment simplicity
- Python-only stack preference

### Decision

Adopt **server-side rendering** using:
- **Jinja2** for HTML templates
- **HTMX** for dynamic interactions without writing JavaScript

This replaces the original plan of JSON API + separate frontend.

### Consequences

**Positive:**
- Single codebase and deployment
- No JavaScript build tooling required
- Simpler mental model (request -> HTML response)
- HTMX provides SPA-like UX with minimal complexity
- Faster initial page loads (no JS bundle)

**Negative:**
- Less flexibility for future native mobile apps (would need to add JSON API back)
- Team must learn HTMX patterns
- OpenAPI docs (`/docs`) become less relevant for the main search endpoint

### Implementation

1. Remove JSON response from `/search` endpoint
2. `/search` returns HTML fragments for HTMX consumption
3. Keep `/health`, `/metrics`, `/bulk-load` as JSON (operational endpoints)
4. Templates in `api/templates/`, static files in `api/static/`

---

## ADR-002: Hybrid Endpoint Strategy (Rejected)

**Date:** 2025-12-21
**Status:** Rejected (superseded by ADR-001)

### Context

During planning, we considered a hybrid approach where `/search` would return JSON or HTML based on the `HX-Request` header (content negotiation).

### Decision

Rejected in favor of full HTML-only for `/search`.

### Rationale

Since we decided on server-rendered HTML as the *only* client (ADR-001), there's no need for JSON responses from `/search`. Content negotiation adds complexity without benefit.

---

## ADR-003: Form Encoding for Search Requests

**Date:** 2025-12-21
**Status:** Accepted
**Tickets:** dishcovery-lwv

### Context

The original JSON API used `POST /search` with a JSON body (`application/json`). HTMX forms submit as `application/x-www-form-urlencoded` by default.

Options considered:
1. Accept form-encoded data natively
2. Use HTMX `json-enc` extension to send JSON

### Decision

Accept **form-encoded data** for the search endpoint.

### Rationale

- Simpler setup (no extra JS extension needed)
- HTML forms work naturally
- For a basic search input, we only need the `query` field initially
- Can expand to include filter fields as form inputs later

### Implementation

```python
@app.post("/search")
async def search_recipes(query: str = Form(None), size: int = Form(10)):
    # Build search request from form fields
```

---

## ADR-004: Modern CSS Features (Container Queries, Layers, Scopes)

**Date:** 2025-12-21
**Status:** Accepted

### Context

The project needs a CSS architecture for the Jinja2 + HTMX frontend. Options range from CSS frameworks (Tailwind, Bootstrap) to vanilla CSS with modern features.

Modern CSS (2023+) provides powerful native features that previously required preprocessors or frameworks:
- **CSS Layers** (`@layer`) - Control cascade ordering
- **Container Queries** (`@container`) - Component-responsive design
- **CSS Scopes** (`@scope`) - Scoped styling without BEM or CSS-in-JS

Browser support (as of late 2024):
- `@layer`: ~95% global support
- `@container`: ~90% global support
- `@scope`: ~85% global support (Chrome 118+, Safari 17.4+, Firefox 128+)

### Decision

Use **modern vanilla CSS** with:
- **`@layer`** for organizing styles (reset, base, components, utilities)
- **`@container`** for component-level responsive design
- **`@scope`** for encapsulated component styles

No CSS framework or preprocessor.

### Rationale

- **Simplicity**: No build step, no node_modules, aligns with HTMX philosophy
- **Performance**: Native browser features, no runtime CSS-in-JS overhead
- **Maintainability**: Scoped styles prevent cascade conflicts naturally
- **Future-proof**: Standards-based, not framework-dependent
- **Component-friendly**: Container queries enable truly reusable components

### Consequences

**Positive:**
- Zero CSS build tooling
- Smaller payload (no framework CSS)
- Styles are co-located and scoped to components
- Container queries make recipe cards responsive to their container, not viewport
- Layers prevent specificity wars

**Negative:**
- ~10-15% of users on older browsers may have degraded experience
- Team must learn newer CSS features
- Less documentation/examples compared to established frameworks
- No utility classes out of the box

### Implementation

```css
/* Layer ordering - defined once */
@layer reset, base, components, utilities;

/* Component with container query */
@layer components {
  .recipe-card-container {
    container-type: inline-size;
    container-name: recipe-card;
  }

  @container recipe-card (min-width: 300px) {
    .recipe-card {
      display: grid;
      grid-template-columns: 1fr 2fr;
    }
  }
}

/* Scoped styles for search results */
@scope (.search-results) to (.recipe-card) {
  h2 { font-size: 1.25rem; }
  p { color: var(--text-muted); }
}
```

### Browser Support Strategy

- Use `@supports` for progressive enhancement where needed
- Core functionality works without these features (graceful degradation)
- Target modern evergreen browsers (last 2 versions)

---

## ADR-005: Template Organization with HTMX Partials

**Date:** 2025-12-21
**Status:** Accepted

### Context

With Jinja2 + HTMX (ADR-001), templates fall into two categories:

1. **Full pages** - Complete HTML documents for initial page loads
2. **Partials** - HTML fragments swapped by HTMX into existing DOM elements

Without conventions, it's unclear which templates are pages vs fragments, and how partials relate to their swap targets.

### Decision

```
api/templates/
├── index.html             # Full page
├── partials/              # HTMX fragments
│   └── search_results.html
```

**Conventions:**

1. **Full pages** live at the root of `templates/`
2. **Partials** live in `templates/partials/`
3. **Naming convention:** Partial filenames match their `hx-target` ID
   - `hx-target="#search-results"` → `partials/search_results.html`
   - `hx-target="#recipe-detail"` → `partials/recipe_detail.html`
4. Partials must NOT include document-level tags (`<!DOCTYPE>`, `<html>`, `<head>`, `<body>`)

### Consequences

**Positive:**
- Location signals purpose (root = page, `partials/` = fragment)
- Naming convention creates traceable link between frontend `hx-target` and backend template
- Easy to find which template renders a given DOM region

**Negative:**
- Requires discipline to maintain naming alignment
- Render calls need `partials/` prefix
