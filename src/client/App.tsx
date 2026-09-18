import { useState, type FormEvent } from "react";
import { authClient } from "./auth-client";
import { trpc } from "./trpc";

const input = "w-full rounded border border-gray-300 px-3 py-2";
const button = "rounded bg-black px-4 py-2 text-white disabled:opacity-50";

export function App() {
  const { data: session, isPending } = authClient.useSession();

  return (
    <main className="mx-auto max-w-xl p-6 font-sans">
      <h1 className="mb-6 text-2xl font-semibold">fleet-pilot</h1>
      {isPending ? <p>Loading…</p> : session ? <Links email={session.user.email} /> : <SignIn />}
    </main>
  );
}

function SignIn() {
  const [mode, setMode] = useState<"signIn" | "signUp">("signIn");
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const email = String(form.get("email"));
    const password = String(form.get("password"));
    const { error } =
      mode === "signUp"
        ? await authClient.signUp.email({ email, password, name: email })
        : await authClient.signIn.email({ email, password });
    setError(error?.message ?? null);
  }

  return (
    <form onSubmit={onSubmit} className="space-y-3">
      <input name="email" type="email" required placeholder="Email" className={input} />
      <input name="password" type="password" required minLength={8} placeholder="Password" className={input} />
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="flex items-center gap-4">
        <button className={button}>{mode === "signUp" ? "Create account" : "Sign in"}</button>
        <button
          type="button"
          className="text-sm underline"
          onClick={() => setMode(mode === "signUp" ? "signIn" : "signUp")}
        >
          {mode === "signUp" ? "Have an account? Sign in" : "New here? Create an account"}
        </button>
      </div>
    </form>
  );
}

function Links({ email }: { email: string }) {
  const utils = trpc.useUtils();
  const list = trpc.links.list.useQuery();
  const create = trpc.links.create.useMutation({ onSuccess: () => utils.links.list.invalidate() });
  const remove = trpc.links.delete.useMutation({ onSuccess: () => utils.links.list.invalidate() });

  function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    create.mutate({ url: String(new FormData(form).get("url")) }, { onSuccess: () => form.reset() });
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between text-sm">
        <span>Signed in as {email}</span>
        <button className="underline" onClick={() => authClient.signOut()}>
          Sign out
        </button>
      </div>

      <form onSubmit={onSubmit} className="flex gap-2">
        <input name="url" type="url" required placeholder="https://example.com/long/path" className={input} />
        <button className={button} disabled={create.isPending}>
          Shorten
        </button>
      </form>
      {create.error && <p className="text-sm text-red-600">{create.error.message}</p>}

      <ul className="divide-y divide-gray-200">
        {list.data?.map((link) => (
          <li key={link.id} className="flex items-center justify-between gap-4 py-2">
            <div className="min-w-0">
              <p className="font-mono">{link.slug}</p>
              <p className="truncate text-sm text-gray-500">{link.url}</p>
            </div>
            <button
              className="text-sm text-red-600 underline"
              disabled={remove.isPending}
              onClick={() => remove.mutate({ id: link.id })}
            >
              Delete
            </button>
          </li>
        ))}
        {list.data?.length === 0 && <li className="py-2 text-gray-500">No links yet.</li>}
      </ul>
    </div>
  );
}
