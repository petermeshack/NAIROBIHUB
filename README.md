# Nairobi County DES File Hub

Welcome to the **Nairobi County DES File Hub** repository! This application is designed to facilitate secure resource sharing, collaborative file management, and real-time network telemetry across connected spaces. It features both a **Desktop App** (Python/PySide6) and an **Android App** (Kotlin/Jetpack Compose), allowing seamless cross-device synchronization and offline access.

---

## 🚀 Key Features

* **Multi-Platform Support:** Fully functional Desktop application and Android mobile application.
* **Shared Space Hosting:** Host your own space, issue secure space access keys, and manage network tunnels using `.loca.lt`.
* **Resource Management:** Organize, upload, and browse folders, documents, spreadsheets, images, audio, and video files with granular public/private access settings.
* **Bookmarks & Offline Mode:** Star your favorite items and save resources locally for offline viewing when the server is unreachable.
* **Moderator Tools:** Comprehensive user permission management (ban, timeout, revoke read/write access, assign moderators) and file moderation oversight.
* **Customizable Settings:** Personalize color themes, accent colors, font scaling, sound alerts, and notification filters.

---

## 🛠️ Prerequisites for Hosting

To successfully run and host shared spaces with public URLs using `.loca.lt`, your machine **must** have **Node.js** installed and the **LocalTunnel** package available globally.

1. **Install Node.js:** Download and install Node.js from [nodejs.org](https://nodejs.org/).
2. **Install LocalTunnel:** Open your terminal or command prompt and run the following command globally:
   ```bash
   npm install -g localtunnel
