import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "za.co.sacryptotracker.app",
  appName: "SA Crypto",
  webDir: "dist",
  backgroundColor: "#0b0d12",
  ios: {
    contentInset: "always",
  },
  android: {
    backgroundColor: "#0b0d12",
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 600,
      backgroundColor: "#0b0d12",
      showSpinner: false,
      androidScaleType: "CENTER_CROP",
    },
    StatusBar: {
      style: "DARK",
      backgroundColor: "#0b0d12",
    },
  },
};

export default config;
