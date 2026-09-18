import { randomUUID } from "node:crypto";
import { TRPCError } from "@trpc/server";
import { beforeEach, describe, expect, it } from "vitest";
import type { Link } from "./db/schema";
import type { LinksRepo } from "./links-repo";
import { appRouter, makeSlug } from "./router";
import { createCallerFactory } from "./trpc";

// In-memory stand-in for the Drizzle repo, so no database is needed.
function fakeRepo(): LinksRepo {
  const rows: Link[] = [];
  return {
    listByUser: async (userId) => rows.filter((r) => r.userId === userId),
    async create(input) {
      const row: Link = { id: randomUUID(), createdAt: new Date(), ...input };
      rows.push(row);
      return row;
    },
    async deleteOwned(userId, id) {
      const i = rows.findIndex((r) => r.id === id && r.userId === userId);
      if (i === -1) return false;
      rows.splice(i, 1);
      return true;
    },
  };
}

const createCaller = createCallerFactory(appRouter);

async function expectCode(promise: Promise<unknown>, code: TRPCError["code"]) {
  await expect(promise).rejects.toSatisfy((e) => e instanceof TRPCError && e.code === code);
}

describe("links router", () => {
  let repo: LinksRepo;
  const as = (userId: string | null) => createCaller({ userId, repo });

  beforeEach(() => {
    repo = fakeRepo();
  });

  it("creates a link with a generated slug and lists only the caller's links", async () => {
    const alice = as("alice");
    const created = await alice.links.create({ url: "https://example.com/a" });
    await as("bob").links.create({ url: "https://example.com/b" });

    expect(created.slug).toMatch(/^[A-Za-z0-9]{7}$/);
    expect(await alice.links.list()).toEqual([created]);
  });

  it("deletes the caller's own link but not someone else's", async () => {
    const link = await as("alice").links.create({ url: "https://example.com/a" });

    await expectCode(as("bob").links.delete({ id: link.id }), "NOT_FOUND");
    expect(await as("alice").links.list()).toHaveLength(1);

    await expect(as("alice").links.delete({ id: link.id })).resolves.toEqual({ id: link.id });
    expect(await as("alice").links.list()).toEqual([]);
  });

  it("rejects signed-out callers", async () => {
    await expectCode(as(null).links.list(), "UNAUTHORIZED");
    await expectCode(as(null).links.create({ url: "https://example.com" }), "UNAUTHORIZED");
  });

  it("rejects non-http URLs", async () => {
    await expectCode(as("alice").links.create({ url: "javascript:alert(1)" }), "BAD_REQUEST");
    await expectCode(as("alice").links.create({ url: "not a url" }), "BAD_REQUEST");
  });
});

describe("makeSlug", () => {
  it("produces slugs of the requested length from an unambiguous alphabet", () => {
    for (let i = 0; i < 200; i++) expect(makeSlug(10)).toMatch(/^[a-km-zA-HJ-NP-Z2-9]{10}$/);
  });
});
