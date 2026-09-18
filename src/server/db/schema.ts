import { index, pgTable, text, timestamp, uuid } from "drizzle-orm/pg-core";

// The app's only Drizzle table. Better Auth manages its own tables
// (user, session, account, verification) — see src/server/db/migrate.ts.
export const links = pgTable(
  "links",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    userId: text("user_id").notNull(),
    slug: text("slug").notNull().unique(),
    url: text("url").notNull(),
    createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
  },
  (t) => [index("links_user_id_idx").on(t.userId)],
);

export type Link = typeof links.$inferSelect;
