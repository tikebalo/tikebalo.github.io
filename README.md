# GML Launcher Registration Site

This repository contains a simple registration page and backend server that mimic the custom authentication described in the GML Launcher documentation.

## Running locally

1. Start the server:
   ```
   node server.js
   ```
2. Open `http://localhost:3000` in your browser.

The registration data is stored in `users.json` in the project root.

## Integrating with GML Launcher

Set the `custom_auth_url` option in your GML Launcher configuration to the
address of this page (for example `https://your-domain.example`). After that,
the launcher will open it for user registration or login and send the entered
credentials back to the launcher as described in the official documentation.
