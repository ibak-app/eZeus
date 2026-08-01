#ifndef EFILESYSTEM_H
#define EFILESYSTEM_H

#include <filesystem>
#include <string>
#include <system_error>
#include <vector>

// Non-throwing wrappers around std::filesystem. The throwing overloads
// abort the process whenever a path cannot be inspected, which happens
// routinely on Android's mediated storage — a failed check should just
// read as "not there" instead of killing the game.
namespace eFs {

inline bool exists(const std::string& path) {
    std::error_code ec;
    return std::filesystem::exists(path, ec);
}

inline bool createDirectories(const std::string& path) {
    std::error_code ec;
    std::filesystem::create_directories(path, ec);
    return !ec;
}

inline bool removeAll(const std::string& path) {
    std::error_code ec;
    std::filesystem::remove_all(path, ec);
    return !ec;
}

// Iterating a directory that is not there is a normal situation (the
// player simply has no adventures or save games yet), so it must read as
// an empty listing rather than take the process down.
inline std::vector<std::filesystem::directory_entry>
    listDirectory(const std::string& path) {
    std::vector<std::filesystem::directory_entry> entries;
    std::error_code ec;
    std::filesystem::directory_iterator it(path, ec);
    if(ec) return entries;
    for(const auto& entry : it) entries.push_back(entry);
    return entries;
}

} // namespace eFs

#endif // EFILESYSTEM_H
