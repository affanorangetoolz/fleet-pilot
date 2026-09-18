import { initTRPC, TRPCError } from "@trpc/server";
import type { LinksRepo } from "./links-repo";

export interface Context {
  userId: string | null;
  repo: LinksRepo;
}

const t = initTRPC.context<Context>().create();

export const router = t.router;

export const protectedProcedure = t.procedure.use(({ ctx, next }) => {
  if (!ctx.userId) throw new TRPCError({ code: "UNAUTHORIZED" });
  return next({ ctx: { ...ctx, userId: ctx.userId } });
});

export const createCallerFactory = t.createCallerFactory;
