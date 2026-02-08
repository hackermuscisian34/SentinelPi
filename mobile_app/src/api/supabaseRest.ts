const SUPABASE_URL = process.env.EXPO_PUBLIC_SUPABASE_URL || "";
const SUPABASE_ANON_KEY = process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY || "";

export async function supabaseGet(path: string, token: string) {
  const resp = await fetch(`${SUPABASE_URL}/rest/v1/${path}`, {
    headers: {
      apikey: SUPABASE_ANON_KEY,
      Authorization: `Bearer ${token}`,
    },
  });
  if (!resp.ok) {
    throw new Error("Supabase request failed");
  }
  return resp.json();
}

export async function supabasePost(path: string, token: string, body: any) {
  const resp = await fetch(`${SUPABASE_URL}/rest/v1/${path}`, {
    method: "POST",
    headers: {
      apikey: SUPABASE_ANON_KEY,
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  if (!resp.ok) {
    throw new Error("Supabase request failed");
  }
  return resp.json();
}
