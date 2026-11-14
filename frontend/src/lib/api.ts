const configuredApiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();

if (!configuredApiUrl) {
  throw new Error(
    "NEXT_PUBLIC_API_URL is missing. Configure it in your frontend environment."
  );
}

export const API_BASE_URL = configuredApiUrl.replace(/\/+$/, "");
