import { describe, expect, it } from "vitest";

import { normalizeErrorMessage, resolveApiBaseUrl } from "./api";

describe("api helpers", () => {
  it("resolves default api base url", () => {
    expect(resolveApiBaseUrl()).toBe("http://localhost:18000/api/v2");
  });

  it("normalizes unknown error shape", () => {
    expect(normalizeErrorMessage({})).toBe("Request failed.");
  });
});
