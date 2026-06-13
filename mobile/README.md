# Chuckwagon Mobile (Expo)

The React Native / Expo customer app. Consumes the Django DRF API in `../backend`.
Stack: Expo SDK 55, Expo Router, TypeScript, NativeWind (Tailwind), Zustand,
jest-expo. Conventions mirror the sibling Expo project (LongWalk).

> Status: **Wave 1 (bootable skeleton)**. Bright Trail theme + Fraunces/Inter
> fonts + placeholder tabs (Discover / Following / Account). Live data, auth, and
> follow land in the next waves.

## One-time setup

You need **Node 20+** and the **Expo Go** app on your phone (iOS App Store /
Google Play). The phone and this computer must be on the **same WiFi**.

```bash
cd mobile
npm install
# Add the native modules planned for the next wave at SDK-correct versions:
npx expo install expo-location expo-secure-store @react-native-async-storage/async-storage zustand
```

If `npm install` complains about a version, run `npx expo install --fix` to let
Expo pin SDK-correct versions.

## Point the app at your backend

In Expo Go on a physical phone, `localhost` means the *phone*, not your PC, so
you must use your computer's LAN IP.

1. Start the backend (from `../backend`): `docker compose up` (serves on `:8000`).
2. Find your PC's IPv4 address: run `ipconfig` and read **IPv4 Address**
   (e.g. `192.168.1.23`).
3. Copy `.env.example` to `.env` and set:
   ```
   EXPO_PUBLIC_API_URL=http://192.168.1.23:8000/api/v1
   ```
   The Django dev server already accepts any host, and CORS does not apply to a
   native app, so only the IP needs to be right.

## Run

```bash
npx expo start
```

Scan the QR code with Expo Go (Android) or the Camera app (iOS). The app reloads
on save.

**Wave 1 check:** you should see a warm cream screen with "Chuckwagon" in the
Fraunces display face (tomato red), Inter body text, a green "Skeleton is live"
pill, and a three-tab bar. That confirms the toolchain, NativeWind theme, and
fonts all work end to end.

## Troubleshooting

- **Blank/again-loading or font errors:** make sure `npm install` finished; the
  app waits for Fraunces/Inter to load before rendering.
- **Network/timeout once data is wired:** re-check `EXPO_PUBLIC_API_URL` is your
  PC's current LAN IP (it changes between networks), the backend is up, and the
  phone is on the same WiFi.
- **Restart cleanly after config changes:** `npx expo start -c` clears the cache.

## Layout

```
app/                 Expo Router routes
  _layout.tsx        root: fonts + Stack
  (tabs)/            tab navigator: Discover / Following / Account
src/
  lib/config.ts      API base URL + constants
tailwind.config.js   Bright Trail palette + Fraunces/Inter (mirrors web tokens)
```
