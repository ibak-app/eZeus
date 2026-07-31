#include "egamedir.h"

#include <SDL2/SDL_filesystem.h>
#ifdef __ANDROID__
#include <SDL2/SDL_system.h>
#endif
#include <fstream>

std::string eGameDir::sPath;

void eGameDir::initialize() {
    sPath = exeDir() + "../../";
    const auto zp = exeDir() + "../zeus_path.txt";
    std::ifstream file(zp);
    if(!file.good()) return;
    std::string str;
    const bool g = !!std::getline(file, str);
    if(!g) return;
    sPath = exeDir() + str;
}

std::string eGameDir::path(const std::string& path) {
    return sPath + path;
}

std::string eGameDir::settingsPath() {
    return exeDir() + "../settings.txt";
}

std::string eGameDir::numbersPath() {
    return exeDir() + "../numbers.txt";
}

std::string eGameDir::iBinaryPath() {
    return exeDir() + "../interface.e";
}

std::string eGameDir::i15BinaryPath() {
    return exeDir() + "../i15.e";
}

std::string eGameDir::i30BinaryPath() {
    return exeDir() + "../i30.e";
}

std::string eGameDir::i45BinaryPath() {
    return exeDir() + "../i45.e";
}

std::string eGameDir::i60BinaryPath() {
    return exeDir() + "../i60.e";
}

std::string eGameDir::exeDir() {
#ifdef __ANDROID__
    // No executable directory on Android. Read the game from a plain
    // shared-storage folder the user can fill with a file manager:
    //   /sdcard/Zeus and Poseidon/         <- DATA, Audio, ...
    //   /sdcard/Zeus and Poseidon/eZeus/   <- interface.e, XMLs, ...
    // App-specific storage would be unreachable for the file manager,
    // and files pushed there by adb end up owned by another user.
    // Derive the storage root from the app-specific path rather than
    // hardcoding /storage/emulated/0.
    std::string root = "/sdcard";
    if(const char* const d = SDL_AndroidGetExternalStoragePath()) {
        const std::string p(d);
        const auto pos = p.find("/Android/data/");
        if(pos != std::string::npos) root = p.substr(0, pos);
    }
    return root + "/Zeus and Poseidon/eZeus/Bin/";
#else
    const auto d = SDL_GetBasePath();
    const std::string str(d);
    return str;
#endif
}

std::string eGameDir::adventuresDir() {
    return exeDir() + "../Adventures/";
}

std::string eGameDir::pakAdventuresDir() {
    // return "/home/ailuropoda/.eZeus/Zeus/Adventures/"; // !!!
    return eGameDir::path("Adventures/");
}

std::string eGameDir::saveDir() {
    return exeDir() + "../Save/";
}

std::string eGameDir::texturesDir() {
    return exeDir() + "../Textures/";
}
