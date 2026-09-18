function required(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(`Missing required env var ${name} — copy .env.example to .env`);
  return value;
}

export const env = {
  DATABASE_URL: required("DATABASE_URL"),
  BETTER_AUTH_SECRET: required("BETTER_AUTH_SECRET"),
  BETTER_AUTH_URL: required("BETTER_AUTH_URL"),
  PORT: Number(process.env.PORT ?? 3000),
};
