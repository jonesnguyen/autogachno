import { QueryClient, QueryFunction } from "@tanstack/react-query";

async function throwIfResNotOk(res: Response) {
  if (!res.ok) {
    const text = (await res.text()) || res.statusText;
    throw new Error(`${res.status}: ${text}`);
  }
}

// Backward/forward-compatible API: accepts either
// - apiRequest(method, url, data) [legacy]
// - apiRequest(url, method?, data?) [preferred]
export async function apiRequest(
  arg1: string,
  arg2?: string | unknown,
  arg3?: unknown,
): Promise<Response> {
  let method = "GET";
  let url = "";
  let data: unknown | undefined;

  const isUrlFirst = arg1.startsWith("/") || arg1.startsWith("http");
  if (isUrlFirst) {
    url = arg1;
    method = (typeof arg2 === "string" ? arg2 : "GET") as string;
    data = typeof arg2 === "string" ? arg3 : arg2;
  } else {
    method = arg1;
    url = arg2 as string;
    data = arg3;
  }

  const res = await fetch(url, {
    method,
    headers: data ? { "Content-Type": "application/json" } : {},
    body: data ? JSON.stringify(data) : undefined,
    credentials: "include",
  });

  await throwIfResNotOk(res);
  return res;
}

type UnauthorizedBehavior = "returnNull" | "throw";
export const getQueryFn: <T>(options: {
  on401: UnauthorizedBehavior;
}) => QueryFunction<T> =
  ({ on401: unauthorizedBehavior }) =>
  async ({ queryKey }) => {
    const res = await fetch(queryKey.join("/") as string, {
      credentials: "include",
    });

    if (unauthorizedBehavior === "returnNull" && res.status === 401) {
      return null;
    }

    await throwIfResNotOk(res);
    return await res.json();
  };

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      queryFn: getQueryFn({ on401: "throw" }),
      refetchInterval: false,
      refetchOnWindowFocus: false,
      staleTime: Infinity,
      retry: false,
    },
    mutations: {
      retry: false,
    },
  },
});
