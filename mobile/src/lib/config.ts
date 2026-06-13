/**
 * App configuration. The API base URL comes from EXPO_PUBLIC_API_URL (set in
 * .env, see .env.example). In Expo Go on a device this must be the computer's
 * LAN IP, not localhost.
 */
export const API_URL =
  process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

/** Default "near me" search radius, matching the web discovery default. */
export const DISCOVERY_RADIUS_KM = 8;
