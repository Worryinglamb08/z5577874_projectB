# Prompt log — Investment website UI research

**Date:** 13 August 2026  
**Scope:** Visual and interaction research for the Stockist Funds Streamlit app

## What I wanted

Research current UI designs for websites and apps that present managed or
automated investment portfolios, then define a coherent, accessible interface
for Stockist Funds without copying another provider or creating a trading-style
experience.

## Prompt(s)

> Now research UI designs for such investment websites

## What the assistant produced

- Reviewed current official presentation and workflow patterns from Wealthfront,
  Betterment, BlackRock Australia, and Vanguard Australia.
- Reviewed current dashboard, comparison-table, tabs, chart, colour, responsive,
  and accessibility guidance from GOV.UK, Atlassian, and IBM Carbon.
- Created `ai/UI_DESIGN_RESEARCH.md` with:
  - reference-platform strengths and weaknesses;
  - a six-page information architecture;
  - the Stockist Funds global shell and visual language;
  - low-fidelity wireframes for overview, comparison, fact sheet, allocation,
    and sentiment pages;
  - a chart-selection matrix;
  - responsive and interaction rules;
  - UI acceptance criteria; and
  - a recommended fixture-data prototyping step.
- Recommended a labelled Streamlit sidebar for primary navigation rather than
  using top-level tabs as page navigation.
- Preserved the Project A Stockist Funds palette and extended it into explicit
  interface roles.

## What was wrong or risky

- Commercial investment sites are designed partly to acquire customers and
  deposits. Their conversion-focused hero sections and calls to action are not
  appropriate defaults for a coursework evidence product.
- Wealthfront and Betterment operate on real account and goal data that Stockist
  Funds does not have. The design cannot imply live balances, personal advice,
  tax optimisation, or forecasted goals.
- BlackRock's product pages are comprehensive but information-dense. Copying
  their full structure would obscure the assignment's required investor journey.
- Vanguard's fee calculator is useful, but a constant assumed return can be
  misunderstood as a forecast. Any Stockist illustration must keep assumptions
  adjacent to the output.
- Dark “fintech” styling can appear polished while reducing readability and
  evoking short-term trading. The proposed direction is light-first and
  evidence-led.
- Tabs can simplify a page but hide information needed for comparison and may
  behave poorly on small screens. They are limited to related secondary views.
- These are research-backed design hypotheses, not validated usability results.
  The proposed screens still require fixture prototyping and fresh-user testing.

## Checks performed

- Prioritised official product pages and maintained design-system sources.
- Compared visual examples with written descriptions of actual current app
  workflows, rather than relying only on promotional screenshots.
- Checked the proposed navigation against the brief's compare, fact-sheet,
  allocation, sentiment, and methodology needs.
- Checked the proposed visual system against the existing Project A palette and
  accessible non-colour cues.
- Kept monthly investable funds visually separate from daily, weekly, and
  bi-weekly diagnostics.
- Required exact tables or downloads alongside charts and avoided hover-only
  evidence.
- Did not modify the app or claim that the proposed design has been user tested.

## What I changed and why

The assistant converted visual research into a specific UI architecture rather
than a generic mood board. The chosen direction prioritises side-by-side
comparison, contextual risk, and evidence confidence because those functions
support both investor understanding and the Part B marking criteria.

## Student review still required

- Approve the six primary page names and sidebar navigation.
- Approve the light-first visual direction and continued Project A palette.
- Decide whether technical material should use expanders on each page or remain
  mostly within `Methods & data`.
- Approve a fixture-data prototype before final analytical outputs are wired in.
- Test the resulting shell on mobile and with a fresh user before treating these
  patterns as validated.

