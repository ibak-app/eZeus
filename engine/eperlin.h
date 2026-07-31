#ifndef EPERLIN_H
#define EPERLIN_H

#include <algorithm>
#include <array>
#include <cmath>
#include <numeric>
#include <random>

// Small self-contained replacement for noise::module::Perlin (libnoise),
// exposing the subset of its interface used by the map generator.
// Classic Ken Perlin improved noise with octave summation.
class ePerlin {
public:
    void SetSeed(const int seed) {
        std::iota(mPerm.begin(), mPerm.begin() + 256, 0);
        std::mt19937 gen(seed);
        std::shuffle(mPerm.begin(), mPerm.begin() + 256, gen);
        for(int i = 0; i < 256; i++) mPerm[256 + i] = mPerm[i];
    }

    void SetOctaveCount(const double o) { mOctaves = int(o); }
    void SetFrequency(const double f) { mFrequency = f; }
    void SetPersistence(const double p) { mPersistence = p; }

    double GetValue(double x, double y, double z) const {
        x *= mFrequency;
        y *= mFrequency;
        z *= mFrequency;
        double result = 0;
        double amplitude = 1;
        // Like libnoise: octaves accumulate without normalization,
        // each one at double the frequency (lacunarity 2).
        for(int i = 0; i < mOctaves; i++) {
            result += amplitude*noise(x, y, z);
            x *= 2; y *= 2; z *= 2;
            amplitude *= mPersistence;
        }
        return result;
    }

private:
    static double fade(const double t) {
        return t*t*t*(t*(t*6 - 15) + 10);
    }

    static double lerp(const double t, const double a, const double b) {
        return a + t*(b - a);
    }

    static double grad(const int hash, const double x,
                       const double y, const double z) {
        const int h = hash & 15;
        const double u = h < 8 ? x : y;
        const double v = h < 4 ? y : (h == 12 || h == 14 ? x : z);
        return ((h & 1) == 0 ? u : -u) + ((h & 2) == 0 ? v : -v);
    }

    double noise(double x, double y, double z) const {
        const int X = int(std::floor(x)) & 255;
        const int Y = int(std::floor(y)) & 255;
        const int Z = int(std::floor(z)) & 255;
        x -= std::floor(x);
        y -= std::floor(y);
        z -= std::floor(z);
        const double u = fade(x);
        const double v = fade(y);
        const double w = fade(z);
        const auto& p = mPerm;
        const int A = p[X] + Y, AA = p[A] + Z, AB = p[A + 1] + Z;
        const int B = p[X + 1] + Y, BA = p[B] + Z, BB = p[B + 1] + Z;

        return lerp(w, lerp(v, lerp(u, grad(p[AA], x, y, z),
                                       grad(p[BA], x - 1, y, z)),
                               lerp(u, grad(p[AB], x, y - 1, z),
                                       grad(p[BB], x - 1, y - 1, z))),
                       lerp(v, lerp(u, grad(p[AA + 1], x, y, z - 1),
                                       grad(p[BA + 1], x - 1, y, z - 1)),
                               lerp(u, grad(p[AB + 1], x, y - 1, z - 1),
                                       grad(p[BB + 1], x - 1, y - 1, z - 1))));
    }

    std::array<int, 512> mPerm{};
    int mOctaves = 1;
    double mFrequency = 1;
    double mPersistence = 0.5;
};

#endif // EPERLIN_H
