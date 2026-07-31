package com.ibak.ezeus;

import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.provider.Settings;

import org.libsdl.app.SDLActivity;

public class EZeusActivity extends SDLActivity {
    @Override
    protected String[] getLibraries() {
        // Order matters: dependencies first, the game library last —
        // SDLActivity resolves SDL_main from the last entry.
        return new String[] {
            "SDL2",
            "SDL2_image",
            "SDL2_ttf",
            "SDL2_mixer",
            "eZeus"
        };
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        requestStorageAccess();
        super.onCreate(savedInstanceState);
    }

    /**
     * The game reads its data from a shared-storage folder the user fills
     * with a file manager, which on Android 11+ requires all-files access.
     * Send the user to the system settings page for it once.
     */
    private void requestStorageAccess() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.R) return;
        if (Environment.isExternalStorageManager()) return;
        try {
            final Intent intent = new Intent(
                Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION,
                Uri.parse("package:" + getPackageName()));
            startActivity(intent);
        } catch (Exception e) {
            startActivity(new Intent(
                Settings.ACTION_MANAGE_ALL_FILES_ACCESS_PERMISSION));
        }
    }
}
