import { and, desc, eq } from "drizzle-orm";
import type { NodePgDatabase } from "drizzle-orm/node-postgres";
import { links, type Link } from "./db/schema";

// The data layer the router depends on. Tests pass an in-memory fake.
export interface LinksRepo {
  listByUser(userId: string): Promise<Link[]>;
  create(input: { userId: string; slug: string; url: string }): Promise<Link>;
  /** Returns true if a row owned by userId was deleted. */
  deleteOwned(userId: string, id: string): Promise<boolean>;
}

export function drizzleLinksRepo(db: NodePgDatabase): LinksRepo {
  return {
    listByUser: (userId) =>
      db.select().from(links).where(eq(links.userId, userId)).orderBy(desc(links.createdAt)),

    async create(input) {
      const [row] = await db.insert(links).values(input).returning();
      return row;
    },

    async deleteOwned(userId, id) {
      const rows = await db
        .delete(links)
        .where(and(eq(links.id, id), eq(links.userId, userId)))
        .returning({ id: links.id });
      return rows.length > 0;
    },
  };
}
