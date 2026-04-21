import { Capacitor } from "@capacitor/core";

export async function bootstrapNative(): Promise<void> {
  if (!Capacitor.isNativePlatform()) return;

  const [{ StatusBar, Style }, { SplashScreen }] = await Promise.all([
    import("@capacitor/status-bar"),
    import("@capacitor/splash-screen"),
  ]);

  try {
    await StatusBar.setStyle({ style: Style.Dark });
    await StatusBar.setBackgroundColor({ color: "#0b0d12" });
  } catch {
    // StatusBar is no-op on platforms that don't support it.
  }

  try {
    await SplashScreen.hide();
  } catch {
    // SplashScreen may already be hidden.
  }
}
