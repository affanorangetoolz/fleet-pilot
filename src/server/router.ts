import { randomInt } from "node:crypto";
import { TRPCError } from "@trpc/server";
import { z } from "zod";
import { protectedProcedure, router } from "./trpc";

const ALPHABET = "abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789";

export function makeSlug(length = 7): string {
  let slug = "";
  for (let i = 0; i < length; i++) slug += ALPHABET[randomInt(ALPHABET.length)];
  return slug;
}

const httpUrl = z.url({ protocol: /^https?$/ });

export const appRouter = router({
  links: router({
    list: protectedProcedure.query(({ ctx }) => ctx.repo.listByUser(ctx.userId)),

    create: protectedProcedure
      .input(z.object({ url: httpUrl }))
      .mutation(({ ctx, input }) =>
        ctx.repo.create({ userId: ctx.userId, slug: makeSlug(), url: input.url }),
      ),

    delete: protectedProcedure
      .input(z.object({ id: z.uuid() }))
      .mutation(async ({ ctx, input }) => {
        const deleted = await ctx.repo.deleteOwned(ctx.userId, input.id);
        if (!deleted) throw new TRPCError({ code: "NOT_FOUND" });
        return { id: input.id };
      }),
  }),
});

export type AppRouter = typeof appRouter;
