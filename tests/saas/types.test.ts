/**
 * Tests for type definitions and utility functions.
 */

import { describe, it, expect } from "vitest";
import {
  STAGE_COLORS,
  DEFAULT_STAGE_COLOR,
  getStageColor,
} from "../../saas/types";

describe("STAGE_COLORS", () => {
  it("has colors for S1 through S8", () => {
    for (let i = 1; i <= 8; i++) {
      expect(STAGE_COLORS[`S${i}`]).toBeDefined();
      expect(STAGE_COLORS[`S${i}`]).toMatch(/^#[0-9A-Fa-f]{6}$/);
    }
  });

  it("all colors are valid hex", () => {
    for (const color of Object.values(STAGE_COLORS)) {
      expect(color).toMatch(/^#[0-9A-Fa-f]{6}$/);
    }
  });
});

describe("getStageColor", () => {
  it("returns correct color for known stages", () => {
    expect(getStageColor("S1")).toBe(STAGE_COLORS.S1);
    expect(getStageColor("S4")).toBe(STAGE_COLORS.S4);
  });

  it("returns default for unknown stages", () => {
    expect(getStageColor("S99")).toBe(DEFAULT_STAGE_COLOR);
    expect(getStageColor("unknown")).toBe(DEFAULT_STAGE_COLOR);
  });

  it("default color is valid hex", () => {
    expect(DEFAULT_STAGE_COLOR).toMatch(/^#[0-9A-Fa-f]{6}$/);
  });
});
