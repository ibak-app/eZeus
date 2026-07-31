package com.ibak.ezeus;

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
}
