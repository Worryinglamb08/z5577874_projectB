"""Accessible single-bar allocation control for two to four funds."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import streamlit as st

_HTML = """
<div class="allocation-control">
  <p class="instructions">Drag a divider to transfer allocation between neighbouring funds.</p>
  <div class="allocation-track" role="group" aria-label="Fund allocation"></div>
  <div class="allocation-legend"></div>
  <div class="allocation-total" aria-live="polite">Allocation total · 100%</div>
</div>
"""

_CSS = """
:host {
  color: var(--st-text-color, #0F172A);
  font-family: Aptos, Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.allocation-control { width: 100%; padding: 0.2rem 0 0.35rem; }
.instructions { margin: 0 0 0.7rem; color: #475569; font-size: 0.9rem; }
.allocation-track {
  position: relative; width: 100%; height: 72px; overflow: visible;
  border: 1px solid #B8C5CA; border-radius: 9px; background: #EEF2F3;
  box-sizing: border-box; touch-action: none;
}
.allocation-segment {
  position: absolute; inset-block: 0; display: flex; align-items: center;
  justify-content: center; overflow: hidden; box-sizing: border-box;
  border-right: 2px solid #FFFFFF; transition: none;
}
.allocation-segment:first-child { border-radius: 8px 0 0 8px; }
.allocation-segment.last { border-right: 0; border-radius: 0 8px 8px 0; }
.segment-value {
  color: #FFFFFF; font-size: 0.9rem; font-weight: 700;
  text-shadow: 0 1px 2px rgba(15, 23, 42, 0.45); white-space: nowrap;
}
.allocation-handle {
  position: absolute; top: 50%; width: 28px; height: 28px;
  transform: translate(-50%, -50%); border-radius: 50%;
  border: 3px solid #FFFFFF; background: #0F172A;
  box-shadow: 0 1px 5px rgba(15, 23, 42, 0.35); cursor: ew-resize;
  z-index: 5; padding: 0;
}
.allocation-handle:hover, .allocation-handle:focus-visible {
  outline: 3px solid rgba(15, 118, 110, 0.28); outline-offset: 2px;
}
.allocation-legend {
  display: grid; grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.5rem 1rem; margin-top: 0.85rem;
}
.legend-item { display: flex; align-items: flex-start; min-width: 0; gap: 0.5rem; }
.legend-swatch {
  width: 12px; height: 12px; border-radius: 3px; flex: 0 0 auto; margin-top: 0.2rem;
}
.legend-copy { min-width: 0; color: #334155; font-size: 0.86rem; line-height: 1.3; }
.legend-label { overflow-wrap: anywhere; }
.legend-value { color: #0F172A; font-weight: 700; white-space: nowrap; }
.allocation-total {
  display: inline-block; margin-top: 0.75rem; padding: 0.23rem 0.58rem;
  border-radius: 999px; background: #DDF3EF; color: #0B514C;
  font-size: 0.84rem; font-weight: 700;
}
@media (max-width: 640px) {
  .allocation-track { height: 62px; }
  .allocation-legend { grid-template-columns: 1fr; }
  .segment-value { font-size: 0.8rem; }
}
"""

_JS = """
export default function(component) {
  const { data, parentElement, setStateValue } = component;
  const labels = Array.isArray(data.labels) ? data.labels.map(String) : [];
  const incoming = Array.isArray(data.weights) ? data.weights.map(Number) : [];
  const colors = ['#0F766E', '#0072B2', '#E69F00', '#CC79A7'];
  let weights = incoming.slice();
  let activeCleanup = null;

  const track = parentElement.querySelector('.allocation-track');
  const legend = parentElement.querySelector('.allocation-legend');
  track.replaceChildren();
  legend.replaceChildren();

  const segments = [];
  const segmentValues = [];
  const handles = [];
  const legendValues = [];

  labels.forEach((label, index) => {
    const segment = document.createElement('div');
    segment.className = `allocation-segment${index === labels.length - 1 ? ' last' : ''}`;
    segment.style.background = colors[index % colors.length];
    segment.setAttribute('aria-hidden', 'true');
    const value = document.createElement('span');
    value.className = 'segment-value';
    segment.appendChild(value);
    track.appendChild(segment);
    segments.push(segment);
    segmentValues.push(value);

    const item = document.createElement('div');
    item.className = 'legend-item';
    const swatch = document.createElement('span');
    swatch.className = 'legend-swatch';
    swatch.style.background = colors[index % colors.length];
    const copy = document.createElement('span');
    copy.className = 'legend-copy';
    const labelNode = document.createElement('span');
    labelNode.className = 'legend-label';
    labelNode.textContent = label;
    const valueNode = document.createElement('span');
    valueNode.className = 'legend-value';
    copy.append(labelNode, document.createTextNode(' · '), valueNode);
    item.append(swatch, copy);
    legend.appendChild(item);
    legendValues.push(valueNode);
  });

  const updateUI = () => {
    let cumulative = 0;
    segments.forEach((segment, index) => {
      segment.style.left = `${cumulative}%`;
      segment.style.width = `${weights[index]}%`;
      segmentValues[index].textContent = weights[index] >= 7 ? `${weights[index]}%` : '';
      legendValues[index].textContent = `${weights[index]}%`;
      cumulative += weights[index];
      if (index < handles.length) {
        handles[index].style.left = `${cumulative}%`;
        handles[index].setAttribute('aria-valuenow', String(weights[index]));
        handles[index].setAttribute('aria-valuemax', String(weights[index] + weights[index + 1]));
        handles[index].setAttribute(
          'aria-valuetext',
          `${labels[index]} ${weights[index]}%, ${labels[index + 1]} ${weights[index + 1]}%`,
        );
      }
    });
  };

  const changePair = (index, newLeft) => {
    const pairTotal = weights[index] + weights[index + 1];
    const bounded = Math.max(0, Math.min(pairTotal, Math.round(newLeft)));
    weights[index] = bounded;
    weights[index + 1] = pairTotal - bounded;
    updateUI();
  };

  const commit = () => setStateValue('weights', weights.slice());

  for (let index = 0; index < labels.length - 1; index += 1) {
    const handle = document.createElement('button');
    handle.type = 'button';
    handle.className = 'allocation-handle';
    handle.setAttribute('role', 'slider');
    handle.setAttribute('aria-valuemin', '0');
    handle.setAttribute(
      'aria-label',
      `Resize ${labels[index]} and ${labels[index + 1]}`,
    );

    handle.addEventListener('pointerdown', (event) => {
      event.preventDefault();
      if (activeCleanup) activeCleanup();
      const prefix = weights.slice(0, index).reduce((sum, value) => sum + value, 0);
      const move = (moveEvent) => {
        const rect = track.getBoundingClientRect();
        const absolute = ((moveEvent.clientX - rect.left) / rect.width) * 100;
        changePair(index, absolute - prefix);
      };
      const finish = () => {
        window.removeEventListener('pointermove', move);
        window.removeEventListener('pointerup', finish);
        window.removeEventListener('pointercancel', finish);
        document.body.style.cursor = '';
        activeCleanup = null;
        commit();
      };
      activeCleanup = () => {
        window.removeEventListener('pointermove', move);
        window.removeEventListener('pointerup', finish);
        window.removeEventListener('pointercancel', finish);
        document.body.style.cursor = '';
      };
      document.body.style.cursor = 'ew-resize';
      window.addEventListener('pointermove', move);
      window.addEventListener('pointerup', finish, { once: true });
      window.addEventListener('pointercancel', finish, { once: true });
    });

    handle.addEventListener('keydown', (event) => {
      const increment = event.shiftKey ? 5 : 1;
      const pairTotal = weights[index] + weights[index + 1];
      if (event.key === 'ArrowLeft' || event.key === 'ArrowDown') {
        event.preventDefault();
        changePair(index, weights[index] - increment);
        commit();
      } else if (event.key === 'ArrowRight' || event.key === 'ArrowUp') {
        event.preventDefault();
        changePair(index, weights[index] + increment);
        commit();
      } else if (event.key === 'Home') {
        event.preventDefault();
        changePair(index, 0);
        commit();
      } else if (event.key === 'End') {
        event.preventDefault();
        changePair(index, pairTotal);
        commit();
      }
    });
    track.appendChild(handle);
    handles.push(handle);
  }

  updateUI();
  return () => {
    if (activeCleanup) activeCleanup();
  };
}
"""

def _component_renderer():
    """Register against the active Streamlit runtime and return the renderer."""
    return st.components.v2.component(
        "stockist_allocation_slider",
        html=_HTML,
        css=_CSS,
        js=_JS,
    )


def _valid_weights(values: Any, count: int) -> list[int] | None:
    """Return whole percentages summing to 100, or ``None`` when malformed."""
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        return None
    if len(values) != count:
        return None
    try:
        weights = [int(value) for value in values]
    except (TypeError, ValueError):
        return None
    if any(weight < 0 or weight > 100 for weight in weights):
        return None
    return weights if sum(weights) == 100 else None


def allocation_slider(
    labels: Sequence[str], default_weights: Sequence[int], *, key: str
) -> list[int]:
    """Render one multi-divider bar whose fund segments always total 100%."""
    label_list = [str(label) for label in labels]
    defaults = _valid_weights(default_weights, len(label_list))
    if defaults is None or not 2 <= len(label_list) <= 4:
        raise ValueError("Allocation slider requires two to four weights summing to 100")
    component_state = st.session_state.get(key, {})
    current = (
        _valid_weights(component_state.get("weights"), len(label_list))
        if hasattr(component_state, "get")
        else None
    )
    current = current or defaults
    result = _component_renderer()(
        data={"labels": label_list, "weights": current},
        default={"weights": current},
        key=key,
        on_weights_change=lambda: None,
        width="stretch",
        height="content",
    )
    returned = _valid_weights(getattr(result, "weights", None), len(label_list))
    return returned or current


__all__ = ["allocation_slider"]
