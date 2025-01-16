#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include "EverCrypt_AutoConfig2.h"
#include "EverCrypt_Poly1305.h"
#include "../src/tsc_x86.h"
#include <vector>
#include <algorithm>

#ifndef STRING_LEN
#define STRING_LEN 25600
#endif

int main() {
    // Initialize EverCrypt
    EverCrypt_AutoConfig2_init();

    // Example key and message
    uint8_t key[32] = {
        0x85, 0xd6, 0xbe, 0x78, 0x57, 0x55, 0x6d, 0x33,
        0x7f, 0x44, 0x52, 0xfe, 0x42, 0xd5, 0x06, 0xa8,
        0x01, 0x03, 0x80, 0x8a, 0xfb, 0x0d, 0x4a, 0x73,
        0x74, 0x7e, 0x18, 0x25, 0x55, 0x69, 0x89, 0x2d
    };
    char message[STRING_LEN];
    for (int i = 0; i < STRING_LEN; i++) {
        message[i] = i % 256;
    }
    size_t message_len = STRING_LEN;//strlen(message);

    // Output tag buffer
    uint8_t tag[16] = {0};

    // Compute Poly1305
    EverCrypt_Poly1305_mac(tag, (uint8_t *)message, message_len, key);

    // Print the tag

    double multiplier = 2.0;
    uint64_t start, end;
    double cycles_required = 1e9;
    int num_runs = 10;
    int reps = 10;

    while(multiplier > 1){
        start = start_tsc();
        for(int i = 0; i < num_runs; i++){
            EverCrypt_Poly1305_mac(tag, (uint8_t *)message, message_len, key);
        }
        end = stop_tsc(start);
        multiplier =  cycles_required / (double)end;
        num_runs = num_runs * multiplier;
    }

    std::vector<double> cycles;

    for(int i = 0; i < reps; i++){
        start = start_tsc();
        for(int i = 0; i < num_runs; i++){
            EverCrypt_Poly1305_mac(tag, (uint8_t *)message, message_len, key);
        }
        end = stop_tsc(start);
        cycles.push_back((double)end / num_runs);
    }

    std::sort(cycles.begin(), cycles.end());

    printf("%d,%f,%f,%f\n", STRING_LEN, cycles[reps/2], multiplier, num_runs);

    return 0;
}